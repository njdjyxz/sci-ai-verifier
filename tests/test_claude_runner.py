"""CLI boundary tests: no model/network calls; real child processes for limits."""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.claude_runner import (ClaudeCode, SUBJECT_SKILL, isolated_environment,
    parse_events, prepare_workspace, run_process, stage_skill)
from sci_ai_verifier.common import Fault, canonical


def stream(session, *, skill=SUBJECT_SKILL, failed=False, output="42", tool="Skill"):
    events = [
        {"type": "assistant", "message": {"model": "claude-fixture-observed", "content": [
            {"type": "tool_use", "id": "call-1", "name": tool, "input": {"skill": skill}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "call-1", "is_error": failed}]}},
        {"type": "result", "subtype": "success", "is_error": False, "session_id": session, "result": output},
    ]
    return b"\n".join(canonical(event) for event in events)


class RunnerTests(unittest.TestCase):
    def test_auth_environment_is_allowlisted_and_credentials_separate(self):
        source = {"PATH": "bin", "ANTHROPIC_API_KEY": "private-api", "CLAUDE_CODE_OAUTH_TOKEN": "private-oauth",
                  "GITHUB_TOKEN": "hidden", "NODE_OPTIONS": "evil", "ANTHROPIC_BASE_URL": "https://untrusted",
                  "CLAUDE_CONFIG_DIR": "old", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "0"}
        for mode, kept, absent in (("api", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"),
                                   ("subscription", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")):
            env = isolated_environment(Path("isolated"), mode, source)
            self.assertEqual(env[kept], source[kept])
            for name in (absent, "GITHUB_TOKEN", "NODE_OPTIONS", "ANTHROPIC_BASE_URL"):
                self.assertNotIn(name, env)
            self.assertEqual(env["CLAUDE_CONFIG_DIR"], "isolated")
            self.assertEqual(env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")
        with self.assertRaises(Fault):
            isolated_environment(Path("new"), "subscription", {"ANTHROPIC_API_KEY": "api"})

    def test_subject_stage_invocation_and_cleanup_both_auth_modes(self):
        source = [{"path": "SKILL.md", "content": "---\nname: original\nallowed-tools: Bash\ncontext: fork\n---\nReturn the supplied number."},
                  {"path": "references/readme.md", "content": "Supporting text."}]
        directories = []
        def fake(command, **kwargs):
            directory = Path(kwargs["cwd"])
            directories.append(directory)
            self.assertEqual(command[command.index("--tools")+1], "Skill")
            self.assertIn("mcp__subject__read_submitted_file",command[command.index("--allowedTools")+1])
            self.assertIn("--restricted", command)
            self.assertIn("--strict-mcp-config", command)
            self.assertIn(SUBJECT_SKILL, kwargs["prompt"])
            self.assertNotIn("expected", kwargs["prompt"])
            self.assertFalse(Path(kwargs["env"]["CLAUDE_CONFIG_DIR"]).is_relative_to(directory))
            settings = json.loads(command[command.index("--settings")+1])
            self.assertTrue(settings["disableSkillShellExecution"])
            self.assertEqual(settings["claudeMdExcludes"], ["**"])
            skill = (directory / "plugin/skills/submitted/SKILL.md").read_text()
            self.assertIn("Return the supplied number", skill)
            self.assertNotIn("allowed-tools", skill)
            self.assertNotIn("context: fork", skill)
            session = command[command.index("--session-id")+1]
            return 0, stream(session), b""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-api-for-boundary-test", "CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            for auth in ("api", "subscription"):
                subject = ClaudeCode(auth=auth, process=fake)
                observation = subject.observe(source=source, case_input={"input": "42"}, config=subject.identity, timeout_seconds=2)
                self.assertTrue(observation["invocation_verified"])
                self.assertEqual(observation["observed_model_ids"], ["claude-fixture-observed"])
                self.assertNotIn("fake-api", canonical(observation).decode())
                self.assertEqual(len(observation["source_pins"]), 2)
        self.assertTrue(all(not path.exists() for path in directories))

    def test_bare_is_api_only_and_controller_has_no_file_tools(self):
        for auth in ("subscription", "api"):
            command = ClaudeCode(auth=auth).command(Path("work"), "session", controller=True, mcp=Path("mcp.json"))
            self.assertEqual("--bare" in command, auth == "api")
            self.assertEqual(command[command.index("--tools")+1], "WebSearch")
            self.assertNotIn("--dangerously-skip-permissions", command)

    def test_missing_failed_or_wrong_invocation_is_rejected(self):
        for raw in (stream("session", skill="other"), stream("session", failed=True), stream("session", tool="Bash"),
                    stream("other-session"), b"not json"):
            with self.subTest(raw=raw), self.assertRaises(Fault):
                parse_events(raw, expected_session="session", subject=True)

    def test_automatic_end_conversation_is_accepted_without_extra_file_tools(self):
        events=stream("session").splitlines()
        events.insert(2,canonical({"type":"assistant","message":{"content":[
            {"type":"tool_use","id":"end","name":"EndConversation","input":{}}]}}))
        result=parse_events(b"\n".join(events),expected_session="session",subject=True,extra_tools=("mcp__subject__read_submitted_file",))
        self.assertTrue(result["invocation_verified"])

    def test_dynamic_shell_and_code_are_rejected_before_launch(self):
        for filename, content in (("SKILL.md", "!`echo evil`"), ("SKILL.md", "```!\necho evil\n```"),
                                  ("script.py", "print('evil')"), (".claude/settings.json", "{}")):
            with tempfile.TemporaryDirectory() as temporary, self.assertRaises(Fault):
                source = [{"path": "SKILL.md", "content": "Plain skill"}]
                if filename == "SKILL.md":
                    source = [{"path": filename, "content": content}]
                else:
                    source.append({"path": filename, "content": content})
                stage_skill(Path(temporary), source)

    def test_real_process_timeout_is_bounded(self):
        started = time.monotonic()
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(Fault) as caught:
            run_process([sys.executable, "-c", "import time; time.sleep(30)"], cwd=temporary,
                        env=dict(os.environ), prompt="", timeout=0.15)
        self.assertEqual(caught.exception.code, "claude_timeout")
        self.assertLess(time.monotonic()-started, 12)

    def test_real_process_output_overflow_is_bounded(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(Fault) as caught:
            run_process([sys.executable, "-c", "import sys; sys.stdout.write('x'*100000)"], cwd=temporary,
                        env=dict(os.environ), prompt="", timeout=5, max_bytes=1000)
        self.assertEqual(caught.exception.code, "claude_output_limit")

    def test_real_process_receives_stdin_without_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            code, out, err = run_process([sys.executable, "-c", "import sys; print(sys.stdin.read())"], cwd=temporary,
                        env=dict(os.environ), prompt="Literal $(danger) `data`", timeout=5)
        self.assertEqual(code, 0)
        self.assertIn(b"Literal $(danger) `data`", out)

    def test_timeout_terminates_descendant_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "should-not-exist"
            child = "import time,pathlib; time.sleep(1.2); pathlib.Path(" + repr(str(marker)) + ").write_text('orphan')"
            parent = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); time.sleep(30)"
            with self.assertRaises(Fault):
                run_process([sys.executable, "-c", parent], cwd=temporary, env=dict(os.environ), prompt="", timeout=0.3)
            time.sleep(1.3)
            self.assertFalse(marker.exists())

    def test_secret_echo_is_rejected_and_temp_removed(self):
        dirs = []
        def fake(command, **kwargs):
            dirs.append(Path(kwargs["cwd"]))
            return 0, stream(command[command.index("--session-id")+1], output="private-opaque-token"), b""
        subject = ClaudeCode(auth="subscription", process=fake)
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "private-opaque-token"}), self.assertRaises(Fault):
            subject.observe(source=[{"path": "SKILL.md", "content": "Return text."}], case_input={"input": "test"}, config=subject.identity, timeout_seconds=1)
        self.assertTrue(all(not path.exists() for path in dirs))


if __name__ == "__main__":
    unittest.main()
