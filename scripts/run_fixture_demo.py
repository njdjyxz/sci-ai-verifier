"""Reproducible synthetic end-to-end acceptance, with no model or network request."""

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.catalog import manifest_for, verify
from sci_ai_verifier.common import canonical, digest
from sci_ai_verifier.fixtures import ReplaySubject
from sci_ai_verifier.scientific import POLICY, SCOPE, pin_assets, resource_requirements
from sci_ai_verifier.storage import Store, atomic_write


def prepare(directory, variant="correct"):
    directory = Path(directory)
    subject_file = directory / "subject.json"
    data = json.loads((ROOT / "examples/chemical-mass-fixture/subject.json").read_bytes())
    if variant == "wrong":
        data["responses"]["H2O"] = "19.01056468403"
    elif variant == "invalid":
        data["responses"]["H2O"] = "18.01056468403 Da"
    atomic_write(subject_file, canonical(data))
    subject = ReplaySubject(subject_file)
    pins = {"objects": []}
    pin_assets(Store(directory), pins, ROOT / "src/sci_ai_verifier/assets")
    provenance = "SYNTHETIC TEST APPROVAL ONLY; no maintainer or scientific approval"
    common = {"version": "fixture-1", "provenance": provenance}
    interfaces = {"input_interface": "neutral-chnops-formula-v1", "output_interface": "plain-decimal-da-v1",
                  "configuration_contract": "fixture-replay-v1"}
    claim_type = {**common, "id": "fixture.chemical.mass", "status": "approved", "name": "Fixture formula mass",
                  "definition": "Specified neutral isotope mass", "inputs": "flat CHNOPS formula",
                  "outputs": "decimal mass in Da", "boundaries": SCOPE}
    harness = {**common, **interfaces, "id": "fixture.chemical.mass.harness", "status": "approved",
               "claim_type_ids": [claim_type["id"]], "scopes": [SCOPE], "grades": ["C"],
               "method": "chemical_mass_v1", "policy_sha256": digest(canonical(POLICY)),
               "scoring_contract": "chemical-mass-comparison-1", "aggregation_contract": "all_trials_all_cases",
               "trial_grade_policy": "chemical-mass-comparison-1", "limitations": [provenance],
               "resources": resource_requirements(pins)}
    runner = {**common, **interfaces, "id": "fixture.replay.runner", "status": "validated",
              "adapter_id": subject.identity["adapter_id"], "model_allowlist": [subject.identity["model_id"]],
              "max_trials": 10}
    assets = {"claim_types": {"schema_version": 1, "revision": 1, "claim_types": [claim_type]},
              "evaluators": {"schema_version": 2, "revision": 1, "evaluators": [], "harnesses": [harness]},
              "subject_runners": {"schema_version": 1, "revision": 1, "subject_runners": [runner]}}
    raw = {key: canonical(value) for key, value in assets.items()}
    manifest = canonical(manifest_for(raw, "synthetic-demo-1", provenance))
    verify(manifest, raw)
    release = directory / "catalog"
    atomic_write(release / "manifest.json", manifest)
    for key, value in raw.items():
        atomic_write(release / (key + ".json"), value)
    return subject_file, release


def run(directory, variant="correct"):
    fixture, release = prepare(directory, variant)
    source_root = ROOT / "examples/chemical-mass-fixture/submitted"
    config = {"mcpServers": {"scientific-verifier-fixture": {"command": sys.executable,
        "args": ["-I", "-B", str(ROOT / "desktop/server.py"), "serve", "--workspace", str(Path(directory) / "app-data"),
                 "--source-root", str(source_root), "--profile", "verification", "--catalog", str(release),
                 "--subject-fixture", str(fixture), "--instructions", str(ROOT / "skills/scientific-verifier")]}}}
    atomic_write(Path(directory) / "claude_desktop_fixture_config.example.json", canonical(config))
    runtime = Runtime(directory, source_root, ROOT / "skills/scientific-verifier", profile="verification",
                      release_directory=release, subject_adapter=ReplaySubject(fixture))
    def invoke(name, arguments):
        result = runtime.call(name, arguments)
        if result["status"] != "ok":
            raise RuntimeError(json.dumps(result))
        return result["data"]
    state = invoke("start_verifier_run", {"source_path": str(source_root)})
    steps = ["start_verifier_run"]
    def step(name, **arguments):
        nonlocal state
        state = invoke(name, {"run_id": state["run_id"], "state_token": state["state_token"], **arguments})
        steps.append(name)
        return state
    step("load_submitted_skill", source_path=str(source_root))
    quote = "This skill calculates the neutral molecular mass of flat CHNOPS formulas using H-1, C-12, N-14, O-16, P-31 and S-32."
    step("commit_claim_manifest", snapshot_id=state["snapshot"]["id"], snapshot_digest=state["snapshot"]["digest"],
         claims=[{"statement": quote, "scope": SCOPE, "expected_behavior": "Plain decimal mass in Da",
                  "source_path": "SKILL.md", "source_quote": quote, "report_note": "Synthetic demo"}])
    manifest = state["manifest"]
    claim_id = manifest["claims"][0]["claim_id"]
    step("list_claim_types")
    step("commit_claim_type_assignments", manifest_id=manifest["id"], index_digest=state["index_digest"],
         assignments=[{"claim_id": claim_id, "claim_type_id": "fixture.chemical.mass", "proposal": {},
                       "report_note": "Synthetic demo"}])
    step("find_registered_evaluators", claim_id=claim_id, route_id=state["routing"]["routes"][0]["route_id"],
         scope=SCOPE, intended_grade="A")
    selection = state["selection"]
    for revision in (1, 2):
        step("commit_evaluation_plan", claim_id=claim_id, selection_id=selection["selection_id"], match_index=0,
             scope=SCOPE, trial_count=2, report_note="Synthetic demo; no live subject execution")
        plan = state["plan"]
        parents = {"claim_id": claim_id, "plan_id": plan["id"], "plan_revision": plan["revision"]}
        step("find_resources", **parents)
        step("materialize_resources", **parents, search_id=state["search"]["id"])
        if revision == 1:
            step("build_evaluation_bundle", **parents)
            bundle_id = state["bundle_id"]
            step("validate_evaluation_bundle", **parents, bundle_id=bundle_id)
            step("register_evaluator", **parents, bundle_id=bundle_id)
    step("commit_plan_audit", **parents, resource_lock_id=state["resource_lock"]["id"],
         scope_finding="supported", fairness_finding="supported", proposed_status="pass",
         limitations="Synthetic replay; seven illustrative cases and two fixed trials; independent review pending")
    step("execute_evaluation_plan", **parents, audit_id=state["audit"]["id"], request_budget=plan["max_subject_calls"])
    if state["outcome"] == "completed_deterministic_decision":
        step("commit_claim_result", **parents, execution_id=state["execution"]["id"])
    step("write_report_card")
    summary = {"synthetic": True, "variant": variant, "run_id": state["run_id"],
               "report_json": state["report_json_path"], "report_markdown": state["report_markdown_path"],
               "subject_fixture": str(fixture), "catalog": str(release), "tools_exercised": steps,
               "evaluated_claims": state["report"]["evaluated_claims"],
               "operational_claims": state["report"]["operational_claims"]}
    atomic_write(Path(directory) / "demo-summary.json", canonical(summary))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".verifier/fixture-demos" / str(uuid4()))
    parser.add_argument("--variant", choices=("correct", "wrong", "invalid"), default="correct")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output directory to preserve earlier demo evidence.")
    print(json.dumps(run(args.output, args.variant), indent=2))


if __name__ == "__main__":
    main()
