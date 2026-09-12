"""Personal local verification plus explicit historical MCP profiles."""

import argparse
import sys
from pathlib import Path

from .agent import ConfigurationError, Runtime
from .common import Fault, canonical
from .mcp import parse_json, serve


def main():
    parser = argparse.ArgumentParser(description="Scientific Verifier desktop MCP server")
    parser.add_argument("command", choices=("verify", "serve-local", "doctor", "serve", "request"))
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--workspace", type=Path, default=Path.cwd(),
                        help="Writable data directory; artifacts go in its .verifier subdirectory")
    parser.add_argument("--source-root", type=Path,
                        help="Operator-authorized submission directory")
    parser.add_argument("--profile", choices=("stage2", "stage3", "verification", "demo"), default="verification")
    parser.add_argument("--model", default="opus")
    parser.add_argument("--auth", choices=("subscription", "api"), default="subscription")
    parser.add_argument("--claude-executable", default="claude")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--config",type=Path,help="Operator settings JSON for container, trials and permitted tools")
    parser.add_argument("--catalog", type=Path, help="Operator-selected local release directory for testing")
    parser.add_argument("--subject-fixture", type=Path,
                        help="Explicit synthetic replay file; never invokes a live subject or API")
    parser.add_argument("--instructions", type=Path,
                        default=Path(__file__).resolve().parents[2] / "skills" / "scientific-verifier")
    args = parser.parse_args()
    if args.command in {"verify", "serve-local", "doctor"}:
        from .local_entry import PublicRuntime
        from .claude_runner import ClaudeCode
        if not 1 <= args.timeout <= 7200:
            parser.error("Timeout must be between 1 and 7200 seconds.")
        public = PublicRuntime(workspace=args.workspace, instructions=args.instructions, model=args.model,
                               auth=args.auth, executable=args.claude_executable, timeout=args.timeout,config_path=args.config)
        if args.command == "serve-local":
            serve(public, sys.stdin.buffer, sys.stdout.buffer)
            return
        if args.command == "verify":
            if args.source is None:
                parser.error("verify needs a skill directory or SKILL.md path.")
            result = public.call("verify_skill", {"source_path": str(args.source.resolve())})
        else:
            try:
                from .local_config import load_configuration
                settings=load_configuration(args.config)
                data=ClaudeCode(executable=args.claude_executable, model=args.model, auth=args.auth,settings=settings).preflight()
                if settings["sandbox_image"]:
                    from .sandbox import DockerSandbox
                    data["sandbox"]=DockerSandbox(args.workspace,settings).preflight()
                result = {"status": "ok", "data":data}
            except Fault as error:
                result = {"status": "unavailable", "error": {"code": error.code, "message": str(error)}}
        sys.stdout.buffer.write(canonical(result) + b"\n")
        raise SystemExit(0 if result["status"] == "ok" else 2)
    if args.source_root is None:
        parser.error("Historical serve/request commands require --source-root.")
    try:
        subject = None
        if args.subject_fixture:
            from .fixtures import ReplaySubject
            subject = ReplaySubject(args.subject_fixture)
        runtime = Runtime(args.workspace, args.source_root, args.instructions,
                          profile=args.profile, release_directory=args.catalog, subject_adapter=subject)
    except (ConfigurationError, Fault, OSError) as error:
        # One actionable line: the app shows a start failure without a Python traceback.
        sys.stderr.write(f"scientific-verifier cannot start. {error}\n")
        raise SystemExit(2) from None
    if args.command == "serve":
        serve(runtime, sys.stdin.buffer, sys.stdout.buffer)
    else:
        raw = sys.stdin.buffer.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            parser.error("Request exceeds 1 MiB.")
        request = parse_json(raw)
        response = runtime.call(request["name"], request.get("arguments", {}), "scripted-request")
        sys.stdout.buffer.write(canonical(response) + b"\n")


if __name__ == "__main__":
    main()
