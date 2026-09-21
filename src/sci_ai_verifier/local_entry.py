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
# Numbered so the order is unambiguous. The pinned contracts remain authoritative;
# this is the task, not a second workflow definition.
PLANNER_PROMPT = """Verify the skill for run {run_id}.

The authorized source path is exactly:
{source_path}
Pass that string, unchanged, as `source_path` to load_submitted_skill. Do not shorten it,
make it relative, or substitute a file name inside it.

Your current state token is {state_token}. Every tool reply returns the next one; always
use the newest. The pinned contracts that govern this run are appended to this message --
read them before acting. get_verifier_context returns your current state, token and
authorized path, and takes an optional `section` to re-read one pinned document or
committed artifact if you lose this message.

1. Read every submitted text file, then commit the claim manifest quoting only what you read.
2. For each claim, look up existing candidates first, then use WebSearch to find independent
   primary references and import them with the reference, resource or asset tools. Python
   retrieves the bytes; your own summary of a source is not evidence.
3. Aim for the strongest evidence the claim allows: expected answers Python retrieved from an
   independent source, scored by an installed comparison method. Qualify a candidate, then call
   select_local_candidate proposing exactly the ceiling Python reports for that design. Aiming
   lower is refused, and so is claiming more. An independent critique session then judges
   whether the evidence really fits the claim.
4. If it returns local_grade_revision_required, you have two moves: qualify a stronger design
   (better source, more cases) and propose its new ceiling, or accept the grade the critique
   supported for this design. Proposing again on the same design is refused and wins nothing.
   Do not argue with the critique and do not aim low to be safe.
5. Execute the settled plan and follow the state Python returns. An execution that supports
   no grade moves to local_documentary, where an independent assessor judges cited sources.
6. record_local_limitation is only for a cause you actually hit, and U is only for a genuine
   absence of evidence after a search Python observed. Neither is a way to finish faster.
7. Never invent an expected answer, an approval or a grade. Finish every independent claim and
   end with write_report_card."""


def planner_prompt(runtime, run_id, created):
    """Deliver the pinned contracts and the authorized path in the prompt itself.

    A tool reply large enough to be spilled to a file is unreadable to this planner:
    its session has no file-read tool. The contracts are instructions, so they belong
    in the instruction turn, and the authorized source path travels with them rather
    than waiting at the end of a 50 KB reply.
    """
    documents = []
    for entry in created["instructions"]:
        text = runtime.store.get(entry["digest"]).decode("utf-8")
        documents.append(f'<pinned-instruction identity="{entry["identity"]}" '
                         f'digest="{entry["digest"]}">\n{text}\n</pinned-instruction>')
    task = PLANNER_PROMPT.format(run_id=run_id, state_token=created["state_token"],
                                 source_path=created["authorized_parameters"]["source_path"])
    return task + "\n\n" + "\n\n".join(documents)


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
    if settings["sandbox_image"]:
        # Probe the container engine before spending a planner session. The CLI preflight
        # reports `live_execution_tested: false` and never touches Docker, so a stopped
        # daemon used to surface at the first subject call, minutes and dollars into a run
        # whose every execution claim was already doomed.
        from .sandbox import DockerSandbox
        preflight["sandbox"] = DockerSandbox(workspace, settings).preflight()
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
            credential = "ANTHROPIC_API_KEY" if auth == "api" else "CLAUDE_CODE_OAUTH_TOKEN"
            # The host CLI removes its own auth variables before expanding an MCP
            # configuration, so a self-referencing placeholder resolves to empty. The
            # credential is offered under a neutral alias that survives that expansion.
            alias = "SCI_VERIFIER_INTERNAL_CREDENTIAL"
            env[alias] = env[credential]
            internal_env = {credential: "${" + alias + ":-}"}
            for tool in settings["external_tools"].values():
                for key in tool["credential_env"]:
                    if key in os.environ:
                        env[key]=os.environ[key]
                        internal_env[key]="${" + key + ":-}"
            # Restricted MCP subprocesses may inherit only a safe baseline. Explicit
            # variable references forward approved credentials without writing values.
            entry = Path(__file__).with_name("internal_server.py")
            arguments = [str(entry), "--workspace", str(Path(workspace).resolve()), "--source-root", str(runtime.source_root),
                         "--instructions", str(Path(instructions).resolve()), "--run-id", run_id,
                         "--model", model, "--auth", auth, "--claude-executable", adapter.executable,
                         "--attempt-id", log.attempt_id]
            mcp = directory / "mcp.json"
            settings_path=Path(temporary)/"settings.json"
            atomic_write(settings_path,canonical(settings))
            arguments += ["--config",str(settings_path)]
            atomic_write(mcp, canonical({"mcpServers": {"verifier_internal": {
                "command": sys.executable, "args": arguments, "env": internal_env}}}))
            code, raw, _ = adapter.run(adapter.command(directory, session, mcp=mcp, controller=True), role="planner",
                cwd=directory, env=env, timeout=timeout, max_bytes=8*1024*1024,
                prompt=planner_prompt(runtime, run_id, created["data"]))
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
            state, _ = runtime.store.read(run_id)
            return {"status": "ok", "data": {"run_id": run_id, "verification_complete": True,
                    "report": runtime.store.get_json(state["report_ref"]),
                    "controller_receipt": "unavailable",
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
