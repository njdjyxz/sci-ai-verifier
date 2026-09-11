"""Authorize only an exact, complete plan and its pinned scientific method."""

from .common import Fault, canonical, digest
from .evaluation import construct
from .planning import artifact, keep, parent, operational
from .scientific import METHOD, POLICY, method_current


def audit_plan(store, state, args):
    item, plan = parent(store, state, args)
    lock = store.get_json(item["lock_ref"]) if item["lock_ref"] else None
    if lock is None or args["resource_lock_id"] != lock["id"]:
        raise Fault("stale_lock", "Use this plan revision's resource lock.", ["resource_lock_id"])
    for field in ("scope_finding", "fairness_finding"):
        if args[field] not in {"supported", "unsupported", "uncertain"}:
            raise Fault("invalid_finding", "Findings must be supported, unsupported or uncertain.", [field])
    if args["proposed_status"] not in {"pass", "fail"}:
        raise Fault("invalid_audit_proposal", "Propose pass or fail.", ["proposed_status"])
    if not method_current(state):
        return operational(store, state, args["claim_id"], "implementation_required",
                           "Installed method changed since run creation; start a new run.")
    expected = construct(store, state, plan, lock)
    bundle = store.get_json(item["bundle_ref"])
    if (bundle["plan_id"] != plan["id"] or bundle["resource_lock_id"] != lock["id"]
            or bundle["cases"] != expected["cases"] or plan["method"] != METHOD
            or plan["policy_ref"] != digest(canonical(POLICY))
            or plan["subject_config"] != state["subject_config"]):
        raise Fault("audit_parent_integrity", "Plan, lock, bundle, method or subject binding is inconsistent.", fatal=True)
    passed = args["scope_finding"] == args["fairness_finding"] == "supported"
    audit = artifact(state, "audit", args["claim_id"], plan_id=plan["id"], plan_revision=plan["revision"],
                     plan_ref=item["plan_ref"], lock_ref=item["lock_ref"], bundle_ref=item["bundle_ref"],
                     method_ref=state["method_ref"], policy_ref=plan["policy_ref"],
                     audit_status="pass" if passed else "fail", proposed_status=args["proposed_status"],
                     proposal_agreed=(args["proposed_status"] == ("pass" if passed else "fail")),
                     scope_finding=args["scope_finding"], fairness_finding=args["fairness_finding"],
                     limitations=args["limitations"], grade_ceiling=plan["planned_grade"],
                     objective_checks=["exact_parents", "resource_digests", "separate_expected_answers",
                                       "fixed_method_policy", "bounded_subject_config", "nonempty_cases"])
    if passed and item["registration_ref"]:
        registration = store.get_json(item["registration_ref"])
        promoted = artifact(state, "registration", args["claim_id"], status="validated",
                            previous_ref=item["registration_ref"], selection_id=plan["selection_id"],
                            capability=plan["capability"], method=plan["method"],
                            bundle_ref=item["bundle_ref"], policy_ref=plan["policy_ref"],
                            original_validation_ref=registration.get("validation_ref"),
                            scope="runtime_only")
        item["registration_ref"] = keep(store, state, promoted)
        audit["promotion_ref"] = item["registration_ref"]
        audit["id"] = "audit-" + digest(canonical({k: v for k, v in audit.items() if k != "id"}))
    item["audit_ref"] = keep(store, state, audit)
    state["claim_states"][args["claim_id"]] = "execution" if passed else "planning"
    return {"outcome": "audit_passed" if passed else "plan_revision_required", "audit": audit}
