"""Private child-process entry point. Not a public user workflow."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.claude_runner import ClaudeCode
from sci_ai_verifier.local_entry import BoundRuntime
from sci_ai_verifier.mcp import serve
from sci_ai_verifier.runlog import WorkflowLog


def main():
    parser = argparse.ArgumentParser()
    for name in ("workspace", "source-root", "instructions", "run-id", "model", "auth", "claude-executable"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--attempt-id")
    parser.add_argument("--config")
    args = parser.parse_args()
    log = WorkflowLog(args.workspace, attempt_id=args.attempt_id) if args.attempt_id else None
    from sci_ai_verifier.local_config import load_configuration
    subject = ClaudeCode(executable=args.claude_executable, model=args.model, auth=args.auth, log=log,settings=load_configuration(args.config))
    runtime = Runtime(args.workspace, args.source_root, args.instructions, profile="local", subject_adapter=subject)
    serve(BoundRuntime(runtime, args.run_id, log), sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    main()
