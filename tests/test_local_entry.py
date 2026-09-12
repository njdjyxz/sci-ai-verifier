"""Exercise the public launcher and its real internal MCP subprocess."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.common import canonical
from sci_ai_verifier.local_entry import verify

ROOT = Path(__file__).resolve().parents[1]


class EntryTests(unittest.TestCase):
    def test_public_action_drives_real_private_stdio_to_immutable_report(self):
        self.run_entry(lost_result=False)

    def test_lost_planner_result_recovers_completed_report_without_replay(self):
        self.run_entry(lost_result=True)

    def run_entry(self, lost_result):
        parent = ROOT / ".verifier/test-work"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            base = Path(temporary)
            skill = base / "SKILL.md"
            skill.write_text("Organize notes into a tidy list. No scientific claims.")

            def controller(command, **kwargs):
                config = json.loads(Path(command[command.index("--mcp-config")+1]).read_bytes())
                private = config["mcpServers"]["verifier_internal"]
                self.assertNotIn("env", private)
                run_id = private["args"][private["args"].index("--run-id")+1]
                process = subprocess.Popen([private["command"], *private["args"]], cwd=kwargs["cwd"],
                                           env=kwargs["env"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

            with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "entry-test-token"}), \
                 patch("sci_ai_verifier.local_entry.ClaudeCode.preflight", return_value={"version": "synthetic"}), \
                 patch("sci_ai_verifier.claude_runner.run_process", side_effect=controller):
                # Default callback is resolved at construction so patches also exercise production wiring.
                result = verify(skill, workspace=base / "data", instructions=ROOT / "skills/scientific-verifier")
            self.assertEqual(result["status"], "ok", result)
            self.assertEqual(result["data"]["report"]["claims"], [])
            self.assertTrue(Path(result["data"]["report_markdown_path"]).exists())
            for file in (base / "data/.verifier").rglob("*"):
                if file.is_file():
                    self.assertNotIn(b"entry-test-token", file.read_bytes())


if __name__ == "__main__":
    unittest.main()
