"""Bounded plans, immutable revision parents and installed resource locks."""

from copy import deepcopy

from .common import Fault, canonical, digest
from .routing import identity

FIELDS = ("plan_ref", "search_ref", "lock_ref", "bundle_ref", "validation_ref",
          "registration_ref", "audit_ref", "execution_ref", "result_ref")


def work(state, claim_id):
    if claim_id not in state["claim_states"]:
        raise Fault("unknown_claim", "Use an accepted claim ID.", ["claim_id"])
    return state["claim_work"].setdefault(claim_id, {**dict.fromkeys(FIELDS), "revision": 0})


def keep(store, state, value):
    key = store.put_json(value)
    if key not in state["objects"]:
        state["objects"].append(key)
    return key


def artifact(state, artifact_kind, claim_id, **fields):
    value = {"schema_version": 1, "run_id": state["run_id"], "claim_id": claim_id,
             "implementation_version": state["implementation_version"],
             "created_at": state["updated_at"], **fields}
    value["id"] = artifact_kind + "-" + digest(canonical(value))
    return value


def parent(store, state, arguments):
    item = work(state, arguments["claim_id"])
    if not item["plan_ref"]:
        raise Fault("plan_missing", "Commit a plan before this operation.", ["plan_id"])
    plan = store.get_json(item["plan_ref"])
    if arguments["plan_id"] != plan["id"] or arguments["plan_revision"] != plan["revision"]:
        raise Fault("stale_plan", "Use the latest committed plan ID and revision.", ["plan_id", "plan_revision"])
    return item, plan


def operational(store, state, claim_id, category, reason, refs=()):
    value = artifact(state, "outcome", claim_id, scope="claim", category=category, reason=reason,
                     workflow_state=state["claim_states"][claim_id], terminal=True,
                     artifact_refs=list(refs), scientific_status=None, evidence_grade=None)
    key = keep(store, state, value)
    state["operational_refs"].append(key)
    state["claim_states"][claim_id] = "terminal_operational"
    return {"outcome": category, "operational_outcome_id": value["id"], "claim_id": claim_id}


def commit_plan(store, state, args):
    from .scientific import METHOD, POLICY, SCOPE, resource_requirements
    claim_id = args["claim_id"]
    item = work(state, claim_id)
    routing = store.get_json(state["routing_ref"])
    selection = next((s for s in reversed(routing["selections"])
                      if s["claim_id"] == claim_id and s["selection_id"] == args["selection_id"]), None)
    if selection is None or args["match_index"] >= len(selection["matches"]):
        raise Fault("unknown_selection", "Use a returned selection and match index.", ["selection_id", "match_index"])
    if args["scope"] != selection["scope"]:
        raise Fault("scope_changed", "Plan scope must equal the selected claim scope.", ["scope"])
    grade = selection["resolved_grade"]
    if grade == "D":
        return operational(store, state, claim_id, "assessor_unavailable",
                           "No independent documentary assessor is configured in this delivery.")
    match = selection["matches"][args["match_index"]]
    capability = next(c for c in selection["capability_contracts"] if c["id"] == match["capability"]["id"])
    runner = next((r for r in selection["runner_contracts"]
                   if isinstance(match["subject_runner"], dict) and r["id"] == match["subject_runner"]["id"]), None)
    if capability.get("method") != METHOD or capability.get("policy_sha256") != digest(canonical(POLICY)):
        return operational(store, state, claim_id, "implementation_required",
                           "The selected capability does not name the installed method and fixed policy.")
    if runner is None or runner.get("adapter_id") != state["subject_config"]["adapter_id"]:
        return operational(store, state, claim_id, "subject_runner_unavailable",
                           "The selected runner does not match the operator-configured subject adapter.")
    model = state["subject_config"]["model_id"]
    models, trials = runner.get("model_allowlist"), runner.get("max_trials")
    if (not isinstance(models, list) or not models or len(models) > 32
            or any(not isinstance(value, str) or not 1 <= len(value) <= 200 for value in models)
            or type(trials) is not int or not 1 <= trials <= 10):
        return operational(store, state, claim_id, "subject_runner_unavailable",
                           "The selected runner has no valid bounded model and trial configuration.")
    if model not in models or args["trial_count"] > trials:
        raise Fault("runner_configuration", "Model or trial count is outside the reviewed runner bounds.", ["trial_count"])
    if args["scope"] != SCOPE:
        return operational(store, state, claim_id, "implementation_required",
                           "The installed cases require the explicit neutral CHNOPS isotope convention.")
    if grade not in POLICY["supported_grades"]:
        return operational(store, state, claim_id, "implementation_required",
                           "This method's fixed policy does not support the selected grade.")
    expected_resources = resource_requirements(state)
    if sorted(capability["resources"], key=lambda p: p["id"]) != expected_resources:
        return operational(store, state, claim_id, "resource_unavailable",
                           "The selected capability requires a different resource version.")
    registration = store.get_json(item["registration_ref"]) if item["registration_ref"] else None
    if registration and registration["selection_id"] != selection["selection_id"]:
        registration = None
    revision = item["revision"] + 1
    source = store.get_json(state["source_ref"])
    plan = artifact(state, "plan", claim_id, revision=revision, previous_plan_ref=item["plan_ref"],
                    selection_id=selection["selection_id"], route_id=selection["route_id"],
                    kind="registered" if registration or selection["capability_kind"] == "registered" else "target",
                    registration_ref=item["registration_ref"] if registration else None,
                    snapshot_id=source["id"], snapshot_digest=source["digest"],
                    scope=args["scope"], requested_grade=state["intended_grade"], planned_grade=grade,
                    capability=match["capability"], subject_runner=match["subject_runner"],
                    subject_config=deepcopy(state["subject_config"]), trial_count=args["trial_count"],
                    required_resources=expected_resources, method=METHOD,
                    method_ref=state["method_ref"], policy=POLICY, policy_ref=digest(canonical(POLICY)),
                    max_subject_calls=len(state["case_formulas"]) * args["trial_count"],
                    report_note=args["report_note"], ai_involvement={"orchestration": True,
                        "evidence_generation": "case_selection_requires_scientific_review", "verdict": False})
    if plan["max_subject_calls"] > state["execution_limits"]["max_subject_calls"]:
        raise Fault("execution_budget", "The planned sample exceeds the configured call budget.", ["trial_count"])
    # Commit only after all repairable validation has succeeded.
    prior_registration = item["registration_ref"] if registration else None
    item.update(dict.fromkeys(FIELDS))
    item.update(revision=revision, registration_ref=prior_registration, plan_ref=keep(store, state, plan))
    state["claim_states"][claim_id] = "resource_resolution"
    return {"outcome": "resource_resolution_required", "plan": plan}


def find_resources(store, state, args):
    item, plan = parent(store, state, args)
    candidates = []
    for pin in plan["required_resources"]:
        entry = state["resource_assets"].get(pin["id"])
        if entry is None or {k: entry[k] for k in ("id", "version", "sha256")} != pin:
            return operational(store, state, args["claim_id"], "resource_unavailable",
                               "A required installed resource is unavailable at its planned version.")
        store.get(entry["sha256"])
        candidates.append(entry)
    search = artifact(state, "search", args["claim_id"], plan_id=plan["id"],
                      plan_revision=plan["revision"], candidates=candidates)
    item["search_ref"] = keep(store, state, search)
    return {"outcome": "planned_grade_candidates_complete", "search": search}


def materialize(store, state, args):
    item, plan = parent(store, state, args)
    search = store.get_json(item["search_ref"]) if item["search_ref"] else None
    if search is None or args["search_id"] != search["id"] or search["plan_id"] != plan["id"]:
        raise Fault("stale_search", "Use the search belonging to this exact plan revision.", ["search_id"])
    for entry in search["candidates"]:
        store.get(entry["sha256"])
    lock = artifact(state, "lock", args["claim_id"], plan_id=plan["id"], plan_revision=plan["revision"],
                    bindings=search["candidates"], complete=True)
    item["lock_ref"] = keep(store, state, lock)
    if plan["kind"] == "registered":
        from .evaluation import construct
        bundle = construct(store, state, plan, lock)
        item["bundle_ref"] = keep(store, state, bundle)
        state["claim_states"][args["claim_id"]] = "audit"
    else:
        state["claim_states"][args["claim_id"]] = "bundle_construction"
    return {"outcome": "all_roles_locked", "resource_lock": lock}
