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
        self.not_kept=[]

    def process(self,command,**kwargs):
        self.commands.append((command,kwargs))
        if "context" in command:
            return 0,canonical(self.endpoint),b""
        if "inspect" in command:
            return 0,canonical([{"Os":"linux","Id":IMAGE}]),b""
        if "python3" in command and "-c" in command and "exec" in command:
            return 0,canonical({"files":self.files,"not_kept":self.not_kept}),b""
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
            files,not_kept=box.collect()
            self.assertEqual((files[0]["bytes"],not_kept),(7,[]))
            self.assertEqual(SubjectRuntime(box).call("run_command",{"command":"python3 script.py","stdin":"","timeout_seconds":5})["status"],"ok")
            # The tool is what a subject reads before each call; run 84e90683's ran pip anyway.
            self.assertIn("nothing can be downloaded or installed",SubjectRuntime(box).definitions[0]["description"])
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

    def test_a_docker_client_fault_is_the_sandboxs_and_not_the_subjects(self):
        """A docker command that hung was reported as the subject reaching its per-trial limit."""
        with patch("shutil.which",return_value="docker.exe"),self.box() as box:
            real=self.process
            for raised,expected in (("claude_timeout","sandbox_timeout"),("claude_output_limit","sandbox_output_limit"),
                                    ("claude_unavailable","sandbox_unavailable")):
                def failing(command,raised=raised,**kwargs):
                    if "exec" in command:
                        raise Fault(raised,"fixture")
                    return real(command,**kwargs)
                box.process=failing
                with self.subTest(raised=raised),self.assertRaises(Fault) as caught:
                    box.command("python3 x.py",timeout=5)
                self.assertEqual(caught.exception.code,expected)
                self.assertIn("exec -i, 5 s",str(caught.exception))
            box.process=real

    def test_a_stopped_engine_is_named_as_such_at_preflight(self):
        """A stopped Docker Desktop was reported as the pinned image being absent."""
        def answer(stderr):
            def process(command,**kwargs):
                if "context" in command:
                    return 0,canonical(self.endpoint),b""
                return 1,b"",stderr
            return process
        down=(b'error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.47/images/x/json": '
              b'open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.')
        with patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault) as caught:
            DockerSandbox(self.directory,self.settings,process=answer(down)).preflight()
        self.assertEqual(caught.exception.code,"sandbox_unavailable")
        self.assertIn("Docker is not running",str(caught.exception))
        with patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault) as caught:
            DockerSandbox(self.directory,self.settings,process=answer(b"Error response from daemon: No such image: x")).preflight()
        self.assertEqual(caught.exception.code,"sandbox_image_unavailable")

    def test_artifact_names_a_host_cannot_save_are_refused(self):
        """A generated file is saved under the run's artifact directory on the host, so a device name, a
        control character or a long path would fail the write after the trial was paid for."""
        for path in ("nul.txt","out/CON","a\x01b.txt","x"*151+".txt"):
            self.files=[{"path":path,"base64":base64.b64encode(b"x").decode()}]
            with self.subTest(path=path),patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault) as caught:
                with self.box() as box:
                    box.collect()
            self.assertEqual(caught.exception.code,"sandbox_artifacts_invalid")
        self.files=[{"path":"out/console.txt","base64":base64.b64encode(b"x").decode()}]
        with patch("shutil.which",return_value="docker.exe"),self.box() as box:
            self.assertEqual([item["path"] for item in box.collect()[0]],["out/console.txt"])

    def test_a_staged_file_still_held_never_fails_the_trial(self):
        """Docker Desktop can hold a bind-mounted file for a moment after the container is removed; a raise
        from the cleanup replaced the trial's own outcome."""
        import shutil
        events=[]

        class Log:
            def emit(self,event,**data):
                events.append(event)
        (self.directory/"readable.txt").write_text("original")
        with patch("shutil.which",return_value="docker.exe"),patch("sci_ai_verifier.claude_runner.CLEANUP_PAUSE",0):
            box=DockerSandbox(self.directory,self.settings,process=self.process,log=Log())
            with box:
                staged=box.source
                self.addCleanup(shutil.rmtree,staged.parent,True)
                with (staged/"readable.txt").open("rb"):
                    box.close()
        self.assertIsNone(box.staging)
        if staged.exists():  # Windows: the open handle kept it; it was logged and left, never raised
            self.assertIn("temporary_cleanup_incomplete",events)

    def test_a_file_past_the_limits_is_left_behind_only_beside_the_kept_results(self):
        """Run 55d345a3's skill wrote a 4 MiB signal table beside its results, which voided the claim."""
        self.files=[{"path":"results.json","base64":base64.b64encode(b"{}").decode()}]
        self.not_kept=[{"path":"signals.csv","bytes":25000000}]
        with patch("shutil.which",return_value="docker.exe"),self.box() as box:
            files,not_kept=box.collect(keep="results.json")
            self.assertEqual(([item["path"] for item in files],not_kept),(["results.json"],self.not_kept))
            sent=next(command for command,_ in reversed(self.commands) if "-c" in command)
            self.assertEqual(json.loads(sent[-1])["keep"],"results.json")
        # Without a file to keep, or for the kept file itself, a limit is still a fault.
        for keep,left in ((None,"signals.csv"),("results.json","results.json"),("results.json","../outside")):
            self.not_kept=[{"path":left,"bytes":5}]
            with self.subTest(keep=keep,left=left),patch("shutil.which",return_value="docker.exe"),self.assertRaises(Fault) as caught:
                with self.box() as box:
                    box.collect(keep=keep)
            self.assertEqual(caught.exception.code,"sandbox_artifacts_invalid")

    def test_the_collect_script_keeps_the_results_first_and_names_what_it_left(self):
        import subprocess
        from sci_ai_verifier.sandbox import COLLECT
        script=COLLECT.replace("root='/work'","root=__import__('sys').argv[2]")
        # Windows has no O_NOFOLLOW; the container's Linux does.
        script=script.replace("f|os.O_NOFOLLOW","f|getattr(os,'O_NOFOLLOW',0)")
        self.assertNotEqual(script,COLLECT)
        for name,raw in (("a_large.csv",b"x"*2048),("notes.txt",b"ok"),("results.json",b"{}"),("z.txt",b"z")):
            (self.directory/name).write_bytes(raw)
        limits={"max_file_bytes":1024,"max_artifacts":2,"max_artifact_bytes":4096}

        def collect(keep):
            done=subprocess.run([sys.executable,"-I","-c",script,canonical({**limits,"keep":keep}).decode(),
                                 str(self.directory)],capture_output=True,timeout=60)
            return done.returncode,done.stdout
        code,out=collect("results.json")
        self.assertEqual(code,0)
        found=json.loads(out)
        self.assertEqual([item["path"] for item in found["files"]],["results.json","notes.txt"])
        # One file too large, one past the count.
        self.assertEqual(found["not_kept"],[{"path":"a_large.csv","bytes":2048},{"path":"z.txt","bytes":1}])
        self.assertNotEqual(collect(None)[0],0)
        (self.directory/"results.json").write_bytes(b"x"*2048)
        self.assertNotEqual(collect("results.json")[0],0)

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
        plugin,pins,_=stage_skill(self.directory,source)
        self.assertEqual((plugin/"skills/submitted/input.bin").read_bytes(),b"\x00\xff")
        self.assertEqual(len(pins),3)
        events=stream("session").splitlines()
        events.insert(2,canonical({"type":"assistant","message":{"content":[{"type":"tool_use","id":"c","name":"Read","input":{"file_path":"C:/secret"}}]}}))
        with self.assertRaises(Fault):
            parse_events(b"\n".join(events),expected_session="session",subject=True,extra_tools=("mcp__subject__run_command",))

    def test_config_rejects_mutable_images_unknown_keys_and_bad_limits(self):
        path=self.directory/"settings.json"
        for value in ({"sandbox_image":"python:latest"},{"allow_host_shell":True},{"trial_count":0},{"trial_count":True},
                      {"package_index":"http://pypi.org/simple"},{"max_packages":0}):
            path.write_bytes(canonical(value))
            with self.assertRaises(Fault):
                load_configuration(path)

    def test_an_app_credential_may_not_take_a_name_the_cli_owns(self):
        """A configuration naming CLAUDE_CONFIG_DIR or ANTHROPIC_BASE_URL would re-point the subject and planner
        sessions, since app credentials are copied after their isolated environment is set."""
        import sys
        path=self.directory/"settings.json"

        def settings(names):
            return canonical({"external_tools":{"app":{"executable":sys.executable,"sha256":"a"*64,"arguments":[],
                                                       "description":"Fixture","credential_env":names,"read_only":True}}})
        path.write_bytes(settings(["LAB_API_TOKEN","MY_APP_KEY"]))
        self.assertEqual(load_configuration(path)["external_tools"]["app"]["credential_env"],["LAB_API_TOKEN","MY_APP_KEY"])
        for name in ("CLAUDE_CONFIG_DIR","CLAUDE_CODE_NO_MODEL_FALLBACK","ANTHROPIC_BASE_URL","ANTHROPIC_AUTH_TOKEN",
                     "SCI_VERIFIER_INTERNAL_CREDENTIAL","PYTHONPATH","PYTHONSTARTUP","NODE_EXTRA_CA_CERTS","HTTPS_PROXY",
                     "NO_PROXY","PATH","HOME","TEMP"):
            path.write_bytes(settings([name]))
            with self.subTest(name=name),self.assertRaises(Fault):
                load_configuration(path)


if __name__=="__main__":
    unittest.main()
