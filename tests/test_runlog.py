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
from sci_ai_verifier.common import Fault, canonical, digest
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

    def test_threads_of_one_process_share_one_valid_event_chain(self):
        """Claim-only sessions run four at a time, each logging its stream from its own thread."""
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as directory:
            log = WorkflowLog(directory)
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda index: log.emit("thread", index=index), range(40)))
            log.emit("threads_finished")
            records = [json.loads(line) for line in Path(log.paths["jsonl_path"]).read_text().splitlines()]
            self.assertEqual([item["sequence"] for item in records], list(range(1, 42)))
            self.assertEqual([item["previous_digest"] for item in records[1:]], [item["digest"] for item in records[:-1]])
            self.assertEqual(sorted(item["data"]["index"] for item in records[:-1]), list(range(40)))

    def test_threads_keep_one_chain_where_the_file_lock_admits_them_all(self):
        """POSIX file locks do not exclude threads of the process that holds them, so on Linux or
        macOS only the in-process lock keeps concurrent emits from racing for one sequence."""
        from concurrent.futures import ThreadPoolExecutor
        admit_all = lambda descriptor: (lambda: None, lambda: None)
        with tempfile.TemporaryDirectory() as directory, patch("sci_ai_verifier.runlog.file_lock", admit_all):
            log = WorkflowLog(directory)
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda index: log.emit("thread", index=index), range(40)))
            records = [json.loads(line) for line in Path(log.paths["jsonl_path"]).read_text().splitlines()]
            self.assertEqual([item["sequence"] for item in records], list(range(1, 41)))
            self.assertEqual([item["previous_digest"] for item in records[1:]], [item["digest"] for item in records[:-1]])

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

    def test_an_event_changed_after_it_was_verified_is_still_detected(self):
        """A write reads back only new or changed files, so a verified one is read again once it changes."""
        with tempfile.TemporaryDirectory() as directory:
            for rehashed in (False, True):
                log = WorkflowLog(directory)
                for index in range(4):
                    log.emit("event", index=index)
                event = log.directory/"events/00000001.json"
                data = json.loads(event.read_bytes())
                data["event"] = "forged-event"
                if rehashed:
                    # A forged event with a correct digest of its own still breaks the next one's link.
                    data["digest"] = digest(canonical({key: value for key, value in data.items() if key != "digest"}))
                event.write_bytes(canonical(data))
                with self.assertRaises(Fault) as caught:
                    log.emit("finished")
                self.assertEqual(caught.exception.code, "workflow_log_corrupted")

    def test_a_write_reads_back_only_events_it_has_not_verified(self):
        """Run d416f79d re-read every earlier event on every write, and a write took 0.94 s by the 2,100th."""
        import sci_ai_verifier.runlog as runlog
        with tempfile.TemporaryDirectory() as directory:
            log = WorkflowLog(directory)
            for index in range(30):
                log.emit("event", index=index)
            read, check = [], runlog.no_links
            def counting(path):
                if Path(path).parent.name == "events":
                    read.append(Path(path).name)
                return check(path)
            with patch("sci_ai_verifier.runlog.no_links", counting):
                log.emit("next")
                self.assertEqual(read, ["00000030.json"])
                # Another writer, like a child process, verifies the whole chain once.
                WorkflowLog(directory, attempt_id=log.attempt_id).emit("other")
                self.assertEqual(len(read), 1+31)
                del read[:]
                log.emit("after")
                self.assertEqual(read, ["00000031.json", "00000032.json"])
            records = [json.loads(line) for line in Path(log.paths["jsonl_path"]).read_text().splitlines()]
            self.assertEqual([item["sequence"] for item in records], list(range(1, 34)))
            self.assertEqual([item["previous_digest"] for item in records[1:]], [item["digest"] for item in records[:-1]])

    @staticmethod
    def sequences(log):
        return [json.loads(line)["sequence"] for line in Path(log.paths["jsonl_path"]).read_bytes().splitlines()]

    def test_a_projection_is_extended_and_rewritten_only_when_it_is_not_whole(self):
        """Run d416f79d rewrote both projections on every event, and a write took a second by the 2,100th."""
        with tempfile.TemporaryDirectory() as directory:
            log = WorkflowLog(directory)
            log.emit("first")
            replaced, real = [], os.replace

            def counting(source, target):
                replaced.append(Path(target).name)
                return real(source, target)
            with patch("sci_ai_verifier.storage.os.replace", counting):
                log.emit("second")
                log.emit("third")
                # Another writer, such as the subject server, finds the projections whole and extends them too.
                WorkflowLog(directory, attempt_id=log.attempt_id).emit("fourth")
            self.assertEqual(replaced, ["00000002.json", "00000003.json", "00000004.json"])
            self.assertEqual(self.sequences(log), [1, 2, 3, 4])
            # Extended or rewritten, a projection holds the same bytes.
            other = WorkflowLog(directory, attempt_id=log.attempt_id)
            other.verify()
            self.assertEqual(Path(log.paths["jsonl_path"]).read_bytes(), b"".join(entry["jsonl"] for entry in other.verified))
            self.assertEqual(Path(log.paths["markdown_path"]).read_bytes(),
                             other.header + b"".join(entry["markdown"] for entry in other.verified))
            self.assertIn("4. ", Path(log.paths["markdown_path"]).read_text(encoding="utf-8"))
            # A projection left short, as a stopped write leaves it, is rewritten whole.
            Path(log.paths["jsonl_path"]).write_bytes(Path(log.paths["jsonl_path"]).read_bytes()[:-5])
            log.emit("fifth")
            self.assertEqual(self.sequences(log), [1, 2, 3, 4, 5])

    def test_a_replace_a_reader_refuses_is_retried(self):
        """Windows refuses to replace a file another process holds open; run 74000d89 lost two claims to a
        monitor reading workflow.jsonl at the wrong moment."""
        refusals, real = [PermissionError(13, "held"), PermissionError(13, "held")], os.replace

        def flaky(source, target):
            if refusals and Path(target).name == "workflow.jsonl":
                raise refusals.pop()
            return real(source, target)
        with tempfile.TemporaryDirectory() as directory, patch("sci_ai_verifier.storage.os.replace", flaky), \
                patch("sci_ai_verifier.storage.REPLACE_PAUSE_SECONDS", 0):
            log = WorkflowLog(directory)
            log.emit("first")
            self.assertEqual(refusals, [])
            self.assertEqual(self.sequences(log), [1])

    def test_a_projection_that_stays_held_is_left_to_the_next_write(self):
        """The event file is the record; a projection a reader keeps open is a reading aid that can wait."""
        held, real = {"jsonl": True}, os.replace

        def refusing(source, target):
            if held["jsonl"] and Path(target).name == "workflow.jsonl":
                raise PermissionError(13, "held")
            return real(source, target)
        with tempfile.TemporaryDirectory() as directory, patch("sci_ai_verifier.storage.os.replace", refusing), \
                patch("sci_ai_verifier.storage.REPLACE_PAUSE_SECONDS", 0):
            log = WorkflowLog(directory)
            record = log.emit("first")
            self.assertEqual(record["sequence"], 1)
            self.assertTrue((log.directory / "events/00000001.json").is_file())
            self.assertFalse(Path(log.paths["jsonl_path"]).exists())
            self.assertIn("1. ", Path(log.paths["markdown_path"]).read_text(encoding="utf-8"))
            held["jsonl"] = False
            log.emit("second")
            self.assertEqual(self.sequences(log), [1, 2])

    @unittest.skipUnless(os.name == "nt", "Windows sharing rules")
    def test_a_reader_holding_the_projection_open_never_stops_a_write(self):
        with tempfile.TemporaryDirectory() as directory, patch("sci_ai_verifier.storage.REPLACE_PAUSE_SECONDS", 0.01):
            log = WorkflowLog(directory)
            log.emit("first")
            path = Path(log.paths["jsonl_path"])
            with path.open("rb") as reader:
                log.emit("second")  # extended beside the open handle
                self.assertEqual(self.sequences(log), [1, 2])
                with path.open("r+b") as handle:
                    handle.truncate(len(path.read_bytes()) - 3)  # a stopped write's leftovers
                log.emit("third")  # the rewrite is refused while the reader holds the file, and waits
                self.assertEqual(reader.read()[:1], b"{")
            log.emit("fourth")
            self.assertEqual(self.sequences(log), [1, 2, 3, 4])

    def test_log_write_failure_stops_child_process(self):
        def observer(name, chunk):
            raise Fault("workflow_log_unavailable", "disk unavailable")
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(Fault) as caught:
            run_process([sys.executable, "-c", "import time; print('data',flush=True); time.sleep(30)"],
                        cwd=directory, env=dict(os.environ), prompt="", timeout=5, observer=observer)
        self.assertEqual(caught.exception.code, "workflow_log_unavailable")


if __name__ == "__main__":
    unittest.main()
