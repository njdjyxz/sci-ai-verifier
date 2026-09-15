"""Evidence-strength grading: mechanical ceilings settled against an independent critique.

The grade is an indicator of how close the evidence is to a gold standard, not an
approval. A means Python compared the subject against independently retrieved
expected answers; D means the conclusion rests on AI judgment over cited sources.
Python computes the strongest grade its own recorded facts can support, a fresh
critique session may only lower that, and the planner may revise its design and
propose again. No human sign-off is required and none is implied.
"""

import re
from collections import Counter

from .common import Fault, canonical, digest
from .storage import implementation_bytes

ORDER = ("A", "B", "C", "D")
GRADES = ("A", "B", "C", "D", "U")
MINIMUM_CASES = 3
STRONG_TRIALS = 3
# One round per grade in the rubric. The count is a policy choice bounded by session
# cost, not a derivation; what makes it safe is that a round is only spent on a design
# that actually changed, so the limit bounds real revisions rather than repetition.
MAX_ROUNDS = len(GRADES)
POLICY = {
    "id": "evidence-strength-v2",
    "minimum_cases": MINIMUM_CASES,
    "strong_grade_minimum_trials": STRONG_TRIALS,
    "negotiation_rounds": MAX_ROUNDS,
    "proposal": "each round proposes the current evidence ceiling, or accepts the grade the "
                "last critique of this exact design supported",
    "revision": "a further round requires a changed design; repeating one spends no session",
    "coverage": "every planned trial of every planned case is scored",
    "invalid": "retained in the denominator; no execution grade",
    "agreement": "unanimous scored status within each case",
    "verdict": "all pass; any fail; any invalid inconclusive",
    "ceiling": "strongest grade supported by recorded evidence facts, lowered by the independent critique",
    "grades": {
        "A": "expected answers independently retrieved by Python, scored by an installed comparison "
             "method, token-exact traceability, at least three cases and three trials",
        "B": "expected answers from a pinned retrieved or operator-imported dataset, or scored by a "
             "control-tested generated evaluator; at least three cases and three trials",
        "C": "reproducible indirect comparison; traceability, independence or trial count is weaker",
        "D": "documentary assessment of cited sources against the fixed rubric; no execution accuracy",
    },
}
POLICY_REF = digest(canonical(POLICY))
PLANNER_JUSTIFICATION = ("oracle_independence", "coverage", "tolerance_basis",
                         "uncertainty", "stronger_grade_considered")


def weaker(first, second):
    """Return the weaker of two grades. Anything unrecognized means no supportable grade.

    Settling always moves down: a value this module does not recognize must never
    become a grade, so it collapses to `None` rather than raising mid-transition.
    """
    if first not in ORDER or second not in ORDER:
        return None
    return first if ORDER.index(first) >= ORDER.index(second) else second


def fingerprint(candidate):
    if candidate["method"] == "python":
        return candidate["specification_ref"]
    keys = ("name", "scope", "method", "limitations", "cases", "absolute_tolerance", "method_version")
    return digest(canonical({key: candidate[key] for key in keys}))


def environment_digest(settings, subject):
    runner = subject["adapter_id"]
    if re.fullmatch(r"[0-9a-f]{64}", runner.rsplit("-", 1)[-1]):
        runner = runner.rsplit("-", 1)[0]
    return digest(canonical({"model_requested": subject["model_id"], "runner": runner,
                             "runtime_digest": digest(implementation_bytes()), "settings": settings}))


def token_exact(case):
    """True when the expected answer is a complete token of its reference quote.

    A substring match lets `1.0` be read out of `21.09`, so a substring supports
    only indirect evidence. Numeric qualification already requires this; the check
    is repeated here because exact-match and generated evaluators do not.
    """
    expected = case["expected"].strip()
    if not expected:
        return False
    if expected == case["source_quote"].strip():
        return True
    return bool(re.search(r"(?<![\w.+-])" + re.escape(expected) + r"(?!\w|\.\d)", case["source_quote"]))


def evidence_ceiling(candidate, references, trials):
    """The strongest grade Python's own recorded facts support, with the reasons it stops there."""
    origins = [references.get(case["reference_ref"], {}).get("origin") for case in candidate["cases"]]
    pinned = {"retrieved_public_https", "operator_local_resource"}
    deterministic = (candidate["method"] in {"exact", "numeric"}
                     or all(item["passed"] for item in candidate.get("controls_receipts", [])))
    reasons = []
    if any(origin not in pinned for origin in origins):
        reasons.append("reference_origin_unknown")
    if any(origin != "retrieved_public_https" for origin in origins):
        reasons.append("expected_answers_not_independently_retrieved")
    if candidate["method"] == "python":
        # Direct validation requires that no AI judgment enters scoring. A generated
        # scorer is reproducible and control-tested, but the planner wrote the rule.
        reasons.append("scoring_code_authored_by_planner")
    if not deterministic:
        reasons.append("comparison_not_deterministic")
    if not all(token_exact(case) for case in candidate["cases"]):
        reasons.append("expected_value_not_token_exact_in_source")
    if len(candidate["cases"]) < MINIMUM_CASES:
        reasons.append("insufficient_distinct_cases")
    if trials < STRONG_TRIALS:
        reasons.append("model_subject_trial_count_below_three")
    blocking = set(reasons)
    if not blocking:
        ceiling = "A"
    elif blocking <= {"expected_answers_not_independently_retrieved", "scoring_code_authored_by_planner"}:
        ceiling = "B"
    elif deterministic and len(candidate["cases"]) >= MINIMUM_CASES:
        # A previously qualified candidate reused offline keeps a reproducible
        # comparison against its pinned quote even when its origin is unrecorded.
        ceiling = "C"
    else:
        ceiling = None
    return ceiling, sorted(blocking)


def proposal_problem(target, ceiling, accepted=None):
    """Why a proposal is refused, or `None` when it is allowed.

    Exactly two proposals are legal for any design: the ceiling its recorded facts
    support, or the grade the last critique of that same design supported. Anything
    above the ceiling overclaims; anything else below it aims low to look cautious,
    which misreports the evidence just as badly. Callers report the reason as an
    ordinary outcome, so neither mistake spends the run's repair budget.
    """
    if target not in ("A", "B", "C"):
        raise Fault("grade_proposal_invalid", "Propose target grade A, B or C for an execution plan.",
                    ["target_grade"])
    if ceiling is None:
        return "no_supported_execution_grade"
    if ORDER.index(target) < ORDER.index(ceiling):
        return "above_evidence_ceiling"
    if target != ceiling and target != accepted:
        return "below_evidence_ceiling"
    return None


def audit(candidate, claim, settings, selection, references, *, critique=None, rounds=1):
    """Freeze the plan, its evidence ceiling and the critique that settled the grade."""
    problems = []
    if len(candidate["cases"]) < MINIMUM_CASES:
        problems.append("insufficient_distinct_cases")
    if selection["trials_per_case"] * len(candidate["cases"]) > settings["max_subject_calls"]:
        problems.append("plan_exceeds_call_budget")
    ceiling, limits = evidence_ceiling(candidate, references, selection["trials_per_case"])
    proposed = selection["target_grade"]
    # A critique answering D says this execution design supports no execution grade.
    # D is established by the documentary path, never by a comparison record.
    supported = critique["supported_grade"] if critique else None
    settled = weaker(proposed, supported if supported in ("A", "B", "C") else None)
    return {
        "kind": "local-plan-audit", "candidate_fingerprint": fingerprint(candidate),
        "selection_digest": digest(canonical(selection)),
        "source_digest": selection["source_digest"],
        "environment_digest": selection["environment_digest"], "scope": claim["scope"],
        "policy": POLICY, "policy_ref": POLICY_REF,
        "proposed_grade": proposed, "evidence_ceiling": ceiling, "evidence_limits": limits,
        "critique": critique, "critique_rounds": rounds, "settled_ceiling": settled,
        "justification": {key: selection[key] for key in PLANNER_JUSTIFICATION},
        "mechanically_accepted": not problems, "problems": problems,
    }


def decide(audit_record, observations, cases, trials, *, synthetic=False):
    """Apply the installed policy to scored trials. The planner cannot change this outcome."""
    planned = len(cases) * trials
    expected = {(case["case_id"], trial) for case in cases for trial in range(1, trials + 1)}
    obtained = [(row["case_id"], row["trial"]) for row in observations]
    if len(obtained) != len(set(obtained)) or set(obtained) != expected:
        raise Fault("incomplete_trial_set", "Missing or duplicate trial observations cannot become a scientific verdict.")
    statuses = [row["comparison_status"] for row in observations]
    if not set(statuses) <= {"pass", "fail", "invalid"}:
        raise Fault("score_invalid", "Scored trials contain an unknown outcome.")
    counts = Counter(statuses)
    per_case = []
    for case in cases:
        values = Counter(row["comparison_status"] for row in observations if row["case_id"] == case["case_id"])
        per_case.append({"case_id": case["case_id"], "planned": trials, "obtained": sum(values.values()),
                         "counts": dict(values), "agreement": max(values.values()) / trials})
    models = sorted({model for row in observations for model in row.get("model_ids", [])})
    constant = len({tuple(sorted(row.get("model_ids", []))) for row in observations}) == 1
    ceiling = audit_record["settled_ceiling"]
    supported = bool(ceiling) and constant and not synthetic and not counts["invalid"] \
        and len(cases) >= MINIMUM_CASES and all(row["agreement"] == 1 for row in per_case)
    grade = ceiling if supported else None
    verdict = "inconclusive" if counts["invalid"] else "fail" if counts["fail"] else "pass"
    reasons = list(audit_record["evidence_limits"])
    if ceiling is None:
        reasons.append("no_supported_execution_grade")
    if synthetic:
        reasons.append("synthetic_observations")
    if counts["invalid"]:
        reasons.append("invalid_observations_retained")
    if any(row["agreement"] < 1 for row in per_case):
        reasons.append("trial_agreement_below_policy")
    if not constant:
        reasons.append("observed_model_identity_changed")
    return {
        "scientific_status": verdict if grade else None, "evidence_grade": grade,
        "achieved_grade_ceiling": grade, "grade_policy_ref": audit_record["policy_ref"],
        "proposed_grade": audit_record["proposed_grade"],
        # Named for the audit field it copies. `evidence_ceiling` in the audit is the
        # mechanical ceiling; reusing that name here for a different value would mislead.
        "settled_ceiling": ceiling, "grade_limit_reasons": sorted(set(reasons)),
        "next_target_grade": None if grade else "D",
        "trial_counts": {"planned": planned, "attempted": planned, "obtained": len(observations),
                         "evaluated": len(observations), "invalid": counts["invalid"], "missing": 0},
        "case_agreement": per_case, "observed_model_ids": models,
        "ai_involvement": {
            "orchestration": True,
            "evidence_generation": "The planner selected the cases; every expected answer is quoted from "
                                   + ("a reference Python retrieved." if audit_record["evidence_ceiling"] == "A"
                                      else "a pinned source, not produced by AI."),
            "verdict": False,
        },
    }
