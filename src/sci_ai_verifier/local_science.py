"""Evidence-strength grading: mechanical ceilings settled against an independent critique.

The grade is an indicator of how close the evidence is to a gold standard, not an
approval. A means Python compared the subject against expected values it built from, or
quoted out of, independently retrieved references; D means the conclusion rests on AI
judgment over cited sources. Python computes the strongest grade its own recorded facts
can support, a fresh critique session may only lower that, and the planner may revise its
design and propose again. No human sign-off is required and none is implied.
"""

import re
from collections import Counter

from .common import Fault, canonical, digest
from .storage import implementation_bytes

ORDER = ("A", "B", "C", "D")
GRADES = ("A", "B", "C", "D", "U")
STRONG_TRIALS = 3
# "Cases each grade requires" in evidence-rubric.md owns these numbers. A case is a task: it runs the
# skill on its input and is checked on every output (local-tasks.md).
TASK_DIRECT = 3
TASK_MINIMUM = 2
# Reasons a design's task count gives; every other limiting reason is the reference's or the trials'.
CASE_REASONS = {"fewer_than_two_counting_tasks", "fewer_than_three_counting_tasks"}
# Reasons that keep a reference out of A but still allow B.
EXTERNAL_REASONS = {"expected_answers_not_independently_retrieved"}
# Revisions a claim may spend replacing tasks the critique did not count.
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
    "id": "evidence-strength-v9",
    "minimum_tasks": TASK_MINIMUM,
    "strong_grade_minimum_trials": STRONG_TRIALS,
    "negotiation_rounds": MAX_ROUNDS,
    "replacement_rounds": REPLACEMENT_ROUNDS,
    "tasks": {"A": TASK_DIRECT, "B": TASK_MINIMUM, "C": TASK_MINIMUM,
              "counted": "tasks the independent critique gave the verdict counts; before a critique, every task"},
    "proposal": "each round proposes the current evidence ceiling, or accepts the grade the "
                "last critique of this exact design settled at",
    "grade_limits": "recorded over the tasks the critique counted",
    "revision": "a further round requires a changed design; repeating one spends no session",
    "coverage": "every planned trial of every planned task is scored",
    "invalid": "retained in the denominator; status inconclusive unless a trial failed; the grade is unaffected",
    "agreement": "unanimous scored status within each task; reported as consistency and fed to "
                 "the aggregation rule, never applied to the grade",
    "aggregation_rule": AGGREGATION_RULE,
    "verdict": "all tasks unanimously pass; any failed trial fails, whatever the others; otherwise any invalid "
               "trial is inconclusive",
    "reading": "Python reads each trial's results file and checks every output; no AI reads a trial",
    "status_withheld": "no_reference_grade, synthetic_observations, not_executed, "
                       "unattributable_observations, incomplete_coverage",
    "axes": "grade reports the reference and test bundle only; accuracy, consistency, "
            "completeness and status are recorded separately and none overwrites another",
    "ceiling": "strongest grade supported by recorded evidence facts, lowered by the independent critique",
    "grades": {
        "A": "expected values planted by Python in task files from a model quoted token-exactly from a reference "
             "Python retrieved, and recovered by the reference solution, or quoted token-exactly from such a "
             "reference; scored by a task's fixed checks; three trials; three counting tasks",
        "B": "expected values quoted from an operator-imported pinned dataset; three trials; two counting tasks",
        "C": "reproducible comparison whose references are weaker, such as a design reused offline whose "
             "reference origin was never recorded; two counting tasks",
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
    """A design's identity: its tasks and the programs that build and check them."""
    keys = ("name", "scope", "method", "limitations", "cases", "method_version", "generator", "solver")
    return digest(canonical({key: candidate[key] for key in keys if key in candidate}))


def environment_digest(settings, subject, environment=None):
    runner = subject["adapter_id"]
    if re.fullmatch(r"[0-9a-f]{64}", runner.rsplit("-", 1)[-1]):
        runner = runner.rsplit("-", 1)[0]
    pinned = {"model_requested": subject["model_id"], "runner": runner,
              "runtime_digest": digest(implementation_bytes()), "settings": settings}
    if environment:
        # The runner suffix stripped above carries the subject image; the record replaces it.
        pinned["environment"] = environment
    return digest(canonical(pinned))


def case_grade(candidate, counted=None):
    """The strongest grade the counting tasks allow, with the reasons it stops there.

    `counted` is the task IDs the critique gave the verdict `counts`; `None` means no critique
    has judged the design yet, so every task is assumed to count.
    """
    cases = [case for case in candidate["cases"] if counted is None or case["case_id"] in counted]
    reasons = (["fewer_than_two_counting_tasks"] if len(cases) < TASK_MINIMUM else []) + (
        ["fewer_than_three_counting_tasks"] if len(cases) < TASK_DIRECT else [])
    return ("A" if len(cases) >= TASK_DIRECT else "B" if len(cases) >= TASK_MINIMUM else None), reasons


def evidence_ceiling(candidate, references, trials, counted=None):
    """The strongest grade Python's own recorded facts support, with the reasons it stops there.

    The weaker of what the references support and what the counting tasks allow.
    """
    from .local_candidates import reference_refs
    from .local_tasks import traceable
    origins = [references.get(ref, {}).get("origin") for ref in reference_refs(candidate)]
    pinned = {"retrieved_public_https", "operator_local_resource"}
    reasons = []
    if any(origin not in pinned for origin in origins):
        reasons.append("reference_origin_unknown")
    if any(origin != "retrieved_public_https" for origin in origins):
        reasons.append("expected_answers_not_independently_retrieved")
    if not all(traceable(candidate, case) for case in candidate["cases"]):
        reasons.append("expected_value_not_token_exact_in_source")
    # Names the subject's trial count: a local subject is always a fresh model session and is
    # never deterministic, so a single trial cannot tell a right skill from a sometimes-right one.
    if trials < STRONG_TRIALS:
        reasons.append("model_subject_trial_count_below_three")
    cases, case_reasons = case_grade(candidate, counted)
    return weaker(reference_grade(reasons), cases), sorted(set(reasons) | set(case_reasons))


def reference_grade(reasons):
    """The grade the reference and trial facts alone support, whatever the tasks: the first half of
    `evidence_ceiling`, which also reads it back from a recorded audit's limiting reasons."""
    blocking = set(reasons) - CASE_REASONS
    if not blocking:
        return "A"
    if blocking <= EXTERNAL_REASONS:
        return "B"
    return "C"


def size_limit(audit_record, candidate):
    """How the number of independent tasks alone held a claim below its source's grade, or `None`."""
    source = reference_grade(audit_record.get("evidence_limits") or [])
    settled = audit_record.get("settled_ceiling")
    if (source is None or "case_ceiling" not in audit_record or audit_record["case_ceiling"] != settled
            or (settled is not None and ORDER.index(settled) <= ORDER.index(source))
            or not set(audit_record.get("case_limits") or []) & CASE_REASONS):
        return None
    cases = [case for case in candidate["cases"] if case["case_id"] in audit_record["counted_cases"]]
    return {"source_supports": source, "settled": settled, "unit": "tasks", "counting": len(cases),
            "counting_needed": POLICY["tasks"][source]}


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
    """Task IDs the critique counted, or `None` when no critique judged individual tasks."""
    if not critique or critique.get("case_verdicts") is None:
        return None
    return [item["case_id"] for item in critique["case_verdicts"] if item["verdict"] == "counts"]


def rejected_cases(critique):
    """Each task that does not count, in task order, with its verdict, reason and described replacement."""
    return [item for item in (critique or {}).get("case_verdicts") or [] if item["verdict"] != "counts"]


def case_gap(candidate, counted, grade, supported):
    """What `grade`'s task requirement still lacks over the counted tasks, in numbers and words.

    Run 31b67427's planner accepted B one counting case short of A, believing it lacked an
    open case it already had. Python holds the count, so it states it, and says when the
    critique's own grade is a limit as well.
    """
    cases = [case for case in candidate["cases"] if counted is None or case["case_id"] in counted]
    need = POLICY["tasks"][grade]
    more = max(0, need - len(cases))
    if more:
        summary = (grade + " needs at least " + str(need) + " counting tasks. This design has " + str(len(cases))
                   + " counted: add at least " + str(more) + " more task" + ("" if more == 1 else "s") + ".")
        if weaker(grade, supported) != grade:
            summary += (" The critique's own grade is " + str(supported or "none")
                        + ", so its objections need answering as well.")
    else:
        summary = ("This design's " + str(len(cases)) + " counted tasks meet " + grade + "'s requirement. The "
                   "critique's own grade, " + str(supported or "none") + ", is what holds the settled grade down, "
                   "so its objections are what to answer.")
    return {"grade": grade, "tasks_required": need, "tasks_counted": len(cases), "tasks_needed": more,
            "summary": summary}


def audit(candidate, claim, settings, selection, references, *, critique=None, rounds=1):
    """Freeze the plan, its evidence ceiling and the critique that settled the grade."""
    problems = []
    if len(candidate["cases"]) < TASK_MINIMUM:
        problems.append("insufficient_distinct_cases")
    if selection["trials_per_case"] * len(candidate["cases"]) > settings["max_subject_calls"]:
        problems.append("plan_exceeds_call_budget")
    ceiling, limits = evidence_ceiling(candidate, references, selection["trials_per_case"])
    proposed = selection["target_grade"]
    # A critique answering D says this execution design supports no execution grade.
    # D is established by the documentary path, never by a comparison record.
    supported = critique["supported_grade"] if critique else None
    # Python applies the task count itself, so a critique that rejected tasks cannot
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


def verdict_for(*, ceiling, synthetic, constant, usable_cases, evaluated, per_case, counts, trials,
                minimum=TASK_MINIMUM):
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
    if usable_cases < minimum:
        return None, "incomplete_coverage"
    # Under unanimity one wrong result already decides the claim, whatever an unreadable trial
    # would have said (operator, 2026-10-05). Only with no wrong result does one leave it open.
    if counts["fail"]:
        return "fail", None
    if counts["invalid"]:
        return "inconclusive", None
    satisfied = all(row["counts"].get("pass", 0) == trials for row in per_case)
    return ("pass" if satisfied else "fail"), None


def tallies(observations, cases, trials):
    """Each task's statuses and agreement, and the overall counts."""
    statuses = [row["comparison_status"] for row in observations]
    if not set(statuses) <= {"pass", "fail", "invalid"}:
        raise Fault("score_invalid", "Scored trials contain an unknown outcome.")
    per_case = []
    for case in cases:
        values = Counter(row["comparison_status"] for row in observations if row["case_id"] == case["case_id"])
        per_case.append({"case_id": case["case_id"], "planned": trials, "obtained": sum(values.values()),
                         "counts": dict(values), "agreement": max(values.values()) / trials})
    return per_case, Counter(statuses)


def decide(audit_record, observations, cases, trials, *, synthetic=False):
    """Apply the installed policy to scored trials. The planner cannot change this outcome."""
    planned = len(cases) * trials
    expected = {(case["case_id"], trial) for case in cases for trial in range(1, trials + 1)}
    obtained = [(row["case_id"], row["trial"]) for row in observations]
    if len(obtained) != len(set(obtained)) or set(obtained) != expected:
        raise Fault("incomplete_trial_set", "Missing or duplicate trial observations cannot become a scientific verdict.")
    per_case, counts = tallies(observations, cases, trials)
    models = sorted({model for row in observations for model in row.get("model_ids", [])})
    constant = len({tuple(sorted(row.get("model_ids", []))) for row in observations}) == 1
    ceiling = audit_record["settled_ceiling"]
    # The grade reports the reference and the test bundle, both settled before any trial
    # ran, so nothing observed during execution may move it. A skill that fails every
    # task against a gold-standard oracle keeps its grade: the evidence is exactly as
    # strong, it simply refutes the claim. A synthetic run has no real reference at all.
    grade = ceiling if (ceiling and not synthetic) else None
    evaluated = len(observations)
    status, withheld = verdict_for(ceiling=ceiling, synthetic=synthetic, constant=constant,
                                   usable_cases=len(per_case), evaluated=evaluated,
                                   per_case=per_case, counts=counts, trials=trials)
    # Two lists, never merged: a reader must be able to tell a weak reference from a
    # wobbling skill without reading the raw trials. The limits are over the tasks the
    # critique counted, so a grade lowered by rejected tasks says why.
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
    sourced = ("a reference Python retrieved." if audit_record["evidence_ceiling"] == "A"
               else "a pinned source, not produced by AI.")
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
        # With no counted task there is no agreement to report; `unanimous` would claim one.
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
        "ai_involvement": {"orchestration": True, "evidence_generation": task_generation(cases, sourced),
                           # Python's fixed checks read every trial; no AI judges a result.
                           "verdict": False},
    }


def task_generation(cases, sourced):
    """What a task design's expected values rest on, for the result's AI-involvement disclosure."""
    outputs = [output for case in cases for output in case["outputs"]]
    planted = sum(output.get("source") == "planted" for output in outputs)
    text = ("The planner designed the tasks, wrote the generator that built their input files and the reference "
            "solution that checked them, and chose the tolerances. ")
    if planted:
        text += (str(planted) + " of the " + str(len(outputs)) + " checked values were planted by Python, which ran "
                 "that generator on a model quoted from " + sourced[:-1] + "; a planted judgment, such as whether a "
                 "problem is present, also quotes the rule it follows. ")
    if planted < len(outputs):
        text += ("The other values are" if planted else "Every expected value is") + " quoted from " + sourced
    return text.strip()
