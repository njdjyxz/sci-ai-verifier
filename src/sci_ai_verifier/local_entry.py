"""One public action backed by Claude Code's own planner/MCP loop."""

import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from .agent import Runtime
from .claude_runner import ClaudeCode, prepare_workspace, isolated_environment, parse_events
from .common import Fault, canonical
from .local import OPERATIONS
from .local_candidates import safe_payload
from .storage import atomic_write, no_links
from .tools import DEFINITIONS, obj, string

INTERNAL_NAMES = {"get_verifier_context", "load_submitted_skill", "read_snapshot_file", "commit_claim_manifest",
                  "write_report_card", *OPERATIONS}


class BoundRuntime:
    """The planner's server can act only on the one operator-created run."""
    instructions = "Get the pinned context for your supplied run ID, then complete the local verification workflow."
    definitions = [item for item in DEFINITIONS if item["name"] in INTERNAL_NAMES]

    def __init__(self, runtime, run_id):
        self.runtime, self.run_id = runtime, run_id

    def call(self, name, arguments, call_id=None):
        if name not in INTERNAL_NAMES or arguments.get("run_id") != self.run_id:
            return {"status": "retryable", "error": {"code": "bound_run_required", "message": "Use the supplied run and internal tools only."}}
        return self.runtime.call(name, arguments, call_id)


def verify(source_path, *, workspace, instructions, model="opus", auth="subscription", executable="claude", timeout=1800):
    source = no_links(source_path)
    if not source.exists():
        raise Fault("source_missing", "Select an existing skill directory or SKILL.md file.")
    adapter = ClaudeCode(executable=executable, model=model, auth=auth)
    preflight = adapter.preflight()
    runtime = Runtime(workspace, source if source.is_dir() else source.parent, instructions,
                      profile="local", subject_adapter=adapter)
    created = runtime.call("start_verifier_run", {"source_path": str(source)})
    if created["status"] != "ok":
        return created
    run_id = created["data"]["run_id"]
    session = str(uuid4())
    try:
        with tempfile.TemporaryDirectory(prefix="sci-verifier-controller-") as temporary:
            directory = no_links(Path(temporary) / "workspace")
            prepare_workspace(directory)
            env = isolated_environment(Path(temporary) / "config", auth)
            # Auth is inherited through the process environment, never this on-disk config.
            entry = Path(__file__).with_name("internal_server.py")
            arguments = [str(entry), "--workspace", str(Path(workspace).resolve()), "--source-root", str(runtime.source_root),
                         "--instructions", str(Path(instructions).resolve()), "--run-id", run_id,
                         "--model", model, "--auth", auth, "--claude-executable", adapter.executable]
            mcp = directory / "mcp.json"
            atomic_write(mcp, canonical({"mcpServers": {"verifier_internal": {"command": sys.executable, "args": arguments}}}))
            code, raw, _ = adapter.process(adapter.command(directory, session, mcp=mcp, controller=True),
                cwd=directory, env=env, timeout=timeout, max_bytes=8*1024*1024,
                prompt="Verify the skill for run " + run_id + ". First call get_verifier_context. Read all submitted text files before extracting scientific claims. Lookup existing local candidates for each claim. If insufficient, discover primary reference sources with WebSearch, fetch exact URLs with fetch_local_reference, qualify source-backed cases, select, execute, and report. Do not invent cases' expected answers or scientific grades. Unsupported capabilities must be recorded with record_local_limitation; continue the other claims. Finish with write_report_card.")
            if code:
                raise Fault("planner_incomplete", "The Claude Code planner stopped before successful completion.")
            receipt = parse_events(raw, expected_session=session)
            # Save identity and accounting only; the journal already records tool arguments/results.
            receipt = {key: receipt[key] for key in ("response_id", "observed_model_ids", "usage", "total_cost_usd")}
            safe_payload(receipt)
            atomic_write(runtime.store.run_dir(run_id) / "controller-receipt.json", canonical({**receipt, "preflight": preflight}))
        state, _ = runtime.store.read(run_id)
        if state["run_state"] != "completed":
            raise Fault("planner_incomplete", "The planner ended without a completed immutable report.")
        return {"status": "ok", "data": {"run_id": run_id, "verification_complete": True,
                "report": runtime.store.get_json(state["report_ref"]),
                "report_json_path": str(runtime.store.run_dir(run_id) / "report-card.json"),
                "report_markdown_path": str(runtime.store.run_dir(run_id) / "report-card.md")}}
    except (Fault, OSError, KeyboardInterrupt) as error:
        # A completed report survives a lost final planner response. No subject is rerun.
        recovered = runtime.call("get_verifier_context", {"run_id": run_id})
        if recovered["status"] == "ok" and recovered["data"]["verification_complete"]:
            return {"status": "ok", "data": {"run_id": run_id, "verification_complete": True,
                    "report": recovered["data"]["report"], "controller_receipt": "unavailable",
                    "report_json_path": str(runtime.store.run_dir(run_id) / "report-card.json"),
                    "report_markdown_path": str(runtime.store.run_dir(run_id) / "report-card.md")}}
        runtime.call("cancel_verifier_run", {"run_id": run_id})
        return {"status": "incomplete", "error": {"code": error.code if isinstance(error, Fault) else "interrupted",
                "message": "Local verification stopped. Saved evidence is retained; no uncertain trial was replayed.",
                "run_id": run_id, "run_directory": str(runtime.store.run_dir(run_id)), "verification_complete": False}}


class PublicRuntime:
    instructions = "Call verify_skill once for the user's selected skill path. It returns the completed report or an honest operational limitation."
    definitions = [{"name": "verify_skill", "description": "Verify a local text skill in fresh Claude Code sessions and return its traceable report.",
                    "inputSchema": obj({"source_path": string(4096)}),
                    "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}}]

    def __init__(self, **configuration):
        self.configuration = configuration

    def call(self, name, arguments, call_id=None):
        from .common import validate
        try:
            if name != "verify_skill":
                raise Fault("unknown_tool", "The public local interface exposes verify_skill only.")
            validate(arguments, self.definitions[0]["inputSchema"])
            return verify(arguments["source_path"], **self.configuration)
        except (Fault, OSError) as error:
            return {"status": "unavailable", "error": {"code": error.code if isinstance(error, Fault) else "configuration_unavailable",
                    "message": str(error) if isinstance(error, Fault) else "Local configuration is unavailable.", "verification_complete": False}}
