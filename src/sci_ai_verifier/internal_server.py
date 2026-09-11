"""Private child-process entry point. Not a public user workflow."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.claude_runner import ClaudeCode
from sci_ai_verifier.local_entry import BoundRuntime
from sci_ai_verifier.mcp import serve


def main():
    parser = argparse.ArgumentParser()
    for name in ("workspace", "source-root", "instructions", "run-id", "model", "auth", "claude-executable"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    subject = ClaudeCode(executable=args.claude_executable, model=args.model, auth=args.auth)
    runtime = Runtime(args.workspace, args.source_root, args.instructions, profile="local", subject_adapter=subject)
    serve(BoundRuntime(runtime, args.run_id), sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    main()
