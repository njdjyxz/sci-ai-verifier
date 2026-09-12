"""Container boundary tests use fake Docker, never a host shell or live daemon."""

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault,canonical
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.sandbox import DockerSandbox
from sci_ai_verifier.subject_server import SubjectRuntime
from sci_ai_verifier.claude_runner import stage_skill,parse_events
from test_claude_runner import stream

IMAGE="sha256:"+"a"*64


class SandboxTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory=Path(temp.name)
        self.settings={**load_configuration(),"sandbox_image":IMAGE}
        self.commands=[]
        self.endpoint="npipe:////./pipe/docker_engine"
        self.files=[{"path":"results/value.bin","base64":base64.b64encode(b"\0binary").decode()}]

    def process(self,command,**kwargs):
        self.commands.append((command,kwargs))
        if "context" in command:
            return 0,canonical(self.endpoint),b""
        if "inspect" in command:
            return 0,canonical([{"Os":"linux","Id":IMAGE}]),b""
        if "python3" in command and "-c" in command and "exec" in command:
            return 0,canonical(self.files),b""
        return 0,b"ok",b""

    def box(self):
        return DockerSandbox(self.directory,self.settings,process=self.process)

    def test_network_mount_credentials_and_cleanup(self):
        (self.directory/"readable.txt").write_text("original bytes")
        with patch("shutil.which",return_value="docker.exe"),self.box() as box:
            staged=box.source
            self.assertNotEqual(staged,self.directory)
            self.assertEqual((staged/"readable.txt").read_text(),"original bytes")
            run=next(command for command,_ in self.commands if "run" in command)
            self.assertEqual(run[run.index("--network")+1],"none")
            self.assertEqual(run[run.index("--user")+1],"65534:65534")
            self.assertIn("--read-only",run)
            self.assertEqual(run.count("--mount"),1)
            self.assertTrue(run[run.index("--mount")+1].endswith("target=/submission,readonly"))
            self.assertNotIn("ANTHROPIC_API_KEY",self.commands[-1][1]["env"])
            files=box.collect()
            self.assertEqual(files[0]["bytes"],7)
            self.assertEqual(SubjectRuntime(box).call("run_command",{"command":"python3 script.py","stdin":"","timeout_seconds":5})["status"],"ok")
            self.assertEqual(SubjectRuntime(box).call("run_command",{"command":"x","stdin":"","timeout_seconds":5,"container":"other"})["status"],"unavailable")
        self.assertEqual(self.commands[-1][0][-3:],["rm","--force",box.name])
        self.assertFalse(staged.exists())
        self.assertEqual((self.directory/"readable.txt").read_text(),"original bytes")

    def test_remote_engine_is_rejected_before_run(self):
        for endpoint in ("tcp://example.org:2375","npipe:////remote-host/pipe/docker_engine","unix://remote-host/socket"):
            self.endpoint=endpoint
            with patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault):
                with self.box():
                    self.fail("Must not execute")
        self.assertFalse(any("run" in command for command,_ in self.commands))

    def test_malicious_artifact_path_and_oversize_rejected_cleanup(self):
        for path in ("../outside", "/absolute", "C:/outside"):
            self.files[0]["path"]=path
            with patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault):
                with self.box() as box:
                    box.collect()
            self.assertIn("rm",self.commands[-1][0])
        self.files=[{"path":"large","base64":base64.b64encode(b"x"*1025).decode()}]
        self.settings["max_file_bytes"]=1024
        with patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault):
            with self.box() as box:
                box.collect()

    def test_source_copy_error_cleans_container(self):
        def failed(command,**kwargs):
            if "cp -R /submission/. /work/" in command:
                self.commands.append((command,kwargs))
                return 1,b"",b"copy failed"
            return self.process(command,**kwargs)
        with patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault):
            with DockerSandbox(self.directory,self.settings,process=failed):
                self.fail("Invalid copy")
        self.assertIn("rm",self.commands[-1][0])

    def test_scripts_and_binary_stage_with_exact_pins(self):
        source=[{"path":"SKILL.md","content":"Run scripts/calc.py on input.bin."},
                {"path":"scripts/calc.py","content":"print(42)"},
                {"path":"input.bin","base64":base64.b64encode(b"\x00\xff").decode()}]
        plugin,pins=stage_skill(self.directory,source,computational=True)
        self.assertEqual((plugin/"skills/submitted/input.bin").read_bytes(),b"\x00\xff")
        self.assertEqual(len(pins),3)
        events=stream("session").splitlines()
        events.insert(2,canonical({"type":"assistant","message":{"content":[{"type":"tool_use","id":"c","name":"Read","input":{"file_path":"C:/secret"}}]}}))
        with self.assertRaises(Fault):
            parse_events(b"\n".join(events),expected_session="session",subject=True,extra_tools=("mcp__subject__run_command",))

    def test_config_rejects_mutable_images_unknown_keys_and_bad_limits(self):
        path=self.directory/"settings.json"
        for value in ({"sandbox_image":"python:latest"},{"allow_host_shell":True},{"trial_count":0},{"trial_count":True}):
            path.write_bytes(canonical(value))
            with self.assertRaises(Fault):
                load_configuration(path)


if __name__=="__main__":
    unittest.main()
