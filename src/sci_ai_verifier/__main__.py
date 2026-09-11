"""Local launch/diagnostics; this CLI never invokes a model."""

import argparse
import sys
from pathlib import Path

from .agent import ConfigurationError, Runtime
from .common import Fault, canonical
from .mcp import parse_json, serve


def main():
    parser = argparse.ArgumentParser(description="Scientific Verifier desktop MCP server")
    parser.add_argument("command", choices=("serve", "request"))
    parser.add_argument("--workspace", type=Path, required=True,
                        help="Writable data directory; artifacts go in its .verifier subdirectory")
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Operator-authorized submission directory")
    parser.add_argument("--profile", choices=("stage2", "stage3", "verification", "demo"), default="demo")
    parser.add_argument("--catalog", type=Path, help="Operator-selected local release directory for testing")
    parser.add_argument("--subject-fixture", type=Path,
                        help="Explicit synthetic replay file; never invokes a live subject or API")
    parser.add_argument("--instructions", type=Path,
                        default=Path(__file__).resolve().parents[2] / "skills" / "scientific-verifier")
    args = parser.parse_args()
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
