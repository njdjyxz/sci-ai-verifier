"""Deterministic claim-result copying and complete report accounting."""

import re

from .common import Fault
from .planning import artifact, keep, parent, operational


def commit_result(store, state, args):
    item, plan = parent(store, state, args)
    execution = store.get_json(item["execution_ref"])
    if args["execution_id"] != execution["id"] or execution["decision_status"] is None:
        raise Fault("invalid_execution", "Use a completed execution with an authoritative scientific decision.", ["execution_id"])
    if ((args.get("status") and args["status"] != execution["decision_status"])
            or (args.get("grade") and args["grade"] != execution["achieved_grade_ceiling"])):
        raise Fault("verdict_override", "Copy the exact execution verdict and grade or omit both.", ["status", "grade"])
    result = artifact(state, "result", args["claim_id"], result_kind="evaluated_result",
                      status=execution["decision_status"], evidence_grade=execution["achieved_grade_ceiling"],
                      requested_grade=plan["requested_grade"], plan_ref=item["plan_ref"], audit_ref=item["audit_ref"],
                      execution_ref=item["execution_ref"], bundle_ref=item["bundle_ref"], resource_lock_ref=item["lock_ref"],
                      source_ref=state["source_ref"], capability=plan["capability"], subject_runner=plan["subject_runner"],
                      subject=execution["subject"], policy_ref=execution["policy_ref"],
                      grade_limit_reasons=execution["grade_limit_reasons"],
                      counts={field: execution[field] for field in ("requested", "attempted", "obtained", "evaluated", "invalid", "missing")},
                      observations=execution["observations"], trial_count=plan["trial_count"],
                      aggregation=plan["policy"]["aggregation"], coverage=execution["coverage"],
                      exclusions=execution["exclusions"], ai_involvement=plan["ai_involvement"],
                      report_note=plan["report_note"], synthetic=execution["synthetic"])
    item["result_ref"] = keep(store, state, result)
    state["claim_states"][args["claim_id"]] = "terminal_result"
    return {"outcome": "claim_result_committed", "claim_result": result}


def escaped(value):
    return re.sub(r"([\\`*_{}\[\]()#+.!|<>-])", r"\\\1", str(value).replace("\n", " "))


def write_report(store, state, args=None):
    manifest = store.get_json(state["manifest_ref"])
    outcomes = [store.get_json(key) for key in state["operational_refs"]]
    rows = []
    for claim in manifest["claims"]:
        claim_id = claim["claim_id"]
        result_ref = state["claim_work"].get(claim_id, {}).get("result_ref")
        found = [o for o in outcomes if o.get("claim_id") == claim_id and o.get("terminal")]
        if state["claim_states"][claim_id] == "terminal_result" and result_ref:
            row = {"claim": claim, "result": store.get_json(result_ref), "operational_outcome": None}
        elif state["claim_states"][claim_id] == "terminal_operational" and len(found) == 1:
            row = {"claim": claim, "result": None, "operational_outcome": found[0]}
        else:
            raise Fault("incomplete_accounting", "Every accepted claim needs exactly one terminal result or operational outcome.", ["run_id"])
        rows.append(row)
    finalization = store.finalize(state)
    report = artifact(state, "report", None, source_ref=state["source_ref"], manifest_ref=state["manifest_ref"],
                      catalog_ref=state["catalog_ref"], claims=rows, claim_count=len(rows),
                      evaluated_claims=sum(row["result"] is not None for row in rows),
                      operational_claims=sum(row["operational_outcome"] is not None for row in rows),
                      overall_scientific_grade=None, finalization=finalization,
                      synthetic=state["subject_config"]["synthetic"],
                      warnings=["Results are limited to each claim's recorded scope and evidence.",
                                "Fixture observations are not evidence of a live submitted skill." ]
                      if state["subject_config"]["synthetic"] else
                      ["A completed report does not imply every claim was scientifically evaluated."])
    lines = ["# Scientific verification report", "", f"Run: `{state['run_id']}`", ""]
    if report["synthetic"]:
        lines += ["**SYNTHETIC FIXTURE RUN — not a live scientific verification.**", ""]
    lines += [f"Claims: {len(rows)}; evaluated: {report['evaluated_claims']}; operational outcomes: {report['operational_claims']}.", "",
              "| Claim | Scientific status | Evidence grade | Limitation |", "|---|---|---|---|"]
    details = []
    for row in rows:
        result, outcome = row["result"], row["operational_outcome"]
        lines.append("| " + " | ".join(escaped(v) for v in (
            row["claim"]["statement"], result["status"] if result else "Not evaluated",
            result["evidence_grade"] if result else "Not assigned",
            result["coverage"] if result else outcome["reason"])) + " |")
        if result:
            details += ["", f"Claim `{row['claim']['claim_id']}`. Subject: {escaped(result['subject']['model_id'])}; trials per case: {result['trial_count']}; "
                      f"aggregation: {escaped(result['aggregation'])}. Exclusions: {escaped(result['exclusions'])}."]
    lines += details
    lines += ["", "Detailed source, versions, observations and outcome IDs are retained in report-card.json.", ""]
    state["report_ref"] = keep(store, state, report)
    state["report_markdown_ref"] = store.put("\n".join(lines).encode("utf-8"))
    state["objects"].append(state["report_markdown_ref"])
    state.update(run_state="completed", verification_complete=True, completion_reason="report_written",
                 finished_at=state["updated_at"], finalization=finalization)
    directory = store.run_dir(state["run_id"])
    return {"outcome": "run_completed" if finalization["status"] == "complete" else "run_completed_with_cleanup_warnings",
            "report": report, "report_json_path": str(directory / "report-card.json"),
            "report_markdown_path": str(directory / "report-card.md")}


def cancel_and_report(store, state, reason):
    for claim_id, claim_state in state["claim_states"].items():
        if claim_state not in {"terminal_result", "terminal_operational"}:
            operational(store, state, claim_id, "cancelled", reason, state["objects"])
    state["run_state"] = "reporting"
    return write_report(store, state)
