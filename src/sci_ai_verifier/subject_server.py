"""Private tools bound by the host to one disposable subject container."""

import argparse
import json
import re
import sys
import time
import shlex
import base64
from urllib.parse import urlsplit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sci_ai_verifier.common import Fault, validate,canonical,digest
from sci_ai_verifier.mcp import serve
from sci_ai_verifier.sandbox import DockerSandbox,local_endpoint
from sci_ai_verifier.storage import no_links
from sci_ai_verifier.tools import obj, string


class TextRuntime:
    instructions="Read supporting files only from the pinned submitted skill. Paths are relative to its root."
    definitions=[{"name":"read_submitted_file","description":"Read a UTF-8 supporting file from the copied submitted skill by relative path.",
                  "inputSchema":obj({"path":string(200)})}]

    def __init__(self,source,log=None):
        self.source,self.log=no_links(source),log

    def call(self,name,arguments,call_id=None):
        try:
            from sci_ai_verifier.ingest import valid_relative,SECRET_BYTES
            if name!="read_submitted_file":
                raise Fault("unknown_tool","Only the bounded submitted-file reader is available.")
            validate(arguments,self.definitions[0]["inputSchema"])
            if not valid_relative(arguments["path"]):
                raise Fault("subject_path_invalid","Choose a relative path within the submitted skill.")
            path=no_links(self.source/arguments["path"])
            if not path.is_relative_to(self.source) or path.stat().st_size>131072:
                raise Fault("subject_file_limit","Supporting file is outside the source or exceeds its read limit.")
            raw=path.read_bytes()
            if SECRET_BYTES.search(raw):
                raise Fault("secret_material","Credential-like content cannot be read through the subject tool.")
            result={"path":arguments["path"],"text":raw.decode("utf-8"),"sha256":digest(raw)}
            if self.log:
                self.log.emit("subject_file_read",**result)
            return {"status":"ok","data":result}
        except (Fault,OSError,UnicodeError) as error:
            return {"status":"unavailable","error":{"code":getattr(error,"code","subject_file_unavailable"),"message":"The bounded submitted-file read failed."}}


class SubjectRuntime:
    instructions = "Run submitted scripts inside /work. Commands cannot access the host or network."
    definitions = [{"name":"run_command", "description":"Run a shell command in this trial's isolated Linux workspace /work, with bounded output and deadline.",
                    "inputSchema":obj({"command":string(16000), "stdin":{"type":"string","maxLength":131072},
                                       "timeout_seconds":{"type":"integer","minimum":1,"maximum":3600}})}]

    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.calls=0
        self.definitions=list(type(self).definitions)
        if sandbox.settings["allowed_subject_hosts"]:
            self.definitions.append({"name":"fetch_resource","description":"Download a public HTTPS resource from an operator-approved host into /work. No redirects or private addresses.",
                "inputSchema":obj({"url":string(4096),"path":string(200)})})
        if sandbox.settings["external_tools"]:
            self.definitions.append({"name":"call_app","description":"Call a configured read-only app with JSON input. Available apps: "+canonical({name:item["description"] for name,item in sandbox.settings["external_tools"].items()}).decode(),
                "inputSchema":obj({"app":string(40),"request_json":string(65536)})})

    def call(self, name, arguments, call_id=None):
        try:
            schema=next((item["inputSchema"] for item in self.definitions if item["name"]==name),None)
            if schema is None:
                raise Fault("unknown_tool", "Use this trial's declared tools only.")
            validate(arguments, schema)
            self.calls+=1
            remaining=self.sandbox.deadline-time.monotonic()
            if self.calls>64 or remaining<=0:
                raise Fault("subject_tool_limit","The trial's tool-call count or deadline was reached.")
            if name=="run_command":
                result=self.sandbox.command(arguments["command"],stdin=arguments["stdin"],timeout=arguments["timeout_seconds"])
            elif name=="call_app":
                from sci_ai_verifier.app_bridge import call_adapter
                from sci_ai_verifier.mcp import parse_json
                result=call_adapter(self.sandbox.settings,arguments["app"],parse_json(arguments["request_json"]),
                    cwd=self.sandbox.source,timeout=min(remaining,30),log=self.sandbox.log)
            else:
                from sci_ai_verifier.local_candidates import fetch_bytes
                from sci_ai_verifier.ingest import valid_relative
                if (urlsplit(arguments["url"]).hostname not in self.sandbox.settings["allowed_subject_hosts"]
                        or not valid_relative(arguments["path"])):
                    raise Fault("resource_not_authorized","Use a permitted public host and a relative output path.")
                raw,mime=fetch_bytes(arguments["url"],max_bytes=self.sandbox.settings["max_file_bytes"])
                # Creation in a fixed direct child prevents traversal through submitted symlinks.
                if "/" in arguments["path"]:
                    raise Fault("resource_path_invalid","Choose a filename directly inside /work for downloads.")
                script="import os,sys,base64; p=sys.argv[1]; f=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); h=os.fdopen(f,'wb'); h.write(base64.b64decode(sys.stdin.buffer.read(),validate=True)); h.close()"
                code,_,_=self.sandbox.invoke(["exec","-i",self.sandbox.name,"python3","-c",script,arguments["path"]],
                    prompt=base64.b64encode(raw).decode(),timeout=min(15,remaining),capture_output=False)
                if code:
                    raise Fault("resource_write_failed","Choose a new file name; existing files are never replaced by downloads.")
                result={"url":arguments["url"],"path":arguments["path"],"sha256":digest(raw),"bytes":len(raw),"content_type":mime}
                if self.sandbox.log:
                    self.sandbox.log.emit("subject_resource_downloaded",**result)
            return {"status":"ok", "data":result}
        except (Fault,OSError,ValueError,RecursionError) as error:
            return {"status":"unavailable","error":{"code":getattr(error,"code","sandbox_unavailable"),
                    "message":"The bounded subject operation failed; no automatic retry occurred."}}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--binding",required=True)
    args=parser.parse_args()
    path=no_links(args.binding)
    if path.stat().st_size>65536:
        raise ValueError("Invalid private binding")
    binding=json.loads(path.read_bytes())
    log=None
    if binding.get("log"):
        from sci_ai_verifier.runlog import WorkflowLog
        log=WorkflowLog(binding["log"]["workspace"],attempt_id=binding["log"]["attempt_id"])
    if binding.get("kind")=="text":
        serve(TextRuntime(binding["source"],log),sys.stdin.buffer,sys.stdout.buffer)
        return
    if not re.fullmatch(r"sci-verifier-[0-9a-f]{32}",binding["name"]):
        raise ValueError("Invalid container identity")
    if not local_endpoint(binding["endpoint"]):
        raise ValueError("Local engine required")
    sandbox=DockerSandbox(binding["source"],binding["settings"],log=log)
    sandbox.name,sandbox.docker,sandbox.endpoint=binding["name"],binding["docker"],binding["endpoint"]
    sandbox.deadline,sandbox.created=binding["deadline"],True
    # The parent alone owns cleanup. The tool cannot choose or replace the binding.
    serve(SubjectRuntime(sandbox),sys.stdin.buffer,sys.stdout.buffer)


if __name__=="__main__":
    main()
