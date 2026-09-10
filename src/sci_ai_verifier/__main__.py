"""Local launch/diagnostics; this CLI never invokes a model."""

import argparse
import sys
from pathlib import Path

from .agent import Runtime
from .common import canonical
from .mcp import parse_json, serve


def main():
    parser = argparse.ArgumentParser(description="Scientific Verifier Stage 2 desktop MCP server")
    parser.add_argument("command", choices=("serve", "request"))
    parser.add_argument("--workspace", type=Path, required=True,
                        help="Writable data directory; artifacts go in its .verifier subdirectory")
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Operator-authorized submission directory")
    parser.add_argument("--instructions", type=Path,
                        default=Path(__file__).resolve().parents[2] / "skills" / "scientific-verifier")
    args = parser.parse_args()
    runtime = Runtime(args.workspace, args.source_root, args.instructions)
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
