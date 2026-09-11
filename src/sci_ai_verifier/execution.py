"""Host-provisioned subject observations; no model-controlled adapter or oracle leakage."""

import time
from copy import deepcopy

from .catalog import decode
from .common import Fault, canonical
from .ingest import verified_snapshot
from .planning import artifact, keep, operational, parent
from .scientific import method_current, score
from .storage import atomic_write, no_links


class UnavailableSubject:
    identity = {"adapter_id": "unavailable", "model_id": "not_configured", "synthetic": False}

    def observe(self, *, source, case_input, config, timeout_seconds):
        raise OSError("No subject adapter is configured.")


def trial_record(store, state, directory, index, kind, value):
    key = keep(store, state, value)
    # This small receipt precedes further calls. It survives a missing main-journal commit.
    atomic_write(directory / f"{index:04d}.{kind}.json", canonical({"object_ref": key}))
    return key


def recovered_refs(store, directory):
    refs = []
    for path in sorted(no_links(directory).glob("*.json")):
        receipt = decode(no_links(path).read_bytes())
        if not isinstance(receipt, dict) or set(receipt) != {"object_ref"}:
            raise Fault("execution_receipt_invalid", "An execution receipt failed validation.", fatal=True)
        store.get(receipt["object_ref"])
        refs.append(receipt["object_ref"])
    return refs


def execute(store, state, args, subject):
    item, plan = parent(store, state, args)
    audit = store.get_json(item["audit_ref"]) if item["audit_ref"] else None
    if audit is None or audit["id"] != args["audit_id"] or audit["audit_status"] != "pass":
        raise Fault("stale_audit", "Use the passing audit for this exact plan.", ["audit_id"])
    if (audit["plan_ref"] != item["plan_ref"] or audit["lock_ref"] != item["lock_ref"]
            or audit["bundle_ref"] != item["bundle_ref"]):
        raise Fault("audit_parent_integrity", "Audit no longer binds the current plan assets.", fatal=True)
    if args["request_budget"] != plan["max_subject_calls"]:
        raise Fault("execution_budget", "Use the exact audited subject-call budget.", ["request_budget"])
    if not method_current(state):
        return operational(store, state, args["claim_id"], "implementation_required",
                           "Installed method differs from the pinned audit; start a new run.")
    if subject.identity != plan["subject_config"]:
        return operational(store, state, args["claim_id"], "subject_runner_unavailable",
                           "Configured subject identity differs from the audited identity.")
    if state["subject_calls_used"] + plan["max_subject_calls"] > state["execution_limits"]["max_subject_calls"]:
        return operational(store, state, args["claim_id"], "operational_failure", "Run execution budget exhausted.")
    directory = store.run_dir(state["run_id"]) / "execution-attempts" / item["plan_ref"]
    previous = recovered_refs(store, directory)
    if previous:
        recovered_calls = 0
        for key in previous:
            if key not in state["objects"]:
                state["objects"].append(key)
            value = store.get_json(key)
            if value.get("snapshot_ref"):
                if value.get("plan_ref") != item["plan_ref"] or value.get("run_id") != state["run_id"]:
                    raise Fault("execution_receipt_invalid", "A recovered request belongs to a different plan.", fatal=True)
                recovered_calls += 1
        state["subject_calls_used"] += recovered_calls
        return operational(store, state, args["claim_id"], "operational_failure",
                           "An earlier execution attempt was interrupted. Its sample is retained, not replayed.", previous)
    snapshot = verified_snapshot(store, state)
    # Only snapshot text is subject instruction; no planner text, rubric, references or expected answers.
    source = []
    total = 0
    for entry in snapshot["files"]:
        if entry["encoding"] == "utf-8":
            raw = store.get(entry["digest"])
            total += len(raw)
            if total > 128 * 1024:
                return operational(store, state, args["claim_id"], "subject_runner_unavailable",
                                   "The text-only subject profile supports at most 128 KiB of submitted text.")
            source.append({"path": entry["path"], "content": raw.decode("utf-8")})
    bundle = store.get_json(item["bundle_ref"])
    observations, raw_refs = [], []
    index = 0
    for case in bundle["cases"]:
        case_scores = []
        for trial in range(plan["trial_count"]):
            index += 1
            request = artifact(state, "subject-request", args["claim_id"], plan_ref=item["plan_ref"],
                               case_id=case["case_id"], trial=trial + 1,
                               snapshot_ref=state["source_ref"], input=case["input"], subject=plan["subject_config"])
            raw_refs.append(trial_record(store, state, directory, index, "request", request))
            state["subject_calls_used"] += 1
            started = time.monotonic()
            try:
                response = subject.observe(source=deepcopy(source), case_input=dict(case["input"]),
                                           config=dict(plan["subject_config"]),
                                           timeout_seconds=state["execution_limits"]["request_timeout_seconds"])
                if time.monotonic() - started > state["execution_limits"]["request_timeout_seconds"]:
                    raise OSError("Subject deadline exceeded.")
                if (not isinstance(response, dict) or set(response) != {"text", "model_id", "response_id"}
                        or response["model_id"] != plan["subject_config"]["model_id"]
                        or not isinstance(response["response_id"], str) or not response["response_id"]
                        or len(response["response_id"]) > 200 or not isinstance(response["text"], str)
                        or len(response["text"].encode("utf-8")) > state["execution_limits"]["max_response_bytes"]):
                    raise OSError("Invalid or mismatched subject response.")
            except Exception:
                return operational(store, state, args["claim_id"], "operational_failure",
                                   "The subject adapter did not return a complete bounded observation; no retry was made.", raw_refs)
            raw_output = artifact(state, "subject-output", args["claim_id"], request_ref=raw_refs[-1], **response)
            raw_ref = trial_record(store, state, directory, index, "response", raw_output)
            raw_refs.append(raw_ref)
            scored = score(response["text"], case["expected_mass_da"])
            scored.update(trial=trial + 1, raw_output_ref=raw_ref)
            case_scores.append(scored)
        usable = [s["status"] for s in case_scores if s["status"] != "invalid"]
        agreement = (max((usable.count(value) for value in set(usable)), default=0) / len(case_scores))
        observations.append({"case_id": case["case_id"], "input": case["input"], "trials": case_scores,
                             "agreement": agreement, "requested_trials": plan["trial_count"]})
    invalid = sum(s["status"] == "invalid" for c in observations for s in c["trials"])
    status = None if invalid else ("pass" if all(s["status"] == "pass" for c in observations for s in c["trials"])
                                  else "fail")
    record = artifact(state, "execution", args["claim_id"], plan_ref=item["plan_ref"], audit_ref=item["audit_ref"],
                      snapshot_digest=plan["snapshot_digest"], subject=plan["subject_config"],
                      observations=observations, raw_refs=raw_refs, decision_status=status,
                      achieved_grade_ceiling=None if invalid else plan["planned_grade"],
                      policy_ref=plan["policy_ref"], grade_limit_reasons=["Pilot supports independent comparison grade C only"],
                      requested=plan["max_subject_calls"], attempted=index, obtained=index, evaluated=index-invalid,
                      invalid=invalid, missing=0, coverage=bundle["coverage"], exclusions=bundle["exclusions"],
                      synthetic=plan["subject_config"]["synthetic"])
    item["execution_ref"] = keep(store, state, record)
    if invalid:
        # No execution grade may be invented. This delivery has no independent D assessor.
        return operational(store, state, args["claim_id"], "assessor_unavailable",
                           "Invalid scientific observations leave no supported execution grade; no independent D assessor is configured.",
                           [item["execution_ref"], *raw_refs])
    state["claim_states"][args["claim_id"]] = "result_commit"
    return {"outcome": "completed_deterministic_decision", "execution": record}
