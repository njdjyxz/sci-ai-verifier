"""Stable tool schemas and the profile-aware deterministic dispatcher."""

from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from .claims import FIELDS, build_manifest
from .common import Fault, canonical, digest, utc_now, validate
from .ingest import authorized_source, read_file, snapshot, verified_snapshot
from . import routing

DEFAULT_LIMITS = {
    "max_steps": 64, "repair_retries": 8, "illegal_transitions": 8,
    "max_files": 200, "max_file_bytes": 1024 * 1024, "max_total_bytes": 8 * 1024 * 1024,
    "max_read_bytes": 128 * 1024, "max_claims": 100,
    "resumption_window_seconds": 24 * 60 * 60,
}
LEGAL = {"created": ["load_submitted_skill"],
         "source_ready": ["read_snapshot_file", "commit_claim_manifest"],
         "claims_ready": ["list_claim_types", "commit_claim_type_assignments"],
         "active": ["find_registered_evaluators"],
         "stage2_complete": [], "stage3_complete": [], "incomplete": []}

CLAIM_TOOLS = {"routing": ["list_claim_types", "commit_claim_type_assignments"],
               "capability_selection": ["find_registered_evaluators"],
               "planning": ["commit_evaluation_plan"],
               "resource_resolution": ["find_resources", "materialize_resources"],
               "bundle_construction": ["build_evaluation_bundle", "validate_evaluation_bundle"],
               "provisional_registration": ["register_evaluator"], "audit": ["commit_plan_audit"],
               "execution": ["execute_evaluation_plan"], "result_commit": ["commit_claim_result"],
               "terminal_result": [], "terminal_operational": []}


def legal_tools(state):
    if state["profile"] == "local":
        from .local import legal
        return legal(state)
    if state["profile"] == "demo":
        from .demo import LEGAL as DEMO_LEGAL
        return DEMO_LEGAL[state["run_state"]]
    if state["profile"] == "verification":
        if state["run_state"] == "active":
            return sorted({name for value in state["claim_states"].values() for name in CLAIM_TOOLS[value]})
        if state["run_state"] == "reporting":
            return ["write_report_card"]
        if state["run_state"] == "completed":
            return []
    return LEGAL[state["run_state"]]


def string(maximum=4096, minimum=1):
    return {"type": "string", "minLength": minimum, "maxLength": maximum}


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


BASE = {"run_id": string(36), "state_token": string(36)}
PARENT = {"snapshot_id": string(80), "snapshot_digest": string(64)}
RANGE = {"type": "integer", "minimum": 0, "maximum": DEFAULT_LIMITS["max_file_bytes"]}
PLAN_BASE = {**BASE, "claim_id": string(80), "plan_id": string(80),
             "plan_revision": {"type": "integer", "minimum": 1, "maximum": 256}}
SCHEMAS = {
    "start_inline_demo_run": obj({"source_name": string(200), "source_text": string(262144)}),
    "start_verifier_run": obj({"source_path": string(), "model_label": string(200)},
                              ["source_path"]),
    "get_verifier_context": obj({"run_id": string(36)}),
    "resume_verifier_run": obj({"run_id": string(36)}),
    "cancel_verifier_run": obj({"run_id": string(36)}),
    "load_submitted_skill": obj({**BASE, "source_path": string()}),
    "read_snapshot_file": obj(
        {**BASE, **PARENT, "path": string(), "start": RANGE, "end": RANGE},
        [*BASE, *PARENT, "path"]),
    "commit_claim_manifest": obj({
        **BASE, **PARENT,
        "claims": {"type": "array", "maxItems": 100,
                   "items": obj({key: string(16000, 0 if key == "report_note" else 1)
                                 for key in FIELDS})},
    }),
    "list_claim_types": obj(BASE),
    "commit_claim_type_assignments": obj({
        **BASE, "manifest_id": string(80), "index_digest": string(64),
        "assignments": {"type": "array", "maxItems": 100, "items": obj({
            "claim_id": string(80), "claim_type_id": string(160, 0),
            "proposal": obj({key: string(16000) for key in
                             ("name", "definition", "inputs", "outputs", "boundaries")}, []),
            "report_note": string(16000, 0),
        })},
    }),
    "find_registered_evaluators": obj({
        **BASE, "claim_id": string(80), "route_id": string(80), "scope": string(16000),
        "intended_grade": string(1),
    }),
    "commit_evaluation_plan": obj({**BASE, "claim_id": string(80), "selection_id": string(80),
        "match_index": {"type": "integer", "minimum": 0, "maximum": 15}, "scope": string(16000),
        "trial_count": {"type": "integer", "minimum": 1, "maximum": 10}, "report_note": string(16000, 0)}),
    "find_resources": obj(PLAN_BASE),
    "materialize_resources": obj({**PLAN_BASE, "search_id": string(80)}),
    "build_evaluation_bundle": obj(PLAN_BASE),
    "validate_evaluation_bundle": obj({**PLAN_BASE, "bundle_id": string(80)}),
    "register_evaluator": obj({**PLAN_BASE, "bundle_id": string(80)}),
    "commit_plan_audit": obj({**PLAN_BASE, "resource_lock_id": string(80), "scope_finding": string(20),
        "fairness_finding": string(20), "proposed_status": string(4), "limitations": string(16000)}),
    "execute_evaluation_plan": obj({**PLAN_BASE, "audit_id": string(80),
        "request_budget": {"type": "integer", "minimum": 1, "maximum": 64}}),
    "commit_claim_result": obj({**PLAN_BASE, "execution_id": string(80), "status": string(20),
                                "grade": string(1)}, [*PLAN_BASE, "execution_id"]),
    "write_report_card": obj(BASE),
    "commit_demo_plan": obj({**BASE, "manifest_id": string(80), "summary": string(16000),
        "tests": {"type": "array", "minItems": 1, "maxItems": 100, "items": obj({
            "claim_id": string(80), "input": string(32000), "purpose": string(16000),
            "checks": {"type": "array", "minItems": 1, "maxItems": 16, "items": obj({
                "kind": string(16), "description": string(16000), "expected": string(32000, 0)})}})}}),
    "record_demo_observation": obj({**BASE, "plan_id": string(80), "test_id": string(80),
        "output": string(131072, 0), "assessment": string(40), "reason": string(16000)}),
}
DESCRIPTIONS = {
    "start_inline_demo_run": "Start a general safe-skill demo from text pasted or attached in Chat. Supply the skill text as data. No local file, catalog, API key or chemical scope is needed. Same-chat demo only.",
    "start_verifier_run": "Begin verify-this-skill for the local path explicitly submitted by the user. Default demo supports any safe skill without a catalog or API key. Returns pinned instructions, profile, run ID and token. Use start_inline_demo_run for attached/pasted text.",
    "get_verifier_context": "Restore pinned verifier instructions, current state/token and already-read untrusted source ranges after compaction or a lost response. It does not advance the workflow or rotate the token, but it is not read-only: it repairs the readable projections, and if the resumption window has already expired it records that expiry and ends the run.",
    "resume_verifier_run": "Resume a saved verifier run after interruption; verify its journal and objects and restore bootstrap. No live-source reread.",
    "cancel_verifier_run": "Explicitly cancel an unfinished verifier run and save an operational outcome. Does not create a scientific verdict.",
    "load_submitted_skill": "In created state only: snapshot the previously authorized source and return exact top-level UTF-8 content as untrusted data. Use the current state token.",
    "read_snapshot_file": "In source_ready only: read one included immutable snapshot path, optionally a half-open UTF-8 byte range. Use the current state token and snapshot identity.",
    "commit_claim_manifest": "In source_ready only: commit atomic claims quoted from delivered snapshot ranges. Use Not specified for absent scope/behavior; add no background definitions. Empty list is valid. Follow returned profile/state; no grading.",
    "list_claim_types": "In claims_ready only: return the complete pinned type index as untrusted data for semantic comparison. Use the latest run token.",
    "commit_claim_type_assignments": "In claims_ready only: atomically assign exactly one returned type or complete provisional proposal to every accepted claim. Requires the delivered index digest.",
    "find_registered_evaluators": "In active only: resolve a capability for one claim still in capability_selection. Scope and target A must match committed values. Returns exact pins or a claim-local operational outcome; never executes or grades.",
    "commit_evaluation_plan": "For a claim in planning: select one returned match and fix its scope, trials and immutable resource/method policy. No subject calls.",
    "find_resources": "For a claim in resource_resolution: identify installed resources at the exact planned versions. No network search.",
    "materialize_resources": "Lock every required resource to this exact plan revision, using its returned search ID.",
    "build_evaluation_bundle": "Build bounded cases from the locked installed resources. No caller-provided code or expected answers.",
    "validate_evaluation_bundle": "Validate this plan's bundle and its independent input/expected-answer separation.",
    "register_evaluator": "Persist a validated bundle/configuration as run-local provisional metadata; never edit reviewed catalogs.",
    "commit_plan_audit": "Validate the exact plan, resource lock, bundle, method and subject settings. Scope/fairness findings are supported, unsupported or uncertain; proposed status is advisory.",
    "execute_evaluation_plan": "Obtain separately recorded observations using the operator-configured subject adapter, then score each trial deterministically. Never include reference answers in subject input.",
    "commit_claim_result": "Copy the exact authoritative execution verdict and grade; never invent a verdict from tool success.",
    "write_report_card": "In reporting only: account for every accepted claim and save immutable JSON and readable Markdown reports. No overall scientific grade.",
    "commit_demo_plan": "In demo_planning: fix useful example inputs and checks covering every accepted skill behavior before producing outputs. No scientific approval is implied.",
    "record_demo_observation": "In demo_execution: record the actual same-chat example output, or not_tested for unavailable capabilities. Never invent external execution. Deterministic check failures override proposed success.",
}
from .local import schemas as local_schemas, OPERATIONS as LOCAL_OPERATIONS
SCHEMAS.update(local_schemas(BASE, obj, string))
DESCRIPTIONS.update({name: "Internal local verification operation: " + name.replace("_", " ") +
                     ". Follow the pinned local contract and current claim state. Never grants scientific approval."
                     for name in LOCAL_OPERATIONS})
DEFINITIONS = [
    # No tool is read-only: every one of them can write the journal or repair a projection.
    {"name": name, "description": DESCRIPTIONS[name], "inputSchema": schema,
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}}
    for name, schema in SCHEMAS.items()
]
WORKFLOW_TOOLS = ("load_submitted_skill", "read_snapshot_file", "commit_claim_manifest",
                  "list_claim_types", "commit_claim_type_assignments", "find_registered_evaluators",
                  "commit_evaluation_plan", "find_resources", "materialize_resources", "build_evaluation_bundle",
                  "validate_evaluation_bundle", "register_evaluator", "commit_plan_audit",
                  "execute_evaluation_plan", "commit_claim_result", "write_report_card",
                  "commit_demo_plan", "record_demo_observation", *LOCAL_OPERATIONS)


def metadata(state):
    return {
        "scope": "run", "run_id": state["run_id"], "profile": state["profile"],
        "run_state": state["run_state"], "claim_states": state["claim_states"],
        "committed_state": state["run_state"], "next_legal_tools": legal_tools(state),
        "state_token": state["state_token"], "revision": state["revision"],
        "verification_complete": state["verification_complete"],
    }


def persistence_failure(code=None, reason=None):
    # The run's committed state was never established here, so it is reported unknown
    # rather than asserted incomplete. `details` names the cause that was established.
    return {"status": "fatal", "error": {
        "code": "operational_outcome_persistence_failed",
        "message": "Trusted run recovery or durable outcome persistence failed; no completed audit is claimed.",
        "scope": "run", "run_state": None, "committed_state": None,
        "claim_states": {}, "next_legal_tools": [], "operational_outcome_id": None,
        "details": {"reason_code": code, "reason": reason} if code else {},
        "verification_complete": False,
    }}


def advance(state):
    state["revision"] += 1
    state["updated_at"] = utc_now()
    state["state_token"] = str(uuid4())


def keep_object(state, key):
    if key not in state["objects"]:
        state["objects"].append(key)


def terminate(store, state, code, message, attempted_tool=None):
    prior_state = state["run_state"]
    state["run_state"] = "incomplete"
    state["completion_reason"] = code
    state["finished_at"] = utc_now()
    outcome = {
        "schema_version": 1, "id": "outcome-" + str(uuid4()),
        "run_id": state["run_id"], "created_at": utc_now(),
        "implementation_version": state["implementation_version"],
        "scope": "run", "category": code, "reason": message,
        "workflow_state": prior_state, "attempted_tool": attempted_tool,
        "attempts_used": state["steps_used"], "limits": state["limits"],
        "artifact_refs": list(state["objects"]), "terminal": True,
        "scientific_status": None, "evidence_grade": None,
        "restart": "Create a new run after resolving the recorded operational cause.",
    }
    key = store.put_json(outcome)
    state["operational_refs"].append(key)
    keep_object(state, key)
    state["finalization"] = store.finalize(state)
    return {"status": "fatal", "error": {
        **metadata(state), "code": code, "message": message, "details": {},
        "operational_outcome_id": outcome["id"],
    }}


def expired(state):
    return (datetime.fromisoformat(utc_now()) - datetime.fromisoformat(state["last_activity_at"])
            ).total_seconds() >= state["limits"]["resumption_window_seconds"]


class Dispatcher:
    def __init__(self, store, subject=None):
        self.store = store
        self.subject = subject

    def dispatch(self, name, arguments, call_id=None):
        run_id = arguments.get("run_id") if isinstance(arguments, dict) else None
        with self.store.lock(run_id):
            state, previous = self.store.read(run_id, verify_objects=False)
            before = deepcopy(metadata(state))
            # Closing the prototype never permits a later request to rewrite the checkpoint.
            if not legal_tools(state):
                return {"status": "retryable", "error": {
                    **metadata(state), "code": "run_closed", "message": "This run accepts no further workflow calls.",
                    "details": {}, "repair_fields": [], "refresh_required": False,
                    "retries_remaining": state["retries_remaining"],
                    "illegal_transitions_remaining": state["illegal_transitions_remaining"],
                }}
            advance(state)
            state["steps_used"] += 1
            state["last_activity_at"], last_activity = utc_now(), state["last_activity_at"]
            fault = None
            illegal = (name not in legal_tools(state)
                       or arguments.get("state_token") != before["state_token"])
            if (name == "find_registered_evaluators" and name in legal_tools(state)
                    and isinstance(arguments.get("claim_id"), str)
                    and arguments["claim_id"] in state["claim_states"]
                    and state["claim_states"][arguments["claim_id"]] != "capability_selection"):
                illegal = True
            if (state["profile"] == "verification" and isinstance(arguments.get("claim_id"), str)
                    and arguments["claim_id"] in state["claim_states"]
                    and name not in CLAIM_TOOLS[state["claim_states"][arguments["claim_id"]]]):
                illegal = True
            try:
                for key in state["objects"]:
                    self.store.get(key)
                if expired({**state, "last_activity_at": last_activity}):
                    raise Fault("resumption_expired", "The resumption window expired.", fatal=True)
                if state["steps_used"] > state["limits"]["max_steps"]:
                    raise Fault("step_limit", "The workflow request limit is exhausted.", fatal=True)
                if illegal:
                    raise Fault("illegal_transition", "Use a legal tool with the latest returned state token.")
                validate(arguments, SCHEMAS[name])
                result = self._execute(name, arguments, state)
            except Fault as error:
                fault = error
                result = self._error(state, error, illegal, name)
            except OSError:
                fault = Fault("storage_failure", "Source or managed storage is unavailable.", fatal=True)
                result = self._error(state, fault, False, name)
            # Accepted calls are recorded exactly. Rejected arbitrary fields are never echoed.
            request = {"id": call_id, "tool": name, "arguments_digest": digest(canonical(arguments))}
            if fault is None:
                request["arguments"] = arguments
            self.store.record(state, previous, "tool_call", before, request, result)
            return result

    def _error(self, state, error, illegal, name):
        if error.fatal:
            return terminate(self.store, state, error.code, str(error), name)
        counter = "illegal_transitions_remaining" if illegal else "retries_remaining"
        state[counter] -= 1
        if state[counter] == 0:
            category = "illegal_transition_limit" if illegal else "retry_limit"
            return terminate(self.store, state, category, "The request repair budget is exhausted.", name)
        return {"status": "retryable", "error": {
            **metadata(state), "code": error.code, "message": str(error), "details": {},
            "repair_fields": [] if illegal else error.fields,
            "refresh_required": illegal,
            "retries_remaining": state["retries_remaining"],
            "illegal_transitions_remaining": state["illegal_transitions_remaining"],
        }}

    def _execute(self, name, arguments, state):
        if state["profile"] == "local":
            from .local_candidates import safe_payload
            safe_payload(arguments)
        if state["profile"] == "local" and name in {*LOCAL_OPERATIONS, "write_report_card"}:
            from .local import operate
            data = operate(self.store, state, name, arguments, self.subject)
        elif state["profile"] == "demo" and name in {"commit_demo_plan", "record_demo_observation", "write_report_card"}:
            from . import demo
            data = {"commit_demo_plan": demo.commit_plan, "record_demo_observation": demo.observe,
                    "write_report_card": demo.write_report}[name](self.store, state, arguments)
        elif name in WORKFLOW_TOOLS[6:]:
            from . import planning, evaluation, audit, execution, reporting
            operations = {"commit_evaluation_plan": planning.commit_plan, "find_resources": planning.find_resources,
                "materialize_resources": planning.materialize, "build_evaluation_bundle": evaluation.build,
                "validate_evaluation_bundle": evaluation.validate_bundle, "register_evaluator": evaluation.register,
                "commit_plan_audit": audit.audit_plan, "commit_claim_result": reporting.commit_result,
                "write_report_card": reporting.write_report}
            data = (execution.execute(self.store, state, arguments, self.subject) if name == "execute_evaluation_plan"
                    else operations[name](self.store, state, arguments))
        elif name in {"list_claim_types", "commit_claim_type_assignments", "find_registered_evaluators"}:
            if name == "list_claim_types":
                data = routing.list_types(self.store, state)
            elif name == "commit_claim_type_assignments":
                data = routing.assign(self.store, state, arguments)
            else:
                data = routing.select(self.store, state, arguments)
                if state["profile"] == "stage3" and all(value != "capability_selection" for value in state["claim_states"].values()):
                    state["run_state"] = "stage3_complete"
                    self._checkpoint(state, "routing_checkpoint")
            data["routing_path"] = str(self.store.run_dir(state["run_id"]) / "routing.json")
        elif name == "load_submitted_skill":
            authorized_source(arguments["source_path"], state)
            source, payload = snapshot(self.store, state)
            state["source_ref"] = self.store.put_json(source)
            keep_object(state, state["source_ref"])
            for entry in source["files"]:
                keep_object(state, entry["digest"])
            state["run_state"] = "source_ready"
            self._receipt(state, payload)
            data = {"outcome": "source_snapshotted", "snapshot": source,
                    "untrusted_payload": payload}
        else:
            source = verified_snapshot(self.store, state, arguments["snapshot_id"],
                                       arguments["snapshot_digest"])
            if name == "read_snapshot_file":
                payload = read_file(self.store, source, arguments["path"],
                                    arguments.get("start", 0), arguments.get("end"),
                                    state["limits"]["max_read_bytes"])
                self._receipt(state, payload)
                data = {"outcome": "snapshot_file_returned", "untrusted_payload": payload}
            else:
                if len(arguments["claims"]) > state["limits"]["max_claims"]:
                    raise Fault("too_many_claims", "The run claim limit was exceeded.", ["claims"])
                manifest = build_manifest(self.store, state, source, arguments["claims"])
                state["manifest_ref"] = self.store.put_json(manifest)
                keep_object(state, state["manifest_ref"])
                state["claim_states"] = {c["claim_id"]: "demo_planning" if state["profile"] == "demo" else "routing"
                                         for c in manifest["claims"]}
                state["run_state"] = (("demo_planning" if manifest["count"] else "reporting") if state["profile"] == "demo" else
                                      "stage2_complete" if state["profile"] == "stage2" else
                                      "claims_ready" if manifest["count"] else
                                      "reporting" if state["profile"] == "verification" else "stage3_complete")
                if state["profile"] == "local":
                    state["claim_states"] = {c["claim_id"]: "local_lookup" for c in manifest["claims"]}
                    state["run_state"] = "active" if manifest["count"] else "reporting"
                if not legal_tools(state):
                    self._checkpoint(state, "claim_extraction_checkpoint" if state["profile"] == "stage2"
                                     else "routing_checkpoint")
                data = {"outcome": "claims_committed" if manifest["count"] else "no_scientific_claims",
                        "manifest": manifest,
                        "manifest_path": str(self.store.run_dir(state["run_id"]) / "claim-manifest.json"),
                        "message": "Claim extraction is saved. Follow the returned legal tools; scientific verification remains pending."}
        if (state["profile"] in {"verification", "local"} and state["run_state"] == "active"
                and all(value in {"terminal_result", "terminal_operational"} for value in state["claim_states"].values())):
            state["run_state"] = "reporting"
        return {"status": "ok", "data": {**metadata(state), **data,
                                        "next_permitted_state": state["run_state"]}}

    @staticmethod
    def _receipt(state, payload):
        receipt = {key: payload[key] for key in ("path", "digest", "start", "end")}
        if receipt not in state["read_receipts"]:
            state["read_receipts"].append(receipt)

    def _checkpoint(self, state, reason):
        state["completion_reason"] = reason
        state["finished_at"] = utc_now()
        state["finalization"] = self.store.finalize(state)
