"""Test doubles for the two independent sessions, built through the real validators.

Not collected by discovery: this module holds helpers, not tests.

Every test that exercises grade negotiation or the documentary path patches out
`documentary.critique_tasks` or `documentary.assess` — the two functions that contain
`validate_task_critique` and `validate_assessment`. A double that returns a hand-written
dict therefore proves only that the test author and the consuming code agree; it can
never notice that the validator and a real session disagree. That blind spot is how
`critic_response_invalid` reached local run a392ea65 and discarded three completed
critiques while 215 tests passed.

So every double here is built by calling the real validator. A test that invents a
reply the runtime would refuse now fails as it is written, and the key set each double
returns is the key set the real function returns, so report fields derived from these
records are exercised rather than silently absent.

Replies a real session actually sent live in `tests/recorded/`; see
`test_recorded_replies.py`. A double gives its reply in the reply schema's shape, task
verdicts keyed by case ID, exactly as Claude Code returns it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.common import canonical, digest
from sci_ai_verifier.documentary import (RUBRIC, RUBRIC_REF, TASK_CRITIQUE_REF, TASK_CRITIQUE_RUBRIC,
    TASK_QUESTIONS, validate_assessment, validate_task_critique)

INDEPENDENCE = "fresh host-selected no-tool session; no planner conversation"


def _envelope(packet, rubric_ref, role):
    """The provenance fields both real functions attach to every reply."""
    return {"session_id": "fixture-" + role, "observed_model_ids": ["fixture-model"],
            "packet_ref": digest(canonical(packet)), "rubric_ref": rubric_ref,
            "usage": None, "total_cost_usd": None,
            "independence": INDEPENDENCE, "ai_judgment": True}


def critic_reply(packet, supported, *, findings=None, objections=(), required_revisions=(), rejected=None,
                 coverage_gaps=(), departures=(), criteria=None, unsourced_rules=()):
    """Shaped exactly as `documentary.critique_tasks` returns, including the "none" -> None mapping.

    Every task in the packet counts unless `rejected` maps its case ID to another verdict, which the reply gives
    by answering yes to the first question of that verdict; `criteria` maps a case ID to the rule its job gives
    that the claim's sections do not; `unsourced_rules` lists (rule, reason) pairs.
    """
    rejected, criteria = rejected or {}, criteria or {}
    case_ids = [case["case_id"] for case in packet["evidence"]["tasks"]]

    def check(key):
        first = next((question for question, verdict, _ in TASK_QUESTIONS if verdict == rejected.get(key)), None)
        return {**{question: {"answer": "yes" if question == first else "no", "reason": "Fixture answer."}
                   for question, _, _ in TASK_QUESTIONS},
                "criterion_given": criteria.get(key, ""),
                "replacement": "Fixture replacement: a task inside the claim." if first else ""}
    value = validate_task_critique({
        "supported_grade": supported,
        "findings": list(findings) if findings else ["Fixture critique finding."] * len(TASK_CRITIQUE_RUBRIC["criteria"]),
        "objections": list(objections), "required_revisions": list(required_revisions),
        "coverage_gaps": list(coverage_gaps), "departures": list(departures),
        "unsourced_rules": [{"rule": rule, "reason": reason} for rule, reason in unsourced_rules],
        "task_checks": {key: check(key) for key in case_ids}},
        case_ids, [item["text"] for item in packet["claim"].get("sections") or []])
    return {**value, **_envelope(packet, TASK_CRITIQUE_REF, "critic")}


def assessor_reply(packet, status, citations, *, findings=None, limitations="Fixture documentary check only."):
    """Shaped exactly as `documentary.assess` returns; quotes are checked against the real packet.

    The assessor gives statements and Python derives the status, so the double writes the statements that
    yield `status`: every citation supported for `pass`, the first contradicted for `fail`, one supported and
    one not addressed for `inconclusive`, and only one not addressed for `no_evidence`.
    """
    def judged(verdict, citation=None):
        return {"statement": "Fixture statement.", "verdict": verdict,
                "reference_ref": citation["reference_ref"] if citation else "", "quote": citation["quote"] if citation else ""}
    citations = [dict(citation) for citation in citations]
    statements = {"pass": [judged("supported", item) for item in citations],
                  "fail": [judged("contradicted", item) for item in citations[:1]]
                          + [judged("supported", item) for item in citations[1:]],
                  "inconclusive": [judged("supported", item) for item in citations] + [judged("not_addressed")],
                  "no_evidence": [judged("not_addressed")]}[status]
    value = validate_assessment({
        "statements": statements,
        "findings": list(findings) if findings else ["Fixture assessment finding."] * len(RUBRIC["criteria"]),
        "limitations": limitations}, packet)
    assert value["status"] == status, (value["status"], status)
    return {"assessment": value, **_envelope(packet, RUBRIC_REF, "assessor")}
