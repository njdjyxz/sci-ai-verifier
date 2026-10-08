"""Disposable local Linux containers; no host shell, credentials, or answer mounts."""

import base64
import json
import os
import re
import shutil
import time
import tempfile
from pathlib import Path
from uuid import uuid4

from .claude_runner import run_process
from .common import Fault, canonical, digest
from .ingest import SECRET_BYTES, valid_relative
from .storage import no_links,atomic_write

COLLECT = r'''
import os,stat,json,base64
root='/work'
limits=json.loads(__import__('sys').argv[1])
keep=limits['keep']
paths=[]
for folder,dirs,names in os.walk(root,followlinks=False):
    dirs[:]=[name for name in dirs if not os.path.islink(os.path.join(folder,name)) and name not in {'__pycache__','.cache'}]
    for name in sorted(names):
        path=os.path.join(folder,name)
        if stat.S_ISREG(os.lstat(path).st_mode): paths.append(os.path.relpath(path,root))
paths.sort(key=lambda path:path!=keep)
files=[]; left=[]; total=0
for relative in paths:
    path=os.path.join(root,relative)
    size=os.lstat(path).st_size
    raw=None
    if size<=limits['max_file_bytes']:
        with open(path,'rb',opener=lambda p,f:os.open(p,f|os.O_NOFOLLOW)) as handle:
            raw=handle.read(limits['max_file_bytes']+1)
    if raw is None or len(raw)>limits['max_file_bytes'] or total+len(raw)>limits['max_artifact_bytes'] or len(files)>=limits['max_artifacts']:
        if keep is None or relative==keep: raise ValueError('artifact limit')
        left.append({'path':relative,'bytes':size}); continue
    total+=len(raw)
    files.append({'path':relative,'base64':base64.b64encode(raw).decode()})
print(json.dumps({'files':files,'not_kept':left}))
'''


def local_endpoint(value):
    return isinstance(value,str) and bool(re.fullmatch(r"npipe:/+(?:\.|localhost)/pipe/[A-Za-z0-9_.-]+",value) or value.startswith("unix:///"))


# Where a task's input files appear, read-only, in every container that works on the task
# ("Tasks" in local-tasks.md).
TASK_ROOT = "/task"
# How many files left behind a trial records by name.
MAX_NOT_KEPT = 20


class DockerSandbox:
    def __init__(self, source, settings, *, timeout=120, log=None, process=None, inputs=None):
        self.source, self.settings = no_links(source), settings
        # A task's input files, by plain name: mounted read-only at TASK_ROOT, never copied into /work.
        self.inputs = dict(inputs or {})
        self.timeout, self.log, self.process = timeout, log, process or run_process
        self.name = "sci-verifier-"+uuid4().hex
        self.docker, self.endpoint, self.image = None, None, None
        self.created, self.deadline = False, None
        self.staging=None
        allowed = {"SYSTEMROOT","WINDIR","PATH","PATHEXT","COMSPEC","TEMP","TMP",
                   "USERPROFILE","HOME","APPDATA","LOCALAPPDATA","PROGRAMFILES"}
        self.env = {key:value for key,value in os.environ.items() if key.upper() in allowed}

    def invoke(self, args, *, timeout=15, prompt="", max_bytes=1024*1024, endpoint=True, capture_output=True):
        command = [self.docker]
        if endpoint and self.endpoint:
            command += ["--host",self.endpoint]
        command += args
        code,out,err = self.process(command,cwd=self.source,env=self.env,prompt=prompt,
                                   timeout=timeout,max_bytes=max_bytes)
        if self.log:
            self.log.emit("sandbox_command", container=self.name, operation=args[:2], exit_code=code,
                          stdout=out.decode("utf-8",errors="replace") if capture_output else {"bytes":len(out)},
                          stderr=err.decode("utf-8",errors="replace") if capture_output else {"bytes":len(err)})
        return code,out,err

    def preflight(self):
        image = self.settings.get("sandbox_image")
        if not image:
            raise Fault("sandbox_configuration_required", "Configure a pinned local container image to run computational skills.")
        self.docker = shutil.which(self.settings["docker_executable"])
        if not self.docker or Path(self.docker).suffix.lower() in {".cmd",".bat",".ps1"}:
            raise Fault("sandbox_unavailable", "Install and start Docker Desktop with Linux containers.")
        code,out,_ = self.invoke(["context","inspect","--format","{{json .Endpoints.docker.Host}}"],endpoint=False)
        try:
            self.endpoint=json.loads(out)
        except (ValueError,UnicodeError):
            self.endpoint=None
        if code or not local_endpoint(self.endpoint):
            raise Fault("sandbox_remote_forbidden", "Use a local Docker engine through a named pipe or Unix socket.")
        code,out,_=self.invoke(["image","inspect",image],capture_output=False)
        try:
            info=json.loads(out)[0]
            self.image=info["Id"]
            valid=info["Os"]=="linux" and re.fullmatch(r"sha256:[0-9a-f]{64}",self.image)
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError):
            valid=False
        if code or not valid:
            raise Fault("sandbox_image_unavailable", "Prepare the pinned Linux image before verification.")
        return {"engine_endpoint":self.endpoint,"image_id":self.image,"network":"none"}

    def __enter__(self):
        self.preflight()
        # A private outer directory protects host data; the mounted inner tree
        # has portable read permissions for the unprivileged container user.
        # Original submitted files and their permissions are never changed.
        self.staging=tempfile.TemporaryDirectory(prefix="sci-verifier-container-")
        original=self.source
        self.source=Path(self.staging.name)/"files"
        self.source.mkdir(mode=0o755)
        count,total=0,0
        try:
            for file in sorted(original.rglob("*")):
                no_links(file)
                if file.is_dir():
                    continue
                if not file.is_file() or file.stat().st_size>self.settings["max_file_bytes"]:
                    raise Fault("sandbox_source_invalid","Container source has a special or oversized file.")
                raw=file.read_bytes()
                count+=1
                total+=len(raw)
                if count>self.settings["max_artifacts"]+1 or total>self.settings["max_artifact_bytes"]:
                    raise Fault("sandbox_source_limit","Container source exceeds its configured limits.")
                target=self.source/file.relative_to(original)
                atomic_write(target,raw)
                target.chmod(0o644)
            for directory in self.source.rglob("*"):
                if directory.is_dir():
                    directory.chmod(0o755)
        except BaseException:
            self.staging.cleanup()
            self.staging=None
            raise
        mounts=["--mount",f"type=bind,source={self.source},target=/submission,readonly"]
        if self.inputs:
            task=Path(self.staging.name)/"task"
            task.mkdir(mode=0o755)
            try:
                for name,raw in sorted(self.inputs.items()):
                    if not valid_relative(name) or "/" in name or not isinstance(raw,bytes):
                        raise Fault("sandbox_source_invalid","Task input files need plain names and bytes.")
                    atomic_write(task/name,raw)
                    (task/name).chmod(0o644)
            except BaseException:
                self.staging.cleanup()
                self.staging=None
                raise
            mounts+=["--mount",f"type=bind,source={task},target={TASK_ROOT},readonly"]
        if "," in self.staging.name:
            self.staging.cleanup()
            self.staging=None
            raise Fault("sandbox_path_invalid", "Use a temporary source path without commas.")
        self.deadline=time.monotonic()+self.timeout
        args=["run","--detach","--rm","--pull","never","--name",self.name,
              "--label","scientific-verifier.managed=true","--init","--network","none",
              "--read-only","--cap-drop","ALL","--security-opt","no-new-privileges:true",
              "--user","65534:65534","--memory",str(self.settings["memory_mib"])+"m",
              "--memory-swap",str(self.settings["memory_mib"])+"m","--cpus",str(self.settings["cpus"]),
              "--pids-limit",str(self.settings["pids_limit"]),
              "--tmpfs",f'/work:rw,nosuid,nodev,size={self.settings["workspace_mib"]}m,mode=1777',
              "--tmpfs","/tmp:rw,nosuid,nodev,size=32m,mode=1777","--workdir","/work",*mounts,
              "--entrypoint","python3",self.image,"-c",f"import time; time.sleep({self.timeout})"]
        # The name is ours even if the client loses the create response. Cleanup uses
        # this unpredictable name only; daemon-side lifetime also bounds orphaned work.
        self.created=True
        try:
            code,_,_=self.invoke(args,timeout=min(30,self.timeout))
            if code:
                raise Fault("sandbox_start_failed", "The controlled execution container could not start.")
            copied=self.command("cp -R /submission/. /work/",timeout=min(15,self.timeout))
            if copied["exit_code"]:
                raise Fault("sandbox_source_unavailable", "The pinned source could not be copied into the trial workspace.")
            return self
        except BaseException:
            self.close()
            raise

    def command(self, command, *, timeout=None, stdin=""):
        if not self.created or self.deadline is None:
            raise Fault("sandbox_not_started", "The execution container is not active.")
        remaining=self.deadline-time.monotonic()
        if remaining<=0:
            raise Fault("sandbox_timeout", "The execution container reached its deadline.")
        if not isinstance(command,str) or len(command)>16000 or not isinstance(stdin,str) or len(stdin)>128*1024:
            raise Fault("sandbox_request_invalid", "Use a bounded command and input.")
        started=time.monotonic()
        code,out,err=self.invoke(["exec","-i",self.name,"/bin/sh","-c",command],
                                timeout=min(remaining,timeout or remaining),prompt=stdin)
        if self.log:
            self.log.emit("subject_command",command=command,exit_code=code,
                          duration_seconds=time.monotonic()-started)
        return {"exit_code":code,"stdout":out.decode("utf-8",errors="replace"),
                "stderr":err.decode("utf-8",errors="replace")}

    def collect(self, *, keep=None):
        """The new files under /work and those left behind, as (files, not_kept).

        Without `keep` every file must fit the limits. With it, `keep` is collected first and must
        fit; any other file past a limit is left in the container and named with its size
        ("Files not kept" in local-tasks.md).
        """
        remaining=self.deadline-time.monotonic()
        if remaining<=0:
            raise Fault("sandbox_timeout", "The execution container reached its deadline.")
        limits={key:self.settings[key] for key in ("max_file_bytes","max_artifacts","max_artifact_bytes")}
        code,out,_=self.invoke(["exec",self.name,"python3","-c",COLLECT,canonical({**limits,"keep":keep}).decode()],
                              timeout=min(15,remaining),max_bytes=self.settings["max_artifact_bytes"]*2+65536,
                              capture_output=False)
        try:
            found=json.loads(out)
            files,left=found["files"],found["not_kept"]
            if (code or not isinstance(files,list) or len(files)>self.settings["max_artifacts"]
                    or not isinstance(left,list) or (left and keep is None)):
                raise ValueError()
            not_kept=[{"path":item["path"],"bytes":item["bytes"]} for item in left[:MAX_NOT_KEPT]
                      if valid_relative(item["path"]) and isinstance(item["bytes"],int) and not isinstance(item["bytes"],bool)]
            if len(not_kept)!=min(len(left),MAX_NOT_KEPT):
                raise ValueError()
            result,total,seen=[],0,set()
            for item in files:
                path=item["path"]
                if not valid_relative(path) or path in seen:
                    raise ValueError()
                raw=base64.b64decode(item["base64"],validate=True)
                total+=len(raw)
                if len(raw)>self.settings["max_file_bytes"] or total>self.settings["max_artifact_bytes"] or SECRET_BYTES.search(raw):
                    raise ValueError()
                seen.add(path)
                result.append({"path":path,"sha256":digest(raw),"bytes":len(raw),"base64":item["base64"]})
            if keep is not None and keep in {item["path"] for item in not_kept}:
                raise ValueError()
            return result,not_kept
        except (ValueError,KeyError,TypeError,UnicodeError):
            raise Fault("sandbox_artifacts_invalid", "Generated artifacts failed path, size or credential checks.") from None

    def close(self):
        try:
            if self.created:
                code,_,_=self.invoke(["rm","--force",self.name],timeout=15)
                if self.log:
                    self.log.emit("sandbox_cleanup",container=self.name,exit_code=code,
                                  lifetime_seconds=self.timeout)
        finally:
            self.created=False
            if self.staging:
                self.staging.cleanup()
                self.staging=None

    def __exit__(self,*args):
        self.close()
