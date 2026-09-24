"""Exercise the public launcher and its real internal MCP subprocess."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.common import canonical
from sci_ai_verifier.local import DEADLINE_ENV
from sci_ai_verifier.local_entry import PROBE_PROMPT, verify

ROOT = Path(__file__).resolve().parents[1]


class EntryTests(unittest.TestCase):
    def test_public_action_drives_real_private_stdio_to_immutable_report(self):
        for auth in ("subscription", "api"):
            with self.subTest(auth=auth):
                self.run_entry(lost_result=False, auth=auth)

    def test_lost_planner_result_recovers_completed_report_without_replay(self):
        self.run_entry(lost_result=True)

    def run_entry(self, lost_result, auth="subscription"):
        parent = ROOT / ".verifier/test-work"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            base = Path(temporary)
            skill = base / "SKILL.md"
            skill.write_text("Organize notes into a tidy list. No scientific claims.")
            settings = base / "settings.json"
            settings.write_bytes(canonical({"external_tools": {"example_app": {
                "executable": sys.executable, "sha256": "a"*64, "arguments": [],
                "description": "Fixture only; never executed", "credential_env": ["EXAMPLE_APP_TOKEN"],
                "read_only": True}}}))
            credentials = {"CLAUDE_CODE_OAUTH_TOKEN": "entry-subscription-token",
                           "ANTHROPIC_API_KEY": "entry-api-token",
                           "EXAMPLE_APP_TOKEN": "entry-app-token", "UNRELATED_SECRET": "entry-unrelated-secret"}
            credential = "ANTHROPIC_API_KEY" if auth == "api" else "CLAUDE_CODE_OAUTH_TOKEN"

            probes = []

            def controller(command, **kwargs):
                if kwargs["prompt"] == PROBE_PROMPT:
                    # The startup probe runs before the planner, in its own no-tool session.
                    probes.append(command)
                    session = command[command.index("--session-id")+1]
                    return 0, canonical({"type": "result", "subtype": "success", "is_error": False,
                                         "session_id": session, "result": "OK"}), b""
                self.assertEqual(len(probes), 1, "the model is probed once, before the planner starts")
                config = json.loads(Path(command[command.index("--mcp-config")+1]).read_bytes())
                private = config["mcpServers"]["verifier_internal"]
                # The tool server learns the attempt deadline, by reference like the credentials.
                self.assertEqual(private["env"].get(DEADLINE_ENV), "${" + DEADLINE_ENV + ":-}")
                # Model the MCP transport's safe baseline, not full parent inheritance.
                child_env = {key: value for key, value in kwargs["env"].items()
                             if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC",
                                                "TEMP", "TMP", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}}
                # The host CLI consumes its own auth variables before expanding this
                # configuration, so they cannot be referenced by their own names.
                expansion = {key: value for key, value in kwargs["env"].items()
                             if key not in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")}
                for key, value in private.get("env", {}).items():
                    match = re.fullmatch(r"\$\{([A-Z][A-Z0-9_]*):-\}", value)
                    self.assertIsNotNone(match, "MCP configuration must contain variable references only")
                    resolved = expansion.get(match.group(1), "")
                    self.assertNotEqual(resolved, "", "credential reference " + value + " expands to nothing")
                    child_env[key] = resolved
                self.assertNotIn("UNRELATED_SECRET", child_env)
                for key in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY"):
                    if key != credential:
                        self.assertNotIn(key, child_env)
                for value in credentials.values():
                    self.assertNotIn(value.encode(), canonical(config))
                # A real child must be able to build the subject/assessor auth environment.
                probe = "import os,sys; from pathlib import Path; sys.path.insert(0," + repr(str(ROOT/"src")) + "); "
                probe += "from sci_ai_verifier.claude_runner import isolated_environment; "
                probe += "env=isolated_environment(Path('probe-config')," + repr(auth) + "); "
                probe += "assert env[" + repr(credential) + "]==" + repr(credentials[credential]) + "; "
                probe += "assert os.environ.get('EXAMPLE_APP_TOKEN')=='entry-app-token'; "
                probe += "assert 'EXAMPLE_APP_TOKEN' not in env; print('credential_handoff_ok')"
                checked = subprocess.run([sys.executable, "-c", probe], cwd=kwargs["cwd"], env=child_env,
                                         capture_output=True, timeout=10)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertEqual(checked.stdout.strip(), b"credential_handoff_ok")
                run_id = private["args"][private["args"].index("--run-id")+1]
                process = subprocess.Popen([private["command"], *private["args"]], cwd=kwargs["cwd"],
                                           env=child_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                sequence = 0
                def rpc(method, params, notification=False):
                    nonlocal sequence
                    sequence += 1
                    frame = {"jsonrpc": "2.0", "method": method, "params": params}
                    if not notification:
                        frame["id"] = sequence
                    process.stdin.write(canonical(frame)+b"\n")
                    process.stdin.flush()
                    if notification:
                        return
                    response = json.loads(process.stdout.readline())
                    self.assertNotIn("error", response)
                    return response["result"]
                def tool(name, arguments):
                    result = rpc("tools/call", {"name": name, "arguments": arguments})
                    value = json.loads(result["content"][0]["text"])
                    self.assertEqual(value["status"], "ok", value)
                    return value["data"]
                try:
                    rpc("initialize", {"protocolVersion": "2025-06-18"})
                    rpc("notifications/initialized", {}, notification=True)
                    context = tool("get_verifier_context", {"run_id": run_id})
                    loaded = tool("load_submitted_skill", {"run_id": run_id, "state_token": context["state_token"], "source_path": str(skill)})
                    committed = tool("commit_claim_manifest", {"run_id": run_id, "state_token": loaded["state_token"],
                         "snapshot_id": loaded["snapshot"]["id"], "snapshot_digest": loaded["snapshot"]["digest"], "claims": []})
                    completed = tool("write_report_card", {"run_id": run_id, "state_token": committed["state_token"]})
                    self.assertTrue(completed["verification_complete"])
                finally:
                    process.stdin.close()
                    process.wait(timeout=10)
                    process.stdout.close()
                    stderr = process.stderr.read()
                    process.stderr.close()
                    self.assertEqual(process.returncode, 0, stderr)
                session = command[command.index("--session-id")+1]
                return (1, b"", b"") if lost_result else (0, canonical({"type": "result", "subtype": "success",
                        "is_error": False, "session_id": session, "result": "Completed"}), b"")

            with patch.dict(os.environ, credentials), \
                 patch("sci_ai_verifier.local_entry.ClaudeCode.preflight", return_value={"version": "synthetic"}), \
                 patch("sci_ai_verifier.claude_runner.run_process", side_effect=controller):
                # Default callback is resolved at construction so patches also exercise production wiring.
                result = verify(skill, workspace=base / "data", instructions=ROOT / "skills/scientific-verifier",
                                auth=auth, config_path=settings)
            self.assertEqual(result["status"], "ok", result)
            self.assertEqual(result["data"]["report"]["claims"], [])
            self.assertTrue(Path(result["data"]["report_markdown_path"]).exists())
            for file in (base / "data/.verifier").rglob("*"):
                if file.is_file():
                    for value in credentials.values():
                        self.assertNotIn(value.encode(), file.read_bytes())


if __name__ == "__main__":
    unittest.main()
