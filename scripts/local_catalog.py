"""Operator catalog maintenance, separate from the one-action verification tool."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault,canonical,digest
from sci_ai_verifier.local_catalog import export_bundle,import_bundle,MAX_BUNDLE
from sci_ai_verifier.local_candidates import candidates
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.storage import Store,atomic_write,no_links


def main():
    parser=argparse.ArgumentParser(description="Prepare, inspect, import and explicitly propose local evaluator bundles")
    parser.add_argument("command",choices=("list","export","import","release","publish"))
    parser.add_argument("--workspace",type=Path,default=Path.cwd())
    parser.add_argument("--config",type=Path)
    parser.add_argument("--file",type=Path)
    parser.add_argument("--candidate",action="append")
    parser.add_argument("--authorization",help="Explicit permission to redistribute every selected reference")
    parser.add_argument("--sha256",help="Expected exact imported/exported bundle digest")
    parser.add_argument("--repository")
    parser.add_argument("--approve-publication",action="store_true")
    parser.add_argument("--approve-promotion",action="store_true")
    parser.add_argument("--reviews",type=Path,help="JSON list of independent catalog review records")
    parser.add_argument("--output",type=Path,help="New release file to create")
    parser.add_argument("--previous",type=Path,help="Previous exact release for a versioned update")
    parser.add_argument("--previous-sha256")
    parser.add_argument("--catalog-id")
    parser.add_argument("--version")
    parser.add_argument("--minimum-runtime",default="0.7.0")
    parser.add_argument("--maximum-runtime-exclusive",default="0.8.0")
    args=parser.parse_args()
    try:
        settings=load_configuration(args.config)
        store=Store(args.workspace)
        if args.command=="list":
            result={"candidates":candidates(store)}
        elif args.command=="export":
            if not args.file or not args.candidate or not args.authorization:
                parser.error("export needs --file, --candidate and --authorization")
            if no_links(args.file).exists():
                raise Fault("export_exists","Choose a new output file; an existing reviewed bundle is never overwritten.")
            raw=export_bundle(store,args.candidate,authorization=args.authorization)
            atomic_write(args.file,raw)
            result={"file":str(args.file.resolve()),"sha256":digest(raw),"bytes":len(raw),"published":False}
        else:
            if not args.file or not args.sha256:
                parser.error("import/release/publish needs --file and its exact --sha256")
            file=no_links(args.file)
            if file.stat().st_size>MAX_BUNDLE:
                raise Fault("catalog_rejected","Bundle exceeds its byte limit.")
            raw=file.read_bytes()
            if digest(raw)!=args.sha256:
                raise Fault("catalog_changed","The file differs from the reviewed digest.")
            from sci_ai_verifier.mcp import parse_json
            from sci_ai_verifier.catalog_release import install,build
            payload=parse_json(raw)
            if args.command=="release":
                if not args.output or not args.reviews or not args.catalog_id or not args.version:
                    parser.error("release needs --output, --reviews, --catalog-id and --version")
                if no_links(args.output).exists():
                    raise Fault("export_exists","Choose a new release file; existing releases are never overwritten.")
                review_file=no_links(args.reviews)
                if review_file.stat().st_size>MAX_BUNDLE:
                    raise Fault("catalog_rejected","Review records exceed their size limit.")
                previous=None
                if args.previous:
                    old=no_links(args.previous)
                    if old.stat().st_size>MAX_BUNDLE:
                        raise Fault("catalog_rejected","Previous release exceeds its size limit.")
                    previous=old.read_bytes()
                    if digest(previous)!=args.previous_sha256:
                        raise Fault("catalog_changed","An update requires the exact previous release SHA256.")
                import tempfile
                with tempfile.TemporaryDirectory(prefix="sci-verifier-release-check-") as temporary:
                    release=build(Store(temporary),raw,settings,
                        {"catalog_id":args.catalog_id,"version":args.version,"minimum_runtime":args.minimum_runtime,
                         "maximum_runtime_exclusive":args.maximum_runtime_exclusive},parse_json(review_file.read_bytes()),
                         approved=args.approve_promotion,previous_raw=previous)
                atomic_write(args.output,release)
                result={"file":str(args.output.resolve()),"sha256":digest(release),"bytes":len(release),"published":False}
            elif args.command=="import":
                result=(install(store,raw,settings) if isinstance(payload,dict) and payload.get("kind")=="local-catalog-release"
                        else import_bundle(store,raw,settings))
                result["note"]="Configure the exact release under catalogs to apply its retirement inventory to new runs. Import alone installs candidate bytes."
            else:
                if not args.repository:
                    parser.error("publish needs --repository owner/name")
                # Revalidate in disposable storage; publication never changes live candidates.
                import tempfile
                with tempfile.TemporaryDirectory(prefix="sci-verifier-catalog-check-") as temporary:
                    if isinstance(payload,dict) and payload.get("kind")=="local-catalog-release":
                        install(Store(temporary),raw,settings)
                    else:
                        import_bundle(Store(temporary),raw,settings)
                from sci_ai_verifier.catalog_publication import publish
                result=publish(file,args.repository,approved=args.approve_publication)
        print(canonical({"status":"ok","data":result}).decode())
    except (Fault,OSError,ValueError) as error:
        print(canonical({"status":"unavailable","error":{"code":getattr(error,"code","catalog_unavailable"),"message":str(error)}}).decode())
        raise SystemExit(2) from None


if __name__=="__main__":
    main()
