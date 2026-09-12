"""One public action backed by Claude Code's own planner/MCP loop."""

import os
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

from .agent import ConfigurationError, Runtime
from .claude_runner import ClaudeCode, prepare_workspace, isolated_environment, parse_events
from .common import Fault, canonical
from .local import OPERATIONS
from .local_candidates import safe_payload
from .storage import atomic_write, no_links
from .tools import DEFINITIONS, obj, string
from .runlog import WorkflowLog, recorded_call

INTERNAL_NAMES = {"get_verifier_context", "load_submitted_skill", "read_snapshot_file", "commit_claim_manifest",
                  "write_report_card", *OPERATIONS}


class BoundRuntime:
    """The planner's server can act only on the one operator-created run."""
    instructions = "Get the pinned context for your supplied run ID, then complete the local verification workflow."
    definitions = [item for item in DEFINITIONS if item["name"] in INTERNAL_NAMES]

    def __init__(self, runtime, run_id, log=None):
        self.runtime, self.run_id, self.log = runtime, run_id, log

    def call(self, name, arguments, call_id=None):
        if name not in INTERNAL_NAMES or arguments.get("run_id") != self.run_id:
            return {"status": "retryable", "error": {"code": "bound_run_required", "message": "Use the supplied run and internal tools only."}}
        return recorded_call(self.log, self.runtime, name, arguments, call_id)


def verify(source_path, *, workspace, instructions, model="opus", auth="subscription", executable="claude", timeout=1800, config_path=None):
    log = WorkflowLog(workspace)
    started = time.monotonic()
    log.emit("verification_started", source_path=str(source_path), model=model, auth_mode=auth)
    try:
        result = _verify(source_path, workspace=workspace, instructions=instructions, model=model,
                         auth=auth, executable=executable, timeout=timeout, log=log,config_path=config_path)
    except (Fault, OSError, ValueError, ConfigurationError, KeyboardInterrupt) as error:
        result = {"status": "unavailable", "error": {
            "code": error.code if isinstance(error, Fault) else "interrupted" if isinstance(error, KeyboardInterrupt) else "configuration_unavailable",
            "message": str(error) if isinstance(error, Fault) else "Local verification could not complete; inspect the workflow log.",
            "verification_complete": False}}
    try:
        log.emit("verification_finished", status=result["status"], error=result.get("error"),
                 duration_seconds=time.monotonic()-started)
    except Fault:
        result["logging_error"] = "workflow_log_unavailable"
    result["log"] = log.paths
    return result


def _verify(source_path, *, workspace, instructions, model, auth, executable, timeout, log, config_path=None):
    from .execution_control import checkpoint
    checkpoint()
    log.emit("setup_started")
    source = no_links(source_path)
    if not source.exists():
        raise Fault("source_missing", "Select an existing skill directory or SKILL.md file.")
    from .local_config import load_configuration
    settings=load_configuration(config_path)
    adapter = ClaudeCode(executable=executable, model=model, auth=auth, log=log,settings=settings)
    preflight = adapter.preflight()
    log.emit("setup_finished", preflight=preflight)
    runtime = Runtime(workspace, source if source.is_dir() else source.parent, instructions,
                      profile="local", subject_adapter=adapter)
    created = recorded_call(log, runtime, "start_verifier_run", {"source_path": str(source)})
    if created["status"] != "ok":
        return created
    run_id = created["data"]["run_id"]
    log.emit("run_bound", run_id=run_id, run_directory=str(runtime.store.run_dir(run_id)))
    atomic_write(runtime.store.run_dir(run_id)/"workflow-log.json", canonical(log.paths))
    session = str(uuid4())
    try:
        with tempfile.TemporaryDirectory(prefix="sci-verifier-controller-") as temporary:
            directory = no_links(Path(temporary) / "workspace")
            prepare_workspace(directory)
            env = isolated_environment(Path(temporary) / "config", auth)
            for tool in settings["external_tools"].values():
                for key in tool["credential_env"]:
                    if key in os.environ:
                        env[key]=os.environ[key]
            # Auth is inherited through the process environment, never this on-disk config.
            entry = Path(__file__).with_name("internal_server.py")
            arguments = [str(entry), "--workspace", str(Path(workspace).resolve()), "--source-root", str(runtime.source_root),
                         "--instructions", str(Path(instructions).resolve()), "--run-id", run_id,
                         "--model", model, "--auth", auth, "--claude-executable", adapter.executable,
                         "--attempt-id", log.attempt_id]
            mcp = directory / "mcp.json"
            settings_path=Path(temporary)/"settings.json"
            atomic_write(settings_path,canonical(settings))
            arguments += ["--config",str(settings_path)]
            atomic_write(mcp, canonical({"mcpServers": {"verifier_internal": {"command": sys.executable, "args": arguments}}}))
            code, raw, _ = adapter.run(adapter.command(directory, session, mcp=mcp, controller=True), role="planner",
                cwd=directory, env=env, timeout=timeout, max_bytes=8*1024*1024,
                prompt="Verify the skill for run " + run_id + ". First call get_verifier_context and follow its pinned local contracts. Read all submitted text files before extracting scientific claims. Look up candidates, discover and import primary references/resources, qualify exact/numeric or generated Python evaluators, select the frozen audited plan, execute the specified repeated trials, and follow the resulting state. local_documentary requires independent cited assessment or an explicit no-evidence search account. Operational failures require record_local_limitation; never use U for a failed operation. Do not invent expected answers, approvals or grades. Continue all independent claims and finish with write_report_card.")
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
        from .execution_control import CURRENT
        control=CURRENT.get()
        if control:
            control.finishing=True  # Cleanup/reporting remain available after cancellation/deadline.
        # A completed report survives a lost final planner response. No subject is rerun.
        try:
            log.emit("run_recovery_started", run_id=run_id,
                     code=getattr(error, "code", type(error).__name__))
        except Fault:
            pass  # Diagnostic failure must not prevent authoritative cancellation.
        def recovery_control(name):
            try:
                return recorded_call(log,runtime,name,{"run_id":run_id})
            except Fault:
                # Only read/recovery and idempotent cancellation use this fallback.
                return runtime.call(name,{"run_id":run_id})
        recovered = recovery_control("get_verifier_context")
        if recovered["status"] == "ok" and recovered["data"]["verification_complete"]:
            return {"status": "ok", "data": {"run_id": run_id, "verification_complete": True,
                    "report": recovered["data"]["report"], "controller_receipt": "unavailable",
                    "report_json_path": str(runtime.store.run_dir(run_id) / "report-card.json"),
                    "report_markdown_path": str(runtime.store.run_dir(run_id) / "report-card.md")}}
        recovery_control("cancel_verifier_run")
        partial={}
        try:
            from .partial_report import write_partial_report
            partial=write_partial_report(runtime.store,run_id,getattr(error,"code","interrupted"))
        except (Fault,OSError):
            partial={"partial_report_unavailable":True}
        return {"status": "incomplete", "error": {"code": error.code if isinstance(error, Fault) else "interrupted",
                "message": "Local verification stopped. Saved evidence is retained; no uncertain trial was replayed.",
                "run_id": run_id, "run_directory": str(runtime.store.run_dir(run_id)), "verification_complete": False},**partial}


class PublicRuntime:
    interruptible=True
    control=None
    instructions = "Call verify_skill once for the user's selected skill path. It returns the completed report or an honest operational limitation."
    definitions = [{"name": "verify_skill", "description": "Verify a local skill in fresh Claude Code sessions and return its traceable report.",
                    "inputSchema": obj({"source_path": string(4096)}),
                    "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}}]

    def __init__(self, **configuration):
        self.configuration = configuration

    def call(self, name, arguments, call_id=None):
        from .common import validate
        from .execution_control import CURRENT,Control
        token=CURRENT.set(self.control or Control(self.configuration.get("timeout",1800)))
        try:
            if name != "verify_skill":
                raise Fault("unknown_tool", "The public local interface exposes verify_skill only.")
            validate(arguments, self.definitions[0]["inputSchema"])
            return verify(arguments["source_path"], **self.configuration)
        except (Fault, OSError) as error:
            return {"status": "unavailable", "error": {"code": error.code if isinstance(error, Fault) else "configuration_unavailable",
                    "message": str(error) if isinstance(error, Fault) else "Local configuration is unavailable.", "verification_complete": False}}
        finally:
            CURRENT.reset(token)
