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
# "Cases each grade requires" in evidence-rubric.md owns these numbers.
DIRECT_CASES = 5
DIRECT_GENERATED = 2
EXTERNAL_GENERATED = 1
# The subject produces the answer for these methods; `choice` only asks it to recognise one.
GENERATED_METHODS = {"exact", "numeric", "python"}
# Revisions a claim may spend replacing cases the critique did not count.
REPLACEMENT_ROUNDS = 2
# The installed aggregation rule. It is recorded on every card because `fail` cannot be
# read without it: thirteen passes in fifteen trials is a failure under unanimity and a
# pass under a majority rule. Making this planner-selectable per claim is deliberately
# not done here; it would change an audited tool schema.
AGGREGATION_RULE = "unanimity"
# One round per grade in the rubric. The count is a policy choice bounded by session
# cost, not a derivation; what makes it safe is that a round is only spent on a design
# that actually changed, so the limit bounds real revisions rather than repetition.
MAX_ROUNDS = len(GRADES)
POLICY = {
    "id": "evidence-strength-v4",
    "minimum_cases": MINIMUM_CASES,
    "strong_grade_minimum_trials": STRONG_TRIALS,
    "negotiation_rounds": MAX_ROUNDS,
    "replacement_rounds": REPLACEMENT_ROUNDS,
    "cases": {"A": {"counting": DIRECT_CASES, "generated": DIRECT_GENERATED},
              "B": {"counting": MINIMUM_CASES, "generated": EXTERNAL_GENERATED},
              "C": {"counting": MINIMUM_CASES, "generated": 0},
              "counted": "cases the independent critique gave the verdict counts; before a critique, every case",
              "generated": "methods " + ", ".join(sorted(GENERATED_METHODS)) + "; choice is recognised"},
    "proposal": "each round proposes the current evidence ceiling, or accepts the grade the "
                "last critique of this exact design settled at",
    "grade_limits": "recorded over the cases the critique counted",
    "revision": "a further round requires a changed design; repeating one spends no session",
    "coverage": "every planned trial of every planned case is scored",
    "invalid": "retained in the denominator; status inconclusive; the grade is unaffected",
    "agreement": "unanimous scored status within each case; reported as consistency and fed to "
                 "the aggregation rule, never applied to the grade",
    "aggregation_rule": AGGREGATION_RULE,
    "verdict": "all cases unanimously pass; anything else fails; any invalid inconclusive",
    "status_withheld": "no_reference_grade, synthetic_observations, not_executed, "
                       "unattributable_observations, incomplete_coverage",
    "axes": "grade reports the reference and test bundle only; accuracy, consistency, "
            "completeness and status are recorded separately and none overwrites another",
    "ceiling": "strongest grade supported by recorded evidence facts, lowered by the independent critique",
    "grades": {
        "A": "expected answers independently retrieved by Python, scored by an installed comparison "
             "method, token-exact traceability, three trials; five counting cases, two generated",
        "B": "expected answers from a pinned retrieved or operator-imported dataset, or scored by a "
             "control-tested generated evaluator; three trials; three counting cases, one generated",
        "C": "reproducible indirect comparison; traceability, independence or trial count is weaker; "
             "three counting cases",
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
    expected = answer_text(case)
    if not expected:
        return False
    if expected == case["source_quote"].strip():
        return True
    return bool(re.search(r"(?<![\w.+-])" + re.escape(expected) + r"(?!\w|\.\d)", case["source_quote"]))


def answer_text(case):
    """The answer whose traceability matters: for a choice, the option its index selects.

    A choice records the option number, which is the planner's own ordering and appears
    in no reference. The quoted option behind it is what the grade rests on.
    """
    expected = case["expected"].strip()
    options = [value.strip() for value in case.get("options") or []]
    if not options:
        return expected
    return options[int(expected) - 1] if expected.isdigit() and 1 <= int(expected) <= len(options) else ""


def answer_form(candidate, case):
    """`generated` when the subject must produce the answer, `recognised` when it picks one."""
    from .local_candidates import case_method
    return "generated" if case_method(candidate, case) in GENERATED_METHODS else "recognised"


def case_grade(candidate, counted=None):
    """The strongest grade the counting cases allow, with the reasons it stops there.

    `counted` is the case IDs the critique gave the verdict `counts`; `None` means no
    critique has judged the design yet, so every case is assumed to count. A single-method
    `choice` design has no generated case and cannot pass C; a `mixed` design reaches A
    with two open cases among its five.
    """
    cases = [case for case in candidate["cases"] if counted is None or case["case_id"] in counted]
    generated = sum(answer_form(candidate, case) == "generated" for case in cases)
    reasons = []
    if len(cases) < MINIMUM_CASES:
        reasons.append("insufficient_distinct_cases")
    if len(cases) < DIRECT_CASES:
        reasons.append("fewer_than_five_counting_cases")
    if generated < EXTERNAL_GENERATED:
        reasons.append("no_generated_case")
    elif generated < DIRECT_GENERATED:
        reasons.append("fewer_than_two_generated_cases")
    if len(cases) >= DIRECT_CASES and generated >= DIRECT_GENERATED:
        return "A", reasons
    if len(cases) >= MINIMUM_CASES and generated >= EXTERNAL_GENERATED:
        return "B", reasons
    return ("C" if len(cases) >= MINIMUM_CASES else None), reasons


def evidence_ceiling(candidate, references, trials, counted=None):
    """The strongest grade Python's own recorded facts support, with the reasons it stops there.

    The weaker of what the reference supports and what the counting cases allow.
    """
    origins = [references.get(case["reference_ref"], {}).get("origin") for case in candidate["cases"]]
    pinned = {"retrieved_public_https", "operator_local_resource"}
    # Names the *comparison*, not the subject. The subject of a local run is always a
    # fresh model session and is never deterministic; reading this as a statement about
    # the subject would wrongly make a single trial look sufficient.
    comparison_deterministic = (candidate["method"] in {"exact", "numeric", "choice", "mixed"}
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
    if not comparison_deterministic:
        reasons.append("comparison_not_deterministic")
    if not all(token_exact(case) for case in candidate["cases"]):
        reasons.append("expected_value_not_token_exact_in_source")
    if trials < STRONG_TRIALS:
        reasons.append("model_subject_trial_count_below_three")
    blocking = set(reasons)
    if not blocking:
        reference = "A"
    elif blocking <= {"expected_answers_not_independently_retrieved", "scoring_code_authored_by_planner"}:
        reference = "B"
    elif comparison_deterministic:
        # A previously qualified candidate reused offline keeps a reproducible
        # comparison against its pinned quote even when its origin is unrecorded.
        reference = "C"
    else:
        reference = None
    cases, case_reasons = case_grade(candidate, counted)
    return weaker(reference, cases), sorted(blocking | set(case_reasons))


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


def counted_cases(critique):
    """Case IDs the critique counted, or `None` when no critique judged individual cases."""
    if not critique or critique.get("case_verdicts") is None:
        return None
    return [item["case_id"] for item in critique["case_verdicts"] if item["verdict"] == "counts"]


def rejected_cases(critique):
    """Each case the critique did not count, with its verdict, reason and described replacement."""
    return [item for item in (critique or {}).get("case_verdicts") or [] if item["verdict"] != "counts"]


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
    # Python applies the case count itself, so a critique that rejected cases cannot
    # still settle a grade those rejections leave unsupported.
    counted = counted_cases(critique)
    case_ceiling, case_limits = evidence_ceiling(candidate, references, selection["trials_per_case"], counted)
    settled = weaker(weaker(proposed, supported if supported in ("A", "B", "C") else None), case_ceiling)
    return {
        "kind": "local-plan-audit", "candidate_fingerprint": fingerprint(candidate),
        "selection_digest": digest(canonical(selection)),
        "source_digest": selection["source_digest"],
        "environment_digest": selection["environment_digest"], "scope": claim["scope"],
        "policy": POLICY, "policy_ref": POLICY_REF,
        "proposed_grade": proposed, "evidence_ceiling": ceiling, "evidence_limits": limits,
        "critique": critique, "critique_rounds": rounds, "settled_ceiling": settled,
        "counted_cases": counted if counted is not None else [case["case_id"] for case in candidate["cases"]],
        "case_ceiling": case_ceiling, "case_limits": case_limits,
        "justification": {key: selection[key] for key in PLANNER_JUSTIFICATION},
        "mechanically_accepted": not problems, "problems": problems,
    }


def verdict_for(*, ceiling, synthetic, constant, usable_cases, evaluated, per_case, counts, trials):
    """The ordered status rubric. Returns `(status, withheld_reason)`; first match wins.

    Status answers whether the claim holds, and is kept independent of the grade. Only a
    missing reference gates it, and that dependency is definitional rather than
    qualitative: with nothing to compare against, "did the output match the expected
    answer" has no value at all rather than a weak one. Disagreement between trials does
    not withhold a verdict — it is an input to the aggregation rule, so a flaky skill
    produces a recorded `fail` instead of an absent result.
    """
    if ceiling is None:
        return None, "no_reference_grade"
    if synthetic:
        return None, "synthetic_observations"
    if not evaluated:
        return None, "not_executed"
    if not constant:
        return None, "unattributable_observations"
    if usable_cases < MINIMUM_CASES:
        return None, "incomplete_coverage"
    if counts["invalid"]:
        return "inconclusive", None
    satisfied = all(row["counts"].get("pass", 0) == trials for row in per_case)
    return ("pass" if satisfied else "fail"), None


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
    # The grade reports the reference and the test bundle, both settled before any trial
    # ran, so nothing observed during execution may move it. A skill that fails every
    # case against a gold-standard oracle keeps its grade: the evidence is exactly as
    # strong, it simply refutes the claim. A synthetic run has no real reference at all.
    grade = ceiling if (ceiling and not synthetic) else None
    evaluated = len(observations)
    status, withheld = verdict_for(ceiling=ceiling, synthetic=synthetic, constant=constant,
                                   usable_cases=len(per_case), evaluated=evaluated,
                                   per_case=per_case, counts=counts, trials=trials)
    # Two lists, never merged: a reader must be able to tell a weak reference from a
    # wobbling skill without reading the raw trials.
    # The limits over the cases the critique counted, so a grade lowered by rejected cases
    # says why. An audit written before case verdicts existed has only the proposal's.
    grade_reasons = list(audit_record.get("case_limits", audit_record["evidence_limits"]))
    if ceiling is None:
        grade_reasons.append("no_supported_execution_grade")
    if synthetic:
        grade_reasons.append("synthetic_observations")
    execution_reasons = []
    if counts["invalid"]:
        execution_reasons.append("invalid_observations_retained")
    if any(row["agreement"] < 1 for row in per_case):
        execution_reasons.append("trial_agreement_below_policy")
    if not constant:
        execution_reasons.append("observed_model_identity_changed")
    unanimous = sum(1 for row in per_case if row["agreement"] == 1)
    return {
        "scientific_status": status, "status_withheld_reason": withheld,
        "evidence_grade": grade,
        "achieved_grade_ceiling": grade, "grade_policy_ref": audit_record["policy_ref"],
        "proposed_grade": audit_record["proposed_grade"],
        "aggregation_rule": AGGREGATION_RULE, "fault": None,
        # Named for the audit field it copies. `evidence_ceiling` in the audit is the
        # mechanical ceiling; reusing that name here for a different value would mislead.
        "settled_ceiling": ceiling, "grade_limit_reasons": sorted(set(grade_reasons)),
        "execution_limit_reasons": sorted(set(execution_reasons)),
        "accuracy": {"matched": counts["pass"], "evaluated": evaluated,
                     "ratio": round(counts["pass"] / evaluated, 4) if evaluated else None},
        # With no counted case there is no agreement to report; `unanimous` would claim one.
        "consistency": {"label": "no_counted_cases" if not per_case
                        else "unanimous" if unanimous == len(per_case) else "split",
                        "overall_agreement": round(sum(row["agreement"] for row in per_case) / len(per_case), 4)
                        if per_case else None,
                        "unanimous_cases": unanimous, "split_cases": len(per_case) - unanimous},
        "completeness": {"obtained": evaluated, "planned": planned,
                         "usable_cases": len(per_case), "planned_cases": len(cases)},
        "next_target_grade": None if grade else "D",
        "trial_counts": {"planned": planned, "attempted": planned, "obtained": evaluated,
                         "evaluated": evaluated, "invalid": counts["invalid"], "missing": 0},
        "case_agreement": per_case, "observed_model_ids": models,
        "ai_involvement": {
            "orchestration": True,
            "evidence_generation": "The planner selected the cases; every expected answer is quoted from "
                                   + ("a reference Python retrieved." if audit_record["evidence_ceiling"] == "A"
                                      else "a pinned source, not produced by AI."),
            "verdict": False,
        },
    }
