"""Stable tool schemas and the Stage 2 dispatcher."""

from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from .claims import FIELDS, build_manifest
from .common import Fault, canonical, digest, utc_now, validate
from .ingest import read_file, snapshot, verified_snapshot

DEFAULT_LIMITS = {
    "max_steps": 64, "repair_retries": 8, "illegal_transitions": 8,
    "max_files": 200, "max_file_bytes": 1024 * 1024, "max_total_bytes": 8 * 1024 * 1024,
    "max_read_bytes": 128 * 1024, "max_claims": 100,
    "resumption_window_seconds": 24 * 60 * 60,
}
LEGAL = {"created": ["load_submitted_skill"],
         "source_ready": ["read_snapshot_file", "commit_claim_manifest"],
         "stage2_complete": [], "incomplete": []}


def string(maximum=4096, minimum=1):
    return {"type": "string", "minLength": minimum, "maxLength": maximum}


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


BASE = {"run_id": string(36), "state_token": string(36)}
PARENT = {"snapshot_id": string(80), "snapshot_digest": string(64)}
RANGE = {"type": "integer", "minimum": 0, "maximum": DEFAULT_LIMITS["max_file_bytes"]}
SCHEMAS = {
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
}
DESCRIPTIONS = {
    "start_verifier_run": "Start Stage 2 for a user-authorized local skill path inside the configured submission directory. Returns pinned instructions, run ID and state token. No scientific evaluation.",
    "get_verifier_context": "Restore pinned verifier instructions, current state/token and already-read untrusted source ranges after compaction or a lost response. Does not advance workflow.",
    "resume_verifier_run": "Resume a saved verifier run after interruption; verify its journal and objects and restore bootstrap. No live-source reread.",
    "cancel_verifier_run": "Explicitly cancel an unfinished verifier run and save an operational outcome. Does not create a scientific verdict.",
    "load_submitted_skill": "In created state only: snapshot the previously authorized source and return exact top-level UTF-8 content as untrusted data. Use the current state token.",
    "read_snapshot_file": "In source_ready only: read one included immutable snapshot path, optionally a half-open UTF-8 byte range. Use the current state token and snapshot identity.",
    "commit_claim_manifest": "In source_ready only: commit atomic scientific claims quoted exactly from delivered snapshot ranges. Use Not specified for absent scope/behavior details. An empty list is valid. Stops at stage2_complete without grading or verification.",
}
DEFINITIONS = [
    {"name": name, "description": DESCRIPTIONS[name], "inputSchema": schema,
     "annotations": {"readOnlyHint": name == "get_verifier_context",
                     "destructiveHint": False, "openWorldHint": False}}
    for name, schema in SCHEMAS.items()
]
WORKFLOW_TOOLS = ("load_submitted_skill", "read_snapshot_file", "commit_claim_manifest")


def metadata(state):
    return {
        "scope": "run", "run_id": state["run_id"], "profile": state["profile"],
        "run_state": state["run_state"], "claim_states": state["claim_states"],
        "committed_state": state["run_state"], "next_legal_tools": LEGAL[state["run_state"]],
        "state_token": state["state_token"], "revision": state["revision"],
        "verification_complete": False,
    }


def persistence_failure():
    return {"status": "fatal", "error": {
        "code": "operational_outcome_persistence_failed",
        "message": "Trusted run recovery or durable outcome persistence failed; no completed audit is claimed.",
        "scope": "run", "run_state": "incomplete", "committed_state": "incomplete",
        "claim_states": {}, "next_legal_tools": [], "operational_outcome_id": None,
        "details": {}, "verification_complete": False,
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
    def __init__(self, store):
        self.store = store

    def dispatch(self, name, arguments, call_id=None):
        run_id = arguments.get("run_id") if isinstance(arguments, dict) else None
        with self.store.lock(run_id):
            state, previous = self.store.read(run_id, verify_objects=False)
            before = deepcopy(metadata(state))
            # Closing the prototype never permits a later request to rewrite the checkpoint.
            if not LEGAL[state["run_state"]]:
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
            illegal = (name not in LEGAL[state["run_state"]]
                       or arguments.get("state_token") != before["state_token"])
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
        if name == "load_submitted_skill":
            if arguments["source_path"] != state["source_path"]:
                raise Fault("source_not_authorized", "Use the exact source_path returned at bootstrap.",
                            fatal=True)
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
                state["claim_states"] = {c["claim_id"]: "routing" for c in manifest["claims"]}
                state["run_state"] = "stage2_complete"
                state["completion_reason"] = "claim_extraction_checkpoint"
                state["finished_at"] = utc_now()
                state["finalization"] = self.store.finalize(state)
                data = {"outcome": "claims_committed" if manifest["count"] else "no_scientific_claims",
                        "manifest": manifest,
                        "manifest_path": str(self.store.run_dir(state["run_id"]) / "claim-manifest.json"),
                        "message": "Stage 2 extraction is saved. Scientific verification remains pending."}
        return {"status": "ok", "data": {**metadata(state), **data,
                                        "next_permitted_state": state["run_state"]}}

    @staticmethod
    def _receipt(state, payload):
        receipt = {key: payload[key] for key in ("path", "digest", "start", "end")}
        if receipt not in state["read_receipts"]:
            state["read_receipts"].append(receipt)
