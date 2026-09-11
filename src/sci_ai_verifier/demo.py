"""General same-chat demonstrations, deliberately separate from scientific verification."""

import json
import re
from decimal import Decimal

from .common import Fault, canonical, digest
from .planning import artifact, keep
from .reporting import escaped

ASSESSMENTS = {"met_expectations", "did_not_meet_expectations", "not_tested"}
LEGAL = {"created": ["load_submitted_skill"],
         "source_ready": ["read_snapshot_file", "commit_claim_manifest"],
         "demo_planning": ["commit_demo_plan"], "demo_execution": ["record_demo_observation"],
         "reporting": ["write_report_card"], "completed": [], "incomplete": []}


def commit_plan(store, state, args):
    manifest = store.get_json(state["manifest_ref"])
    if args["manifest_id"] != manifest["id"]:
        raise Fault("stale_manifest", "Use the accepted manifest ID.", ["manifest_id"])
    claims = set(state["claim_states"])
    if {test["claim_id"] for test in args["tests"]} != claims:
        raise Fault("demo_coverage", "Include at least one example for every accepted claim, and no unknown claims.", ["tests"])
    tests = []
    for index, test in enumerate(args["tests"]):
        for check in test["checks"]:
            if check["kind"] not in {"review", "contains", "equals", "json"}:
                raise Fault("demo_check_kind", "Use review, contains, equals or json.", ["tests"])
            if check["kind"] in {"contains", "equals"} and not check["expected"]:
                raise Fault("demo_check_expected", "Exact and contains checks need an expected value.", ["tests"])
        identity = digest(canonical({"manifest_ref": state["manifest_ref"], "index": index, **test}))
        tests.append({"test_id": "test-" + identity, **test})
    plan = artifact(state, "demo-plan", None, source_ref=state["source_ref"], manifest_ref=state["manifest_ref"],
                    summary=args["summary"], tests=tests, assessment_basis="same_chat_demo",
                    independent_verification=False, scientific_grade=None)
    state["demo_plan_ref"] = keep(store, state, plan)
    state["run_state"] = "demo_execution"
    state["claim_states"] = dict.fromkeys(claims, "demo_execution")
    return {"outcome": "demo_plan_committed", "demo_plan": plan,
            "instruction": "Apply the submitted skill to each fixed input in Chat; record the actual output or not_tested."}


def checks_for(output, checks):
    results = []
    for check in checks:
        passed = None
        if check["kind"] == "contains":
            passed = check["expected"] in output
        elif check["kind"] == "equals":
            passed = check["expected"] == output
        elif check["kind"] == "json":
            try:
                def no_constant(value):
                    raise ValueError("Not a finite JSON value")
                def unique_pairs(pairs):
                    result = {}
                    for key, value in pairs:
                        if key in result:
                            raise ValueError("Duplicate key")
                        result[key] = value
                    return result
                json.loads(output, parse_constant=no_constant, object_pairs_hook=unique_pairs, parse_float=Decimal)
                passed = True
            except (ValueError, RecursionError):
                passed = False
        results.append({**check, "passed": passed, "basis": "same_chat_review" if passed is None else "deterministic_text_check"})
    return results


def observe(store, state, args):
    plan = store.get_json(state["demo_plan_ref"])
    if args["plan_id"] != plan["id"]:
        raise Fault("stale_demo_plan", "Use the committed demo plan ID.", ["plan_id"])
    test = next((value for value in plan["tests"] if value["test_id"] == args["test_id"]), None)
    if test is None:
        raise Fault("unknown_test", "Use a test ID returned in the committed plan.", ["test_id"])
    if args["test_id"] in state["demo_observation_refs"]:
        raise Fault("demo_observation_exists", "This example is already recorded; recover context instead of replacing it.", ["test_id"])
    if args["assessment"] not in ASSESSMENTS:
        raise Fault("demo_assessment", "Use met_expectations, did_not_meet_expectations or not_tested.", ["assessment"])
    if args["assessment"] != "not_tested" and not args["output"].strip():
        raise Fault("demo_output_missing", "Record the actual output, or mark the example not_tested.", ["output"])
    if not args["reason"].strip():
        raise Fault("demo_reason_missing", "Explain the assessment or missing prerequisite.", ["reason"])
    checks = checks_for(args["output"], test["checks"]) if args["assessment"] != "not_tested" else []
    assessment = ("did_not_meet_expectations" if any(check["passed"] is False for check in checks)
                  else args["assessment"])
    value = artifact(state, "demo-observation", test["claim_id"], plan_ref=state["demo_plan_ref"],
                     test_id=test["test_id"], output=args["output"], proposed_assessment=args["assessment"],
                     assessment=assessment, reason=args["reason"], checks=checks,
                     assessment_basis="same_chat_demo", independent_verification=False,
                     actual_model_identity=None, scientific_grade=None)
    state["demo_observation_refs"][test["test_id"]] = keep(store, state, value)
    for claim_id in state["claim_states"]:
        if all(test["test_id"] in state["demo_observation_refs"] for test in plan["tests"] if test["claim_id"] == claim_id):
            state["claim_states"][claim_id] = "terminal_demo"
    if len(state["demo_observation_refs"]) == len(plan["tests"]):
        state["run_state"] = "reporting"
    return {"outcome": "demo_observation_recorded", "observation": value,
            "remaining_test_ids": [test["test_id"] for test in plan["tests"] if test["test_id"] not in state["demo_observation_refs"]]}


def write_report(store, state, args=None, *, cancelled=False):
    manifest = store.get_json(state["manifest_ref"])
    plan = store.get_json(state["demo_plan_ref"]) if state["demo_plan_ref"] else None
    tests = plan["tests"] if plan else []
    rows = []
    for test in tests:
        key = state["demo_observation_refs"].get(test["test_id"])
        if key is None and not cancelled:
            raise Fault("demo_incomplete", "Record every example before reporting.", ["run_id"])
        rows.append({"test": test, "observation_ref": key,
                     "observation": store.get_json(key) if key else None,
                     "assessment": store.get_json(key)["assessment"] if key else "not_tested",
                     "reason": "Cancelled before this example was recorded" if key is None else ""})
    claims = []
    for claim in manifest["claims"]:
        related = [row for row in rows if row["test"]["claim_id"] == claim["claim_id"]]
        counts = {name: sum(row["assessment"] == name for row in related) for name in sorted(ASSESSMENTS)}
        claims.append({"claim": claim, "test_ids": [row["test"]["test_id"] for row in related],
                       "counts": counts, "untested": not related or all(row["assessment"] == "not_tested" for row in related)})
    finalization = store.finalize(state)
    report = artifact(state, "demo-report", None, title="Skill demo report", assessment_basis="same_chat_demo",
                      independent_verification=False, scientific_grade=None, actual_model_identity=None,
                      source_ref=state["source_ref"], manifest_ref=state["manifest_ref"], plan_ref=state["demo_plan_ref"],
                      submission_origin=state["submission_origin"], claims=claims, examples=rows,
                      counts={name: sum(row["assessment"] == name for row in rows) for name in sorted(ASSESSMENTS)},
                      cancelled=cancelled, finalization=finalization,
                      limitations=["Outputs and qualitative assessments were supplied by the same Claude chat.",
                                   "No separate subject execution, independent scientific evaluation or exact model identity is attested.",
                                   "Examples cover only the recorded inputs; unavailable external capabilities remain untested."])
    lines = ["# Skill demo report", "", "**Same-chat demo — independent verification has not been performed.**", "",
             f"Run: `{state['run_id']}`", "", f"Claims: {len(claims)}. Examples: {len(rows)}.", "",
             "| Example | Assessment | Purpose |", "|---|---|---|"]
    for index, row in enumerate(rows, 1):
        lines.append(f"| {index} | {escaped(row['assessment'].replace('_', ' '))} | {escaped(row['test']['purpose'])} |")
    if not claims:
        lines += ["", "No testable behavior was extracted from this submission."]
    for entry in claims:
        if entry["untested"]:
            lines += ["", "Untested claim: " + escaped(entry["claim"]["statement"])]
    for index, row in enumerate(rows, 1):
        observation = row["observation"]
        lines += ["", f"## Example {index}", "", "Input:", "", fenced(row["test"]["input"]), "", "Output:", "",
                  fenced(observation["output"]) if observation else "Not recorded.", "", "Assessment:", "",
                  escaped(observation["reason"] if observation else row["reason"])]
        if observation:
            for check in observation["checks"]:
                label = "Same-chat review" if check["passed"] is None else "Passed" if check["passed"] else "Failed"
                lines += ["", f"{label}: {escaped(check['description'])}"]
    lines += ["", "## Limits", "", *["- " + value for value in report["limitations"]], "",
              "Scientific grade: not assigned. Exact source, plan and observations are retained in report-card.json.", ""]
    state["report_ref"] = keep(store, state, report)
    state["report_markdown_ref"] = store.put("\n".join(lines).encode("utf-8"))
    state["objects"].append(state["report_markdown_ref"])
    state.update(run_state="completed", claim_states=dict.fromkeys(state["claim_states"], "terminal_demo"),
                 verification_complete=True, finished_at=state["updated_at"],
                 completion_reason="demo_cancelled" if cancelled else "demo_report_written", finalization=finalization)
    directory = store.run_dir(state["run_id"])
    return {"outcome": "demo_report_completed", "report": report,
            "report_json_path": str(directory / "report-card.json"), "report_markdown_path": str(directory / "report-card.md")}


def fenced(value):
    delimiter = "`" * max(3, 1 + max((len(match.group()) for match in re.finditer(r"`+", value)), default=0))
    return delimiter + "\n" + value + "\n" + delimiter
