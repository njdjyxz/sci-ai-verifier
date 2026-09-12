"""Local resource checks reject traversal, malformed tables and changed pins."""

import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault,digest
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.local_resources import inspect_resource,import_configured
from sci_ai_verifier.app_bridge import call_adapter


class ResourceTests(unittest.TestCase):
    def test_tables_json_archives_and_binary(self):
        settings=load_configuration()
        for format,raw in (("csv",b"a,b\n1,2\n"),("json",b'{"number":1}'),("binary",b"\0\xff")):
            self.assertEqual(inspect_resource(raw,format,settings)["format"],format)
        for format,raw in (("csv",b"a,b\n1\n"),("json",b'{"a":1,"a":2}')):
            with self.assertRaises(Fault):
                inspect_resource(raw,format,settings)
        for name in ("../escape","/absolute","C:/drive"):
            data=io.BytesIO()
            with zipfile.ZipFile(data,"w") as archive:
                archive.writestr(name,b"test")
            with self.assertRaises(Fault):
                inspect_resource(data.getvalue(),"zip",settings)

    def test_resource_digest_and_operator_name_required(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"dataset.csv"
            file.write_bytes(b"a,b\n1,2\n")
            settings=load_configuration()
            settings["resources"]={"table":{"path":str(file),"sha256":digest(file.read_bytes()),"version":"1","license":"private","units":"none","description":"fixture"}}
            self.assertTrue(import_configured(settings,"table")[0])
            with self.assertRaises(Fault):
                import_configured(settings,"unknown")
            file.write_bytes(b"changed")
            with self.assertRaises(Fault):
                import_configured(settings,"table")

    def test_app_exec_is_fixed_and_model_json_is_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/"fixture.exe"
            exe.write_bytes(b"fake adapter; never executed")
            settings=load_configuration()
            settings["external_tools"]={"fixture":{"executable":str(exe),"sha256":digest(exe.read_bytes()),"arguments":["fixed"],"description":"Read-only test","credential_env":[],"read_only":True}}
            def fake(command,**kwargs):
                self.assertNotEqual(Path(kwargs["cwd"]),Path(directory))
                self.assertEqual(list(Path(kwargs["cwd"]).iterdir()),[])
                self.assertEqual(command,[str(exe),"fixed"])
                self.assertEqual(kwargs["prompt"],'{"query":"$(untrusted)"}')
                self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN",kwargs["env"])
                return 0,b'{"value":42}',b""
            self.assertEqual(call_adapter(settings,"fixture",{"query":"$(untrusted)"},cwd=directory,process=fake)["response"]["value"],42)
            exe.write_bytes(b"modified")
            with self.assertRaises(Fault):
                call_adapter(settings,"fixture",{},cwd=directory,process=fake)
            shell=Path(directory)/"cmd.exe"
            shell.write_bytes(b"fake shell; never executed")
            settings["external_tools"]["fixture"].update(executable=str(shell),sha256=digest(shell.read_bytes()))
            with self.assertRaises(Fault):
                call_adapter(settings,"fixture",{},cwd=directory,process=fake)


if __name__=="__main__":
    unittest.main()
