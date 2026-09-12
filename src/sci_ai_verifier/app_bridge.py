"""Explicit operator-approved read-only app adapters with bounded JSON stdio."""

import os
import re
import tempfile
from pathlib import Path

from .claude_runner import run_process
from .common import Fault,canonical,digest
from .local_candidates import safe_payload
from .mcp import parse_json
from .storage import no_links


def call_adapter(settings,name,request,*,cwd,timeout=30,log=None,process=None):
    tool=settings["external_tools"].get(name)
    if tool is None:
        raise Fault("app_not_authorized","Select an operator-configured app adapter.")
    executable=no_links(tool["executable"])
    if (executable.suffix.lower() in {".cmd",".bat",".ps1",".py",".sh"}
            or re.fullmatch(r"(?:cmd|powershell|pwsh|sh|bash|dash|zsh|fish|wscript|cscript|node|perl|ruby|python[0-9.]*)",executable.stem.lower())
            or executable.stat().st_size>256*1024*1024 or digest(executable.read_bytes())!=tool["sha256"]):
        raise Fault("app_changed","The app adapter no longer matches its reviewed executable digest.")
    if not isinstance(request,dict) or len(canonical(request))>65536:
        raise Fault("app_input_invalid","App adapters accept bounded JSON objects only.")
    safe_payload(request)
    env={key:value for key,value in os.environ.items() if key.upper() in {"SYSTEMROOT","WINDIR","PATH","TEMP","TMP"}}
    for key in tool["credential_env"]:
        if not os.environ.get(key):
            raise Fault("app_authentication_required","A configured app credential is missing from the environment.")
        env[key]=os.environ[key]
    if log:
        log.emit("app_started",app=name,executable_sha256=tool["sha256"],request=request)
    try:
        # Never make submitted files the working directory of a trusted host app:
        # loaders may otherwise discover an untrusted DLL/module/configuration.
        with tempfile.TemporaryDirectory(prefix="sci-verifier-app-") as temporary:
            code,out,_=(process or run_process)([str(executable),*tool["arguments"]],cwd=temporary,env=env,
                                               prompt=canonical(request).decode(),timeout=timeout,max_bytes=262144)
        if code:
            raise Fault("app_failed","The app adapter did not return a successful result.")
        if any(env[key].encode() in out for key in tool["credential_env"]):
            raise Fault("secret_material","Credential material was rejected in an app response.")
        result=parse_json(out)
        if not isinstance(result,dict):
            raise ValueError()
        safe_payload(result)
        if log:
            log.emit("app_finished",app=name,response=result,response_sha256=digest(out))
        return {"app":name,"response":result,"response_sha256":digest(out),"adapter_sha256":tool["sha256"]}
    except (ValueError,UnicodeError,RecursionError):
        raise Fault("app_response_invalid","The app adapter must return a bounded JSON object.") from None
    except BaseException as error:
        if log:
            log.emit("app_failed",app=name,code=getattr(error,"code",type(error).__name__))
        raise
