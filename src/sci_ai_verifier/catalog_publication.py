"""Opt-in GitHub draft proposals; durable retries never rerun scientific work."""

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from .common import Fault,canonical,digest,utc_now
from .claude_runner import run_process
from .local_catalog import MAX_BUNDLE
from .mcp import parse_json
from .storage import atomic_write,no_links


def publish(bundle_path,repository,*,approved=False,process=None):
    if not approved:
        raise Fault("publication_authorization_required","Review the exact exported file and explicitly approve publication before submitting.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repository):
        raise Fault("repository_invalid","Specify the intended GitHub owner/repository.")
    path=no_links(bundle_path)
    if path.stat().st_size>MAX_BUNDLE:
        raise Fault("catalog_rejected","Candidate bundle exceeds its byte limit.")
    raw=path.read_bytes()
    bundle=parse_json(raw)
    release=isinstance(bundle,dict) and bundle.get("kind")=="local-catalog-release"
    if release:
        from .catalog_release import validate
        validate(raw)
    elif not isinstance(bundle,dict) or bundle.get("kind")!="local-candidate-bundle" or not isinstance(bundle.get("authorization"),str) or len(bundle["authorization"])<20:
        raise Fault("catalog_invalid","Publish a reviewed, explicitly authorized candidate export.")
    key=digest(raw)
    state_path=path.with_name(path.name+".publication.json")
    state=parse_json(no_links(state_path).read_bytes()) if state_path.exists() else {"bundle_sha256":key,"repository":repository,"created_at":utc_now()}
    if state["bundle_sha256"]!=key or state["repository"]!=repository:
        raise Fault("publication_changed","The approved bundle or repository changed; prepare a separate proposal.")
    if state.get("pull_request_url"):
        return state
    gh=shutil.which("gh")
    if not gh or Path(gh).suffix.lower() in {".cmd",".bat",".ps1"}:
        raise Fault("github_cli_unavailable","Install and sign in to the native GitHub CLI before opt-in publication.")
    env={key:value for key,value in os.environ.items() if key.upper() in {"PATH","SYSTEMROOT","WINDIR","APPDATA","LOCALAPPDATA","USERPROFILE","HOME","TEMP","TMP","GH_TOKEN","GITHUB_TOKEN"}}
    env["GH_PROMPT_DISABLED"]="1"
    def api(endpoint,body=None,method=None):
        command=[gh,"api","--hostname","github.com","repos/"+repository+"/"+endpoint]
        if body is not None:
            command += ["--method",method or "POST","--input","-"]
        code,out,_=(process or run_process)(command,cwd=path.parent,env=env,prompt=canonical(body).decode() if body is not None else "",timeout=45,max_bytes=2*1024*1024)
        if code:
            raise Fault("publication_unavailable","GitHub publication failed. The prepared bundle and completed stages are retained; retry this file only.")
        return parse_json(out)
    def save():
        atomic_write(state_path,canonical(state))
    branch=("codex/local-release-" if release else "codex/local-candidate-")+key[:20]
    owner=repository.split("/")[0]
    # A successful remote write with a lost response is reconciled before another write.
    pulls=api("pulls?state=all&head="+owner+":"+branch)
    if pulls:
        state["pull_request_url"]=pulls[0]["html_url"]
        save()
        return state
    if "commit" not in state:
        ref=api("git/ref/heads/main")
        base=ref["object"]["sha"]
        commit=api("git/commits/"+base)
        tree=api("git/trees",{"base_tree":commit["tree"]["sha"],"tree":[{"path":("catalog/releases/" if release else "catalog/proposals/")+key+".json","mode":"100644","type":"blob","content":raw.decode("utf-8")}]})
        state["commit"]=api("git/commits",{"message":"Propose local evaluator bundle "+key[:12],"tree":tree["sha"],"parents":[base]})["sha"]
        save()
    if not state.get("branch_created"):
        # Matching-refs returns an empty list when a branch does not exist.
        refs=api("git/matching-refs/heads/"+branch)
        exact=next((item for item in refs if item["ref"]=="refs/heads/"+branch),None)
        if exact and exact["object"]["sha"]!=state["commit"]:
            raise Fault("publication_conflict","The proposed branch already points elsewhere; no branch was overwritten.")
        if not exact:
            api("git/refs",{"ref":"refs/heads/"+branch,"sha":state["commit"]})
        state["branch_created"]=True
        save()
    body=("Proposes the exact candidate bundle `"+key+"` for independent review.\n\n"
          "The export contains candidate specifications and explicitly authorized reference assets. "
          "It excludes subject runs, workflow logs and operator scientific approvals. "
          "Mechanical qualification does not grant scientific approval.\n\n"
          "Review applicability, independence, controls, coverage, uncertainty and redistribution before promotion or release.")
    if release:
        body=("Proposes reviewed local catalog `"+bundle["catalog_id"]+"` version `"+bundle["version"]+"`, exact SHA256 `"+key+"`.\n\n"
              "Inspect every independent review, retirement decision, redistribution assessment, runtime range and predecessor pin. "
              "Catalog membership does not confer scientific grades. Merging makes these exact release bytes available for opt-in retrieval.")
    result=api("pulls",{"title":("Review local catalog release " if release else "Review local evaluator bundle ")+key[:12],"head":branch,"base":"main","draft":True,"body":body})
    state["pull_request_url"]=result["html_url"]
    save()
    return state
