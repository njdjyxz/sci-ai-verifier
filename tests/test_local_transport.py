"""Actual process cancellation and private MCP transport, without Claude or Docker."""

import io
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.claude_runner import run_process
from sci_ai_verifier.common import Fault,canonical
from sci_ai_verifier.execution_control import CURRENT,Control
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.local_entry import PublicRuntime
from sci_ai_verifier.mcp import serve
from sci_ai_verifier.runlog import WorkflowLog


class Input:
    def __init__(self):
        self.queue=queue.Queue()

    def readline(self,limit):
        return self.queue.get(timeout=10)

    def put(self,method,request_id=None,params=None):
        message={"jsonrpc":"2.0","method":method,"params":params or {}}
        if request_id is not None:
            message["id"]=request_id
        self.queue.put(canonical(message)+b"\n")


class TransportTests(unittest.TestCase):
    def exercise_cancel(self,close=False):
        with tempfile.TemporaryDirectory() as temporary:
            runtime=PublicRuntime(workspace=temporary,timeout=30)
            source,destination=Input(),io.BytesIO()
            started,finished=threading.Event(),threading.Event()
            observed=[]
            def fake_verify(*args,**kwargs):
                log=WorkflowLog(temporary)
                log.emit("verification_started")
                started.set()
                try:
                    run_process([sys.executable,"-c","import time; time.sleep(30)"],cwd=temporary,env=dict(os.environ),prompt="",timeout=30)
                    self.fail("Process should be cancelled")
                except Fault as error:
                    observed.append(error.code)
                    return {"status":"incomplete","error":{"code":error.code}}
                finally:
                    finished.set()
            source.put("initialize",1,{"protocolVersion":"2025-06-18"})
            source.put("notifications/initialized")
            source.put("tools/call",2,{"name":"verify_skill","arguments":{"source_path":temporary},"_meta":{"progressToken":"progress"}})
            with patch("sci_ai_verifier.local_entry.verify",side_effect=fake_verify):
                worker=threading.Thread(target=serve,args=(runtime,source,destination))
                worker.start()
                self.assertTrue(started.wait(5))
                if close:
                    source.queue.put(b"")
                else:
                    source.put("notifications/cancelled",params={"requestId":999})
                    source.put("tools/call",3,{"name":"verify_skill","arguments":{"source_path":temporary}})
                    source.put("ping",4)
                    source.put("notifications/cancelled",params={"requestId":2})
                self.assertTrue(finished.wait(5))
                if not close:
                    source.queue.put(b"")
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive())
            records=[json.loads(line) for line in destination.getvalue().splitlines()]
            self.assertEqual(observed,["verification_cancelled"])
            self.assertFalse(any(row.get("id")==2 for row in records))
            progress=[row["params"]["progress"] for row in records if row.get("method")=="notifications/progress"]
            self.assertTrue(progress)
            self.assertEqual(progress,sorted(set(progress)))
            if not close:
                self.assertTrue(next(row for row in records if row.get("id")==3).get("error"))
                self.assertEqual(next(row for row in records if row.get("id")==4)["result"],{})

    def test_cancel_notification_is_read_during_active_request(self):
        self.exercise_cancel()

    def test_connection_close_stops_active_request(self):
        self.exercise_cancel(close=True)

    def test_attempt_deadline_stops_a_process_before_its_own_timeout(self):
        with tempfile.TemporaryDirectory() as temporary:
            token=CURRENT.set(Control(0.1))
            started=time.monotonic()
            try:
                with self.assertRaises(Fault) as caught:
                    run_process([sys.executable,"-c","import time; time.sleep(30)"],cwd=temporary,env=dict(os.environ),prompt="",timeout=30)
                self.assertEqual(caught.exception.code,"verification_timeout")
                self.assertLess(time.monotonic()-started,5)
            finally:
                CURRENT.reset(token)

    def test_subject_tool_server_works_through_real_stdio_subprocess(self):
        """The trial's tool server as Claude Code starts it: a child process on stdio, bound to one
        container. Listing its tools and refusing an unknown one need no container."""
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            source=root/"submission"
            source.mkdir()
            binding=root/"binding.json"
            bound={"source":str(source),"settings":{**load_configuration(),"sandbox_image":"sha256:"+"a"*64},
                   "name":"sci-verifier-"+"0"*32,"docker":"docker","endpoint":"npipe:////./pipe/docker_engine",
                   "deadline":time.monotonic()+60,"log":None}
            binding.write_bytes(canonical(bound))
            requests=Input()
            requests.put("initialize",1,{"protocolVersion":"2025-06-18"})
            requests.put("notifications/initialized")
            requests.put("tools/list",2)
            requests.put("tools/call",3,{"name":"read_submitted_file","arguments":{"path":"note.md"}})
            raw=b"".join(list(requests.queue.queue))
            entry=Path(__file__).resolve().parents[1]/"src/sci_ai_verifier/subject_server.py"
            result=subprocess.run([sys.executable,str(entry),"--binding",str(binding)],input=raw,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            rows=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual([tool["name"] for tool in rows[1]["result"]["tools"]],["run_command"])
            self.assertTrue(rows[2]["result"]["isError"])
            # A binding naming a container the runner did not create is refused before anything is served.
            binding.write_bytes(canonical({**bound,"name":"another-container"}))
            refused=subprocess.run([sys.executable,str(entry),"--binding",str(binding)],input=raw,capture_output=True,timeout=10)
            self.assertNotEqual(refused.returncode,0)
            self.assertEqual(refused.stdout,b"")

if __name__=="__main__":
    unittest.main()
