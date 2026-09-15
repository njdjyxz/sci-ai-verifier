"""Catalog maintenance, separate from the one-action verification tool.

The order is: prepare and check locally, open a draft pull request, read the review,
push a revision. A person reviews on the pull request and accepts by merging it.
"""

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault,canonical,digest
from sci_ai_verifier.local_catalog import export_bundle,import_bundle,MAX_BUNDLE
from sci_ai_verifier.local_candidates import candidates
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.mcp import parse_json
from sci_ai_verifier.storage import Store,atomic_write,no_links


def read_pinned(path,expected,*,label):
    file=no_links(path)
    if file.stat().st_size>MAX_BUNDLE:
        raise Fault("catalog_rejected",label+" exceeds its byte limit.")
    raw=file.read_bytes()
    if digest(raw)!=expected:
        raise Fault("catalog_changed",label+" differs from the digest you named.")
    return file,raw


def parser():
    parsed=argparse.ArgumentParser(description="Prepare, inspect, propose and revise local evaluator bundles")
    parsed.add_argument("command",choices=("list","export","import","release","publish","review"))
    parsed.add_argument("--workspace",type=Path,default=Path.cwd())
    parsed.add_argument("--config",type=Path)
    parsed.add_argument("--file",type=Path)
    parsed.add_argument("--candidate",action="append")
    parsed.add_argument("--redistribution",help="Licence, source and redistribution assessment for every selected reference")
    parsed.add_argument("--sha256",help="Expected exact imported/exported bundle digest")
    parsed.add_argument("--repository")
    parsed.add_argument("--assessments",type=Path,help="JSON list of prepared per-candidate assessments")
    parsed.add_argument("--output",type=Path,help="New release file to create")
    parsed.add_argument("--previous",type=Path,help="Previous exact release for a versioned update")
    parsed.add_argument("--previous-sha256")
    parsed.add_argument("--catalog-id")
    parsed.add_argument("--version")
    parsed.add_argument("--minimum-runtime",default="0.7.0")
    parsed.add_argument("--maximum-runtime-exclusive",default="0.8.0")
    return parsed


def run(args,parsed):
    settings=load_configuration(args.config)
    store=Store(args.workspace)
    if args.command=="list":
        return {"candidates":candidates(store)}
    if args.command=="export":
        if not args.file or not args.candidate or not args.redistribution:
            parsed.error("export needs --file, --candidate and --redistribution")
        if no_links(args.file).exists():
            raise Fault("export_exists","Choose a new output file; a prepared bundle is never overwritten.")
        raw=export_bundle(store,args.candidate,redistribution=args.redistribution)
        atomic_write(args.file,raw)
        return {"file":str(args.file.resolve()),"sha256":digest(raw),"bytes":len(raw),"published":False,
                "next_step":"Publish it to open a draft pull request for review."}
    if not args.file or not args.sha256:
        parsed.error(args.command+" needs --file and its exact --sha256")
    file,raw=read_pinned(args.file,args.sha256,label="That file")
    payload=parse_json(raw)
    release=isinstance(payload,dict) and payload.get("kind")=="local-catalog-release"
    from sci_ai_verifier.catalog_release import build,install
    if args.command=="release":
        if not args.output or not args.assessments or not args.catalog_id or not args.version:
            parsed.error("release needs --output, --assessments, --catalog-id and --version")
        if no_links(args.output).exists():
            raise Fault("export_exists","Choose a new release file; existing releases are never overwritten.")
        assessments=no_links(args.assessments)
        if assessments.stat().st_size>MAX_BUNDLE:
            raise Fault("catalog_rejected","Assessment records exceed their size limit.")
        previous=None
        if args.previous:
            previous=read_pinned(args.previous,args.previous_sha256,label="The previous release")[1]
        # Requalify in disposable storage; preparing a release never changes live candidates.
        with tempfile.TemporaryDirectory(prefix="sci-verifier-release-check-") as temporary:
            prepared=build(Store(temporary),raw,settings,
                           {"catalog_id":args.catalog_id,"version":args.version,
                            "minimum_runtime":args.minimum_runtime,
                            "maximum_runtime_exclusive":args.maximum_runtime_exclusive},
                           parse_json(assessments.read_bytes()),previous_raw=previous)
        atomic_write(args.output,prepared)
        return {"file":str(args.output.resolve()),"sha256":digest(prepared),"bytes":len(prepared),"published":False,
                "next_step":"Publish it to open a draft pull request for review."}
    if args.command=="import":
        result=install(store,raw,settings) if release else import_bundle(store,raw,settings)
        result["note"]=("Configure the exact release under catalogs to apply its retirement inventory to "
                        "new runs. Import alone installs candidate bytes.")
        return result
    if not args.repository:
        parsed.error(args.command+" needs --repository owner/name")
    if args.command=="review":
        from sci_ai_verifier.catalog_publication import review
        return review(file,args.repository)
    # Revalidate in disposable storage; publication never changes live candidates.
    with tempfile.TemporaryDirectory(prefix="sci-verifier-catalog-check-") as temporary:
        checked=Store(temporary)
        install(checked,raw,settings) if release else import_bundle(checked,raw,settings)
    from sci_ai_verifier.catalog_publication import publish
    return publish(file,args.repository)


def main():
    parsed=parser()
    args=parsed.parse_args()
    try:
        print(canonical({"status":"ok","data":run(args,parsed)}).decode())
    # TypeError and KeyError included: an unexpected remote response shape should be
    # reported as unavailable, not printed as a traceback.
    except (Fault,OSError,ValueError,TypeError,KeyError) as error:
        print(canonical({"status":"unavailable","error":{"code":getattr(error,"code","catalog_unavailable"),
                                                        "message":str(error)}}).decode())
        raise SystemExit(2) from None


if __name__=="__main__":
    main()
