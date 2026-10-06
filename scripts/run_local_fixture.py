"""Reproduce a complete local-profile report with visibly synthetic test evidence.

Three tasks ask for unit conversions whose expected values are quoted from the fixture's reference.
The reference solution and every subject trial are synthetic stand-ins, so this needs no Docker, no
Claude account and no network; it checks the workflow's mechanics only.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import canonical, digest

ANSWERS = {"one kilometer in meters": 1000, "one hour in seconds": 3600, "one day in seconds": 86400}


def answer(given):
    """The conversion a task's job asks for, as the fixture skill gives it."""
    asked = next(key for key in ANSWERS if key in given["task"].lower())
    return json.dumps({"value": ANSWERS[asked]}).encode()


class SyntheticRunner:
    """Stands in for the operator's container: the reference solution answers each task correctly."""

    def __init__(self, settings, *, log=None, sandbox_factory=None):
        pass

    def generate(self, code, arguments):
        raise AssertionError("The fixture's tasks have no generator.")

    def solve(self, code, given, files):
        return {"exit_code": 0, "stderr": "", "results": answer(given), "image_id": "synthetic"}


class SyntheticSubject:
    identity = {"adapter_id": "local-acceptance-fixture-1", "model_id": "synthetic-no-model", "synthetic": True}

    def observe(self, *, source, case_input, config, timeout_seconds, task_files=None):
        # Independent fixture observations; never read the design or reference object.
        raw = answer(case_input)
        return {"text": "Wrote the results file.", "response_id": "synthetic-" + str(uuid4()),
                "invocation_verified": True, "invocation_evidence": "synthetic test double; no Claude execution",
                "model_id": "synthetic-no-model", "synthetic": True,
                "artifacts": [{"path": "results.json", "sha256": digest(raw), "bytes": len(raw),
                               "base64": __import__("base64").b64encode(raw).decode()}], "run_problems": []}


def main():
    fixture = ROOT / "examples/local-reference-fixture"
    # Synthetic designs never enter the user's live local candidate pool.
    workspace = ROOT / ".verifier/local-fixtures" / str(uuid4())
    runtime = Runtime(workspace, fixture, ROOT / "skills/scientific-verifier", profile="local", subject_adapter=SyntheticSubject())
    data = runtime.call("start_verifier_run", {"source_path": str(fixture / "SKILL.md")})["data"]

    def call(tool, **arguments):
        nonlocal data
        response = runtime.call(tool, {"run_id": data["run_id"], "state_token": data["state_token"], **arguments})
        if response["status"] != "ok":
            raise RuntimeError(response)
        data = response["data"]
        return data
    call("load_submitted_skill", source_path=str(fixture / "SKILL.md"))
    snapshot, sections = data["snapshot"], [item["section"] for item in data["sections"]]
    quote = "Convert one kilometer to meters, one hour to seconds, or one day to seconds."
    call("commit_claim_manifest", snapshot_id=snapshot["id"], snapshot_digest=snapshot["digest"], claims=[{
        "statement": quote, "scope": "Three named unit conversions", "expected_behavior": "Plain decimal without units",
        "source_path": "SKILL.md", "source_quote": quote, "report_note": "Synthetic workflow acceptance only",
        "sections": sections}])
    claim_id = data["manifest"]["claims"][0]["claim_id"]
    call("list_local_candidates", claim_id=claim_id)
    raw = (fixture / "reference.txt").read_bytes()
    with patch("sci_ai_verifier.local_candidates.fetch_public", return_value=(raw, raw.decode())):
        call("fetch_local_reference", claim_id=claim_id, url="https://example.invalid/synthetic-reference",
             version="fixture-1", license="Repository test fixture; not an external scientific source")
    reference = data["reference_ref"]
    cases = [{"case_id": str(index), "job": "Convert " + prompt + " and write the number as `value`.",
              "sections": sections, "outputs": [{"field": "value", "type": "number", "value": expected,
                                                 "reference_ref": reference, "source_quote": source}],
              "applicability": "Exact named conversion in the synthetic fixture"}
             for index, (prompt, expected, source) in enumerate([
                ("one kilometer in meters", "1000", "One kilometer equals 1000 meters."),
                ("one hour in seconds", "3600", "One hour equals 3600 seconds."),
                ("one day in seconds", "86400", "One day equals 86400 seconds.")], 1)]
    with patch("sci_ai_verifier.local_tasks.SandboxRunner", SyntheticRunner):
        call("qualify_local_tasks", claim_id=claim_id, name="Synthetic conversion tasks",
             scope="Three named unit conversions", solver={"code": "print('synthetic reference solution')"},
             limitations="Three illustrative synthetic tasks; no live model or scientific qualification.", cases=cases)
        # A synthetic subject is never graded, so this selection settles at no grade; the
        # proposal and justification are still required and are still checked against the facts.
        call("select_local_candidate", claim_id=claim_id, candidate_ref=data["candidate_ref"],
             applicability="Synthetic fixture matches the named input conversions", target_grade="C",
             oracle_independence="Fictional repository fixture, not an external scientific source.",
             coverage="Three tasks, each using the fixture's one section.",
             tolerance_basis="Installed numeric comparison tolerance.",
             uncertainty="A synthetic reference states no uncertainty.",
             stronger_grade_considered="One trial per task is configured, which caps this design at C.")
        call("execute_local_claim", claim_id=claim_id)
    call("write_report_card")
    runtime.store.read(data["run_id"], verify_objects=True)
    summary = {key: data[key] for key in ("run_id", "verification_complete", "report_json_path", "report_markdown_path")}
    summary.update(synthetic=True, workspace=str(workspace), scientific_grade=None)
    sys.stdout.buffer.write(canonical(summary)+b"\n")


if __name__ == "__main__":
    main()
