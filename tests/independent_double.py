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
    validate_assessment, validate_task_critique)

INDEPENDENCE = "fresh host-selected no-tool session; no planner conversation"


def _envelope(packet, rubric_ref, role):
    """The provenance fields both real functions attach to every reply."""
    return {"session_id": "fixture-" + role, "observed_model_ids": ["fixture-model"],
            "packet_ref": digest(canonical(packet)), "rubric_ref": rubric_ref,
            "usage": None, "total_cost_usd": None,
            "independence": INDEPENDENCE, "ai_judgment": True}


def critic_reply(packet, supported, *, findings=None, objections=(), required_revisions=(), rejected=None):
    """Shaped exactly as `documentary.critique_tasks` returns, including the "none" -> None mapping.

    Every task in the packet counts unless `rejected` maps its case ID to another verdict.
    """
    rejected = rejected or {}
    case_ids = [case["case_id"] for case in packet["evidence"]["tasks"]]
    verdicts = {key: {"verdict": rejected.get(key, "counts"), "reason": "Fixture task verdict.",
                      "replacement": "Fixture replacement: a task inside the claim." if key in rejected else ""}
                for key in case_ids}
    value = validate_task_critique({
        "supported_grade": supported,
        "findings": list(findings) if findings else ["Fixture critique finding."] * len(TASK_CRITIQUE_RUBRIC["criteria"]),
        "objections": list(objections), "required_revisions": list(required_revisions), "case_verdicts": verdicts},
        case_ids)
    return {**value, **_envelope(packet, TASK_CRITIQUE_REF, "critic")}


def assessor_reply(packet, status, citations, *, findings=None, limitations="Fixture documentary check only."):
    """Shaped exactly as `documentary.assess` returns; citations are checked against the real packet."""
    value = validate_assessment({
        "status": status,
        "findings": list(findings) if findings else ["Fixture assessment finding."] * len(RUBRIC["criteria"]),
        "citations": [dict(citation) for citation in citations], "limitations": limitations}, packet)
    return {"assessment": value, **_envelope(packet, RUBRIC_REF, "assessor")}
