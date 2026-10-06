"""CLI boundary tests: no model/network calls; real child processes for limits."""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.claude_runner import (ClaudeCode, SUBJECT_SKILL, isolated_environment,
    parse_events, prepare_workspace, refusal_category, run_process, session_directory, stage_skill,
    sweep_stale_directories)
from sci_ai_verifier.common import Fault, canonical
from sci_ai_verifier.local_config import load_configuration


NEWLINE = bytes([10])
IMAGE = "sha256:" + "a" * 64


class FakeSandbox:
    """Stands in for a trial's container: keeps what it was given and collects nothing."""
    opened = []

    def __init__(self, source, settings, *, timeout=None, log=None, inputs=None):
        self.source, self.settings, self.inputs = Path(source), settings, inputs
        self.name, self.docker, self.endpoint = "sci-verifier-" + "0" * 32, "docker", "npipe:////./pipe/docker_engine"
        self.deadline = time.time() + 60
        FakeSandbox.opened.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *error):
        return False

    def collect(self):
        return []


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
            self.assertIn("mcp__subject__run_command",command[command.index("--allowedTools")+1])
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
        settings = {**load_configuration(), "sandbox_image": IMAGE}
        given = {"task": "Return the supplied number as value.", "results_file": "/work/results.json"}
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-api-for-boundary-test", "CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}), \
                patch("sci_ai_verifier.sandbox.DockerSandbox", FakeSandbox):
            for auth in ("api", "subscription"):
                subject = ClaudeCode(auth=auth, process=fake, settings=settings)
                observation = subject.observe(source=source, case_input=given, config=subject.identity, timeout_seconds=2,
                                              task_files={"numbers.csv": b"n\n42\n"})
                # The task's files reach the trial's container, which runs the staged skill.
                self.assertEqual(FakeSandbox.opened[-1].inputs, {"numbers.csv": b"n\n42\n"})
                self.assertEqual(FakeSandbox.opened[-1].settings["sandbox_image"], IMAGE)
                self.assertTrue(observation["invocation_verified"])
                self.assertEqual(observation["observed_model_ids"], ["claude-fixture-observed"])
                self.assertNotIn("fake-api", canonical(observation).decode())
                self.assertEqual(len(observation["source_pins"]), 2)
        self.assertTrue(all(not path.exists() for path in directories))
        # With no container image there is nowhere to run a task, so no session starts.
        with self.assertRaises(Fault) as caught:
            ClaudeCode(process=fake, settings=load_configuration()).observe(
                source=source, case_input=given, config={}, timeout_seconds=2)
        self.assertEqual(caught.exception.code, "sandbox_configuration_required")
        self.assertEqual(len(directories), 2)

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
        result=parse_events(b"\n".join(events),expected_session="session",subject=True,extra_tools=("mcp__subject__run_command",))
        self.assertTrue(result["invocation_verified"])

    def test_dynamic_shell_and_configuration_are_rejected_but_scripts_are_staged(self):
        # A trial runs the skill's own scripts in its container, so a script is staged as a file.
        with tempfile.TemporaryDirectory() as temporary:
            plugin, pins = stage_skill(Path(temporary), [{"path": "SKILL.md", "content": "Plain skill"},
                                                         {"path": "scripts/fit.py", "content": "print('fit')"}])
            self.assertEqual((plugin / "skills/submitted/scripts/fit.py").read_text(), "print('fit')")
            self.assertEqual([pin["path"] for pin in pins], ["SKILL.md", "scripts/fit.py"])
        for filename, content in (("SKILL.md", "!`echo evil`"), ("SKILL.md", "```!\necho evil\n```"),
                                  ("notes.md", "!`echo evil`"), (".claude/settings.json", "{}")):
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

    def test_output_survives_a_grandchild_holding_the_pipe_open(self):
        """A complete answer must not be discarded because a reader is still parked.

        Claude Code launches the subject MCP server as its own child, which inherits the
        stdout handle and can outlive it. The pipe then stays open after Claude Code exits,
        with the full reply already buffered. Run e035eef6 threw away a correct subject
        answer exactly this way and lost the twelve trials that were queued behind it.
        """
        grandchild = "import time; time.sleep(3)"
        child = ("import subprocess,sys; sys.stdout.write('COMPLETE-OUTPUT'); sys.stdout.flush(); "
                 "subprocess.Popen([sys.executable,'-c'," + repr(grandchild) + "])")
        with tempfile.TemporaryDirectory() as temporary:
            with patch("sci_ai_verifier.claude_runner.DRAIN_GRACE_SECONDS", 0.3):
                code, out, _ = run_process([sys.executable, "-c", child], cwd=temporary,
                                           env=dict(os.environ), prompt="", timeout=10)
        self.assertEqual(code, 0)
        self.assertIn(b"COMPLETE-OUTPUT", out)

    def test_a_slow_observer_leaves_no_output_unread(self):
        """Run d416f79d: the readers logged as they read, a log write took about a second, and
        two finished claim-only answers were still unread when the drain grace expired."""
        child = ("import sys,time; sys.stdout.buffer.write(b'first\\n'); sys.stdout.flush(); time.sleep(0.2); "
                 "sys.stdout.buffer.write(b'second\\nthird\\n'); sys.stdout.flush()")
        seen, callers = [], set()
        def slow(name, chunk):
            callers.add(threading.get_ident())
            seen.append((name, chunk))
            time.sleep(1)
        with tempfile.TemporaryDirectory() as temporary:
            with patch("sci_ai_verifier.claude_runner.DRAIN_GRACE_SECONDS", 0.3):
                code, out, _ = run_process([sys.executable, "-c", child], cwd=temporary,
                                           env=dict(os.environ), prompt="", timeout=20, observer=slow)
        self.assertEqual(code, 0)
        self.assertEqual(out, b"first\nsecond\nthird\n")
        # The observer saw exactly what was returned, on the thread that waited for the process.
        self.assertEqual(b"".join(chunk for name, chunk in seen if name == "stdout"), out)
        self.assertEqual(callers, {threading.get_ident()})

    def test_a_safety_refusal_is_recognised_and_an_ordinary_stream_is_not(self):
        refusal = canonical({"type": "system", "subtype": "model_refusal_no_fallback",
                             "api_refusal_category": "bio"})
        joined = NEWLINE.join([refusal, stream("session")])
        self.assertEqual(refusal_category(joined), "bio")
        # A refusal event without a category is still a refusal, not a crash.
        bare = canonical({"type": "system", "subtype": "model_refusal_fallback"})
        self.assertEqual(refusal_category(bare), "unspecified")
        self.assertIsNone(refusal_category(stream("session")))
        self.assertIsNone(refusal_category(b"not json at all"))

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


def extended(path):
    """The extended-length form, the only way to reach a path past 260 characters on a Windows
    machine without long-path support; the tests build and remove their deep files through it."""
    text = os.path.abspath(path)
    return "\\\\?\\" + text if os.name == "nt" else text


def deep_file(root):
    """A file more than 260 characters deep, like the tool result the planner's Claude Code saves
    under `config/projects/<workspace name>/<session>/tool-results/` (273 to 277 in run 0aeca4c6)."""
    target = os.path.join(root, *(["d" * 60] * 5), "result.txt")
    os.makedirs(extended(os.path.dirname(target)))
    with open(extended(target), "wb") as handle:
        handle.write(b"x")
    return target


class StaleSweepTests(unittest.TestCase):
    def test_a_file_past_the_windows_path_limit_does_not_keep_a_directory(self):
        # Each of the 25 controller directories left in %TEMP% from 2026-09-23 on held one.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as root:
            self.addCleanup(shutil.rmtree, extended(root), True)
            old = Path(root) / "sci-verifier-controller-old"
            self.assertGreater(len(os.path.abspath(deep_file(old))), 260)
            now = time.time()
            os.utime(old, (now - 2 * 86400, now - 2 * 86400))
            self.assertEqual(sweep_stale_directories(None, root=root, now=now), (1, 0))
            self.assertFalse(old.exists())

    def test_only_this_verifiers_directories_older_than_a_day_are_removed(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            now = time.time()
            old, young, foreign = root / "sci-verifier-controller-old", root / "sci-verifier-subject-new", root / "other-old"
            for path in (old, young, foreign):
                (path / "config").mkdir(parents=True)
                (path / "config" / "file").write_bytes(b"x")
            for path in (old, foreign):
                os.utime(path, (now - 2 * 86400, now - 2 * 86400))
            events = []

            class Log:
                def emit(self, event, **data):
                    events.append((event, data))

            self.assertEqual(sweep_stale_directories(Log(), root=root, now=now), (1, 0))
            self.assertFalse(old.exists())
            self.assertTrue(young.exists())   # a run in progress is never swept
            self.assertTrue(foreign.exists())  # nothing without this verifier's prefix
            self.assertEqual(events, [("stale_temporary_swept", {"removed": 1, "still_held": 0})])
            # Nothing to do logs nothing.
            events.clear()
            self.assertEqual(sweep_stale_directories(Log(), root=root, now=now), (0, 0))
            self.assertEqual(events, [])

class SessionDirectoryTests(unittest.TestCase):
    """A child still holding a file must not turn a finished session into a failure."""

    class Log:
        def __init__(self):
            self.events = []

        def emit(self, event, **data):
            self.events.append((event, data))

    def test_removal_is_retried_until_the_directory_is_gone(self):
        import shutil
        real, calls = shutil.rmtree, []

        def held_twice(path, ignore_errors=False):
            calls.append(path)
            if len(calls) > 2:
                real(path, ignore_errors=ignore_errors)

        log = self.Log()
        with patch("sci_ai_verifier.claude_runner.CLEANUP_PAUSE", 0),                 patch("sci_ai_verifier.claude_runner.shutil.rmtree", side_effect=held_twice):
            with session_directory("sci-verifier-test-", log) as temporary:
                (Path(temporary) / "file").write_bytes(b"x")
        self.assertFalse(Path(temporary).exists())
        self.assertEqual(len(calls), 3)
        self.assertEqual(log.events, [])

    def test_a_file_past_the_windows_path_limit_is_removed(self):
        # Every controller session saves one; until removal reached it, each run left its
        # directory and logged temporary_cleanup_incomplete.
        log = self.Log()
        with patch("sci_ai_verifier.claude_runner.CLEANUP_PAUSE", 0):
            with session_directory("sci-verifier-test-", log) as temporary:
                self.addCleanup(shutil.rmtree, extended(temporary), True)
                self.assertGreater(len(os.path.abspath(deep_file(temporary))), 260)
        self.assertFalse(Path(temporary).exists())
        self.assertEqual(log.events, [])

    def test_a_directory_that_stays_held_is_logged_and_never_raised(self):
        log = self.Log()
        with patch("sci_ai_verifier.claude_runner.CLEANUP_PAUSE", 0),                 patch("sci_ai_verifier.claude_runner.shutil.rmtree"):
            with session_directory("sci-verifier-test-", log) as temporary:
                pass
        try:
            self.assertEqual([event for event, _ in log.events], ["temporary_cleanup_incomplete"])
            self.assertEqual(log.events[0][1]["path"], temporary)
        finally:
            import shutil
            shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
