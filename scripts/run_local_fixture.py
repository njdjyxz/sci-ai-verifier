"""Reproduce a complete local-profile report with visibly synthetic test evidence."""

import sys
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import canonical


class SyntheticSubject:
    identity = {"adapter_id": "local-acceptance-fixture-1", "model_id": "synthetic-no-model", "synthetic": True}

    def observe(self, *, source, case_input, config, timeout_seconds):
        # Independent fixture observations; never read the candidate or reference object.
        responses = {"One kilometer in meters": "1000", "One hour in seconds": "3600", "One day in seconds": "86400"}
        return {"text": responses[case_input["input"]], "response_id": "synthetic-" + str(uuid4()),
                "invocation_verified": True, "invocation_evidence": "synthetic test double; no Claude execution",
                "model_id": "synthetic-no-model", "synthetic": True}


def main():
    fixture = ROOT / "examples/local-reference-fixture"
    # Synthetic candidates never enter the user's live local candidate pool.
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
    snapshot = data["snapshot"]
    quote = "Convert one kilometer to meters, one hour to seconds, or one day to seconds."
    call("commit_claim_manifest", snapshot_id=snapshot["id"], snapshot_digest=snapshot["digest"], claims=[{
        "statement": quote, "scope": "Three named unit conversions", "expected_behavior": "Plain decimal without units",
        "source_path": "SKILL.md", "source_quote": quote, "report_note": "Synthetic workflow acceptance only"}])
    claim_id = data["manifest"]["claims"][0]["claim_id"]
    call("list_local_candidates", claim_id=claim_id)
    raw = (fixture / "reference.txt").read_bytes()
    with patch("sci_ai_verifier.local_candidates.fetch_public", return_value=(raw, raw.decode())):
        call("fetch_local_reference", claim_id=claim_id, url="https://example.invalid/synthetic-reference",
             version="fixture-1", license="Repository test fixture; not an external scientific source")
    reference = data["reference_ref"]
    cases = [{"case_id": str(index), "input": prompt, "expected": expected, "reference_ref": reference,
              "source_quote": quote, "applicability": "Exact named conversion in the synthetic fixture"}
             for index, (prompt, expected, quote) in enumerate([
                ("One kilometer in meters", "1000", "One kilometer equals 1000 meters."),
                ("One hour in seconds", "3600", "One hour equals 3600 seconds."),
                ("One day in seconds", "86400", "One day equals 86400 seconds.")], 1)]
    call("qualify_local_candidate", claim_id=claim_id, name="Synthetic conversion reference", scope="Three named unit conversions",
         method="numeric", limitations="Three illustrative synthetic cases; no live model or scientific qualification.", cases=cases)
    call("select_local_candidate", claim_id=claim_id, candidate_ref=data["candidate_ref"], applicability="Synthetic fixture matches the named input conversions")
    call("execute_local_claim", claim_id=claim_id)
    call("write_report_card")
    runtime.store.read(data["run_id"], verify_objects=True)
    summary = {key: data[key] for key in ("run_id", "verification_complete", "report_json_path", "report_markdown_path")}
    summary.update(synthetic=True, workspace=str(workspace), scientific_grade=None)
    sys.stdout.buffer.write(canonical(summary)+b"\n")


if __name__ == "__main__":
    main()
