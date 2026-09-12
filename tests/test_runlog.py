"""Durability and credential exclusions across failed and concurrent workflow runs."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))

from sci_ai_verifier.claude_runner import ClaudeCode, run_process
from sci_ai_verifier.common import Fault, canonical
from sci_ai_verifier.local_entry import verify
from sci_ai_verifier.runlog import WorkflowLog, StreamLog

ROOT = Path(__file__).resolve().parents[1]


class LogTests(unittest.TestCase):
    def test_preflight_failure_returns_durable_attempt_without_run(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/"SKILL.md"
            source.write_text("Return the input")
            with patch.object(ClaudeCode, "preflight", side_effect=Fault("claude_unavailable", "Missing CLI")):
                result = verify(source, workspace=directory, instructions=ROOT/"skills/scientific-verifier")
            self.assertEqual(result["error"]["code"], "claude_unavailable")
            records = [json.loads(line) for line in Path(result["log"]["jsonl_path"]).read_text().splitlines()]
            self.assertEqual([item["event"] for item in records],
                             ["verification_started", "setup_started", "verification_finished"])
            self.assertFalse((Path(directory)/".verifier/runs").exists())
            self.assertIn("Missing CLI", Path(result["log"]["markdown_path"]).read_text())

    def test_credentials_and_private_reasoning_are_removed_before_persistence(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "special-test-auth-value"}):
            log = WorkflowLog(directory)
            stream = StreamLog(log, "subject", "session")
            event = {"type": "assistant", "message": {"content": [
                {"type": "thinking", "thinking": "PRIVATE_THOUGHT"},
                {"type": "text", "text": "special-test-auth-value"},
                {"type": "tool_use", "input": {"password": "PRIVATE_PASSWORD"}}]}}
            raw = canonical(event)+b"\n"
            for index in range(0, len(raw), 7):
                stream("stdout", raw[index:index+7])
            stream("stderr", b"-----BEGIN "+b"PRIVATE KEY-----\nPRIVATE_KEY_BODY\n-----END PRIVATE KEY-----\n")
            stream.close()
            for path in log.directory.rglob("*"):
                if path.is_file():
                    for secret in (b"special-test-auth-value", b"PRIVATE_THOUGHT", b"PRIVATE_PASSWORD", b"PRIVATE_KEY_BODY"):
                        self.assertNotIn(secret, path.read_bytes(), path)

    def test_process_events_are_recorded_before_timeout_and_survive_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            log = WorkflowLog(directory)
            stream = StreamLog(log, "subject", "session")
            code = "import json,time; print(json.dumps({'type':'assistant','message':{'content':[{'type':'text','text':'started'}]}}),flush=True); time.sleep(30)"
            with self.assertRaises(Fault) as caught:
                run_process([sys.executable, "-c", code], cwd=directory, env=dict(os.environ), prompt="",
                            timeout=1, observer=stream)
            self.assertEqual(caught.exception.code, "claude_timeout")
            self.assertIn("started", Path(log.paths["jsonl_path"]).read_text())

    def test_child_processes_share_one_valid_event_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            log = WorkflowLog(directory)
            code = "import sys; from sci_ai_verifier.runlog import WorkflowLog; log=WorkflowLog(sys.argv[1],attempt_id=sys.argv[2]); [log.emit('child',index=i) for i in range(8)]"
            env = {**os.environ, "PYTHONPATH": str(ROOT/"src")}
            processes = [subprocess.Popen([sys.executable, "-c", code, directory, log.attempt_id],
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
            for process in processes:
                output, error = process.communicate(timeout=15)
                self.assertEqual(process.returncode, 0, error)
            log.emit("parent_finished")
            records = [json.loads(line) for line in Path(log.paths["jsonl_path"]).read_text().splitlines()]
            self.assertEqual([item["sequence"] for item in records], list(range(1,18)))

    def test_tampered_event_cannot_be_silently_reprojected(self):
        with tempfile.TemporaryDirectory() as directory:
            log = WorkflowLog(directory)
            log.emit("started")
            event = log.directory/"events/00000001.json"
            data = json.loads(event.read_bytes())
            data["event"] = "forged"
            event.write_bytes(canonical(data))
            with self.assertRaises(Fault) as caught:
                log.emit("finished")
            self.assertEqual(caught.exception.code, "workflow_log_corrupted")

    def test_log_write_failure_stops_child_process(self):
        def observer(name, chunk):
            raise Fault("workflow_log_unavailable", "disk unavailable")
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(Fault) as caught:
            run_process([sys.executable, "-c", "import time; print('data',flush=True); time.sleep(30)"],
                        cwd=directory, env=dict(os.environ), prompt="", timeout=5, observer=observer)
        self.assertEqual(caught.exception.code, "workflow_log_unavailable")


if __name__ == "__main__":
    unittest.main()
