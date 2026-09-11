"""Build and validate a bounded bundle without caller-authored transformations."""

from .common import Fault, canonical, digest
from .planning import artifact, keep, parent
from .scientific import mass


def construct(store, state, plan, lock):
    if lock["plan_id"] != plan["id"] or lock["plan_revision"] != plan["revision"] or not lock["complete"]:
        raise Fault("stale_lock", "Resource lock must belong to this exact plan revision.", ["resource_lock_id"])
    bound = {entry["id"]: entry["sha256"] for entry in lock["bindings"]}
    reference = store.get_json(bound["nist-chnops-isotopes"])
    specification = store.get_json(bound["chemical-pilot-cases"])
    if specification["scope"] != plan["scope"]:
        raise Fault("bundle_scope", "Bundle scope differs from the committed plan.", fatal=True)
    formulas = specification["formulas"]
    if not formulas or len(formulas) != len(set(formulas)) or formulas != state["case_formulas"]:
        raise Fault("bundle_invalid", "Installed cases must be nonempty, unique and pinned.", fatal=True)
    cases = [{"case_id": "case-" + digest(formula.encode()), "input": {"formula": formula},
              "expected_mass_da": str(mass(formula, reference))} for formula in formulas]
    return artifact(state, "bundle", plan["claim_id"], plan_id=plan["id"], plan_revision=plan["revision"],
                    resource_lock_id=lock["id"], resource_lock_ref=keep(store, state, lock),
                    cases=cases, grade_ceiling=plan["planned_grade"], coverage=specification["coverage"],
                    exclusions="Other elements, isotopic labels, charges, groups, hydrates and untested formulas",
                    expected_answers_separate=True, policy_ref=plan["policy_ref"])


def build(store, state, args):
    item, plan = parent(store, state, args)
    if not item["lock_ref"]:
        raise Fault("lock_missing", "Materialize resources first.", ["plan_id"])
    bundle = construct(store, state, plan, store.get_json(item["lock_ref"]))
    item["bundle_ref"] = keep(store, state, bundle)
    return {"outcome": "bundle_candidate_built", "bundle_id": bundle["id"], "case_count": len(bundle["cases"])}


def validate_bundle(store, state, args):
    item, plan = parent(store, state, args)
    if not item["bundle_ref"]:
        raise Fault("bundle_missing", "Build the bundle first.", ["bundle_id"])
    bundle = store.get_json(item["bundle_ref"])
    if args["bundle_id"] != bundle["id"]:
        raise Fault("stale_bundle", "Use this plan's current bundle.", ["bundle_id"])
    rebuilt = construct(store, state, plan, store.get_json(item["lock_ref"]))
    if bundle["cases"] != rebuilt["cases"] or not bundle["expected_answers_separate"]:
        raise Fault("bundle_invalid", "Bundle content differs from locked resources.", fatal=True)
    validation = artifact(state, "validation", args["claim_id"], plan_id=plan["id"],
                          bundle_id=bundle["id"], bundle_ref=item["bundle_ref"], adequate=True,
                          checks=["unique_nonempty_cases", "locked_oracle", "input_answer_separation"],
                          grade_ceiling=plan["planned_grade"])
    item["validation_ref"] = keep(store, state, validation)
    state["claim_states"][args["claim_id"]] = "provisional_registration"
    return {"outcome": "bundle_adequate", "validation": validation}


def register(store, state, args):
    item, plan = parent(store, state, args)
    validation = store.get_json(item["validation_ref"])
    if args["bundle_id"] != validation["bundle_id"] or not validation["adequate"]:
        raise Fault("stale_bundle", "Use the validated bundle.", ["bundle_id"])
    registration = artifact(state, "registration", args["claim_id"], status="provisional",
                            selection_id=plan["selection_id"], capability=plan["capability"],
                            method=plan["method"], bundle_ref=item["bundle_ref"],
                            validation_ref=item["validation_ref"], policy_ref=plan["policy_ref"])
    item["registration_ref"] = keep(store, state, registration)
    state["claim_states"][args["claim_id"]] = "planning"
    return {"outcome": "provisional_evaluator_registered", "registration": registration}
