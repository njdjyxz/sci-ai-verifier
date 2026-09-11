"""Complete synthetic workflow acceptance; approvals here are deliberately fictional."""

import json
import tempfile
import unittest
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import test_stage2 as stage2
import test_stage3 as stage3
from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import canonical, digest
from sci_ai_verifier.common import Fault
from sci_ai_verifier.fixtures import ReplaySubject
from sci_ai_verifier.scientific import POLICY, SCOPE, composition, score, pin_assets, resource_requirements
from sci_ai_verifier.storage import Store

# Independently tabulated fixture responses, not obtained from the evaluator at execution time.
ANSWERS = {"H2O": "18.01056468403", "CO2": "43.98982923914", "NH3": "17.02654910112",
           "CH4": "16.03130012892", "C6H12O6": "180.06338810418",
           "H3PO4": "97.97689557339", "C2H6OS": "78.01393598735"}
QUOTES = ["The skill computes neutral CHNOPS mass with H-1 C-12 N-14 O-16 P-31 S-32.",
          "The skill provides the same mass as a plain decimal in Da."]


class FixtureSubject:
    identity = {"adapter_id": "scripted-mass-v1", "model_id": "scripted", "synthetic": True}

    def __init__(self, mode="correct"):
        self.identity = deepcopy(type(self).identity)
        self.mode, self.calls = mode, []

    def observe(self, **request):
        self.calls.append(deepcopy(request))
        if self.mode == "error":
            raise RuntimeError("Sensitive adapter exception must not leak")
        if self.mode == "interrupt":
            raise KeyboardInterrupt()
        formula = request["case_input"]["formula"]
        value = ANSWERS[formula]
        if self.mode == "wrong" or (self.mode == "alternating" and len(self.calls) % 2 == 0):
            value = str(Decimal(value) + 1)
        if self.mode == "invalid":
            value += " Da"
        if self.mode == "mutating":
            request["source"][0]["content"] = "Changed by adapter"
        return {"text": value, "model_id": "other" if self.mode == "identity" else "scripted",
                "response_id": "fixture-" + str(len(self.calls))}


def fixture_release(directory, subject, *, generic=False):
    pins = {"objects": []}
    pin_assets(Store(directory / "pin-builder"), pins,
               stage2.ROOT / "src/sci_ai_verifier/assets")
    assets = stage3.fixture_assets()
    evaluator = assets["evaluators"]["evaluators"][0]
    evaluator.update(scopes=[SCOPE], grades=["C"], method="chemical_mass_v1",
                     policy_sha256=digest(canonical(POLICY)), resources=resource_requirements(pins))
    assets["evaluators"]["harnesses"] = []
    if generic:
        evaluator["status"] = "approved"
        assets["evaluators"]["evaluators"] = []
        assets["evaluators"]["harnesses"] = [evaluator]
    assets["subject_runners"]["subject_runners"][0].update(
        adapter_id=subject.identity["adapter_id"], model_allowlist=[subject.identity["model_id"]], max_trials=10)
    stage3.write_release(directory / "release", assets)
    return assets


class VerificationTests(unittest.TestCase):
    start = stage2.Stage2Tests.start
    call = stage2.Stage2Tests.call
    load = stage2.Stage2Tests.load
    parent_args = stage2.Stage2Tests.parent_args

    def setUp(self):
        parent = stage2.ROOT / ".verifier/test-work"
        parent.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="verification-", dir=parent)
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.sources = self.base / "sources"
        self.skill = self.sources / "skill"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("\n".join(QUOTES), encoding="utf-8")
        self.subject = FixtureSubject()
        self.assets = fixture_release(self.base, self.subject)
        self.runtime = self.new_runtime()

    def new_runtime(self, **kwargs):
        return Runtime(self.base / "data", self.sources, stage2.INSTRUCTIONS, profile="verification",
                       release_directory=self.base / "release", subject_adapter=self.subject, **kwargs)

    def ok(self, state, name, **kwargs):
        result = self.call(state, name, **kwargs)
        self.assertEqual(result["status"], "ok", result)
        return result["data"]

    def extracted(self, count=1):
        data = self.load()
        return self.ok(data, "commit_claim_manifest", **self.parent_args(data), claims=[
            {"statement": quote, "scope": SCOPE, "expected_behavior": "Plain decimal mass in Da",
             "source_path": "SKILL.md", "source_quote": quote, "report_note": "fixture"}
            for quote in QUOTES[:count]])

    def assigned(self, count=1):
        data = self.extracted(count)
        manifest = data["manifest"]
        data = self.ok(data, "list_claim_types")
        return self.ok(data, "commit_claim_type_assignments", manifest_id=manifest["id"],
                       index_digest=data["index_digest"], assignments=[
                           {"claim_id": c["claim_id"], "claim_type_id": "formula.mass", "proposal": {},
                            "report_note": "Synthetic approval only"} for c in manifest["claims"]])

    def selected(self, data=None, route=None):
        data = data or self.assigned()
        route = route or data["routing"]["routes"][0]
        return self.ok(data, "find_registered_evaluators", claim_id=route["claim_id"],
                       route_id=route["route_id"], scope=SCOPE, intended_grade="A")

    def planned(self, data=None, trials=1):
        data = data or self.selected()
        selection = data["selection"]
        return self.ok(data, "commit_evaluation_plan", claim_id=selection["claim_id"],
                       selection_id=selection["selection_id"], match_index=0, scope=SCOPE,
                       trial_count=trials, report_note="Synthetic acceptance")

    @staticmethod
    def parents(plan):
        return {"claim_id": plan["claim_id"], "plan_id": plan["id"], "plan_revision": plan["revision"]}

    def locked(self, data=None, trials=1):
        data = data or self.planned(trials=trials)
        plan = data["plan"]
        data = self.ok(data, "find_resources", **self.parents(plan))
        data = self.ok(data, "materialize_resources", **self.parents(plan), search_id=data["search"]["id"])
        return data, plan

    def audited(self, data=None, trials=1, **kwargs):
        data, plan = self.locked(data, trials)
        arguments = {"scope_finding": "supported", "fairness_finding": "supported",
                     "proposed_status": "pass", "limitations": "Synthetic seven-case pilot"}
        arguments.update(kwargs)
        data = self.ok(data, "commit_plan_audit", **self.parents(plan),
                       resource_lock_id=data["resource_lock"]["id"], **arguments)
        return data, plan

    def executed(self, data=None, plan=None, trials=1):
        if data is None:
            data, plan = self.audited(trials=trials)
        return self.ok(data, "execute_evaluation_plan", **self.parents(plan),
                       audit_id=data["audit"]["id"], request_budget=plan["max_subject_calls"]), plan

    def committed(self, data=None, plan=None):
        if data is None:
            data, plan = self.executed()
        return self.ok(data, "commit_claim_result", **self.parents(plan), execution_id=data["execution"]["id"])

    def test_registered_flow_reports_and_recovery(self):
        data = self.ok(self.committed(), "write_report_card")
        self.assertEqual(data["run_state"], "completed")
        self.assertTrue(data["verification_complete"])
        report = data["report"]
        self.assertTrue(report["synthetic"])
        self.assertEqual((report["evaluated_claims"], report["operational_claims"]), (1, 0))
        result = report["claims"][0]["result"]
        self.assertEqual((result["status"], result["evidence_grade"]), ("pass", "C"))
        self.assertEqual(result["counts"]["evaluated"], 7)
        self.assertIsNone(report["overall_scientific_grade"])
        markdown = Path(data["report_markdown_path"])
        self.assertIn("SYNTHETIC FIXTURE RUN", markdown.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(Path(data["report_json_path"]).read_bytes()), report)
        markdown.unlink()
        resumed = self.runtime.call("resume_verifier_run", {"run_id": data["run_id"]})
        self.assertEqual(resumed["data"]["report"], report)
        self.assertTrue(markdown.is_file())

    def test_generic_bundle_registration_requires_second_revision(self):
        self.assets = fixture_release(self.base, self.subject, generic=True)
        data = self.selected()
        selection = data["selection"]
        data, plan = self.locked(self.planned(data))
        self.assertEqual(data["claim_states"][plan["claim_id"]], "bundle_construction")
        data = self.ok(data, "build_evaluation_bundle", **self.parents(plan))
        bundle_id = data["bundle_id"]
        data = self.ok(data, "validate_evaluation_bundle", **self.parents(plan), bundle_id=bundle_id)
        data = self.ok(data, "register_evaluator", **self.parents(plan), bundle_id=bundle_id)
        self.assertEqual(data["registration"]["status"], "provisional")
        data["selection"] = selection
        data = self.planned(data)
        self.assertEqual((data["plan"]["revision"], data["plan"]["kind"]), (2, "registered"))
        data, plan = self.audited(data)
        audit = data["audit"]
        self.assertEqual(audit["id"], "audit-" + digest(canonical({k: v for k, v in audit.items() if k != "id"})))
        state, _ = self.runtime.store.read(data["run_id"])
        registration = self.runtime.store.get_json(state["claim_work"][plan["claim_id"]]["registration_ref"])
        self.assertEqual((registration["status"], registration["scope"]), ("validated", "runtime_only"))
        data, plan = self.executed(data, plan)
        self.assertEqual(self.ok(self.committed(data, plan), "write_report_card")["report"]["evaluated_claims"], 1)

    def test_wrong_answers_are_fail_at_same_grade(self):
        self.subject.mode = "wrong"
        data, _ = self.executed()
        self.assertEqual((data["execution"]["decision_status"], data["execution"]["achieved_grade_ceiling"]), ("fail", "C"))

    def test_trials_scored_separately_without_averaging(self):
        self.subject.mode = "alternating"
        data, _ = self.executed(trials=2)
        execution = data["execution"]
        self.assertEqual((execution["decision_status"], execution["evaluated"]), ("fail", 14))
        for case in execution["observations"]:
            self.assertEqual([t["status"] for t in case["trials"]], ["pass", "fail"])
            self.assertEqual(case["agreement"], 0.5)

    def test_invalid_observations_retained_without_grade(self):
        self.subject.mode = "invalid"
        data, plan = self.executed()
        self.assertEqual(data["outcome"], "assessor_unavailable")
        state, _ = self.runtime.store.read(data["run_id"])
        record = self.runtime.store.get_json(state["claim_work"][plan["claim_id"]]["execution_ref"])
        self.assertEqual((record["invalid"], record["evaluated"], record["obtained"]), (7, 0, 7))
        self.assertIsNone(record["achieved_grade_ceiling"])
        report = self.ok(data, "write_report_card")["report"]
        self.assertEqual(report["evaluated_claims"], 0)
        self.assertIsNone(report["claims"][0]["operational_outcome"]["scientific_status"])

    def test_adapter_errors_are_operational_and_not_retried(self):
        self.subject.mode = "error"
        data, _ = self.executed()
        self.assertEqual(data["outcome"], "operational_failure")
        self.assertEqual(len(self.subject.calls), 1)
        self.assertNotIn("Sensitive", json.dumps(data))
        self.assertEqual(self.ok(data, "write_report_card")["report"]["operational_claims"], 1)

    def test_interrupted_attempt_is_retained_without_replay(self):
        data, plan = self.audited()
        self.subject.mode = "interrupt"
        with self.assertRaises(KeyboardInterrupt):
            self.executed(data, plan)
        self.runtime = self.new_runtime()
        resumed = self.runtime.call("resume_verifier_run", {"run_id": data["run_id"]})["data"]
        resumed["audit"] = data["audit"]
        self.subject.mode = "correct"
        data, _ = self.executed(resumed, plan)
        self.assertEqual((data["outcome"], len(self.subject.calls)), ("operational_failure", 1))
        report = self.ok(data, "write_report_card")["report"]
        self.assertTrue(report["claims"][0]["operational_outcome"]["artifact_refs"])

    def test_subject_never_receives_oracle_or_planner_notes(self):
        self.subject.mode = "mutating"
        self.executed()
        for request in self.subject.calls:
            self.assertEqual(set(request), {"source", "case_input", "config", "timeout_seconds"})
            self.assertEqual(set(request["case_input"]), {"formula"})
            self.assertEqual(request["source"], [{"path": "SKILL.md", "content": "\n".join(QUOTES)}])
            self.assertNotIn("expected_mass_da", json.dumps(request))
            self.assertNotIn("Synthetic acceptance", json.dumps(request))

    def test_audit_proposal_advisory_and_revision_invalidates_lock(self):
        selected = self.selected()
        selection = selected["selection"]
        data, plan = self.audited(self.planned(selected), scope_finding="uncertain")
        self.assertEqual(data["audit"]["audit_status"], "fail")
        self.assertFalse(data["audit"]["proposal_agreed"])
        data["selection"] = selection
        revised = self.planned(data)
        self.assertEqual(revised["plan"]["revision"], 2)
        stale = self.call(revised, "find_resources", **self.parents(plan))
        self.assertEqual(stale["error"]["code"], "stale_plan")
        state, _ = self.runtime.store.read(revised["run_id"])
        self.assertIsNone(state["claim_work"][plan["claim_id"]]["lock_ref"])
        revised.update(stale["error"])
        data, _ = self.audited(revised, proposed_status="fail")
        self.assertEqual(data["audit"]["audit_status"], "pass")

    def test_verdict_override_rejected(self):
        data, plan = self.executed()
        result = self.call(data, "commit_claim_result", **self.parents(plan),
                           execution_id=data["execution"]["id"], status="fail", grade="A")
        self.assertEqual(result["error"]["code"], "verdict_override")
        data.update(result["error"])
        self.assertEqual(self.committed(data, plan)["claim_result"]["evidence_grade"], "C")

    def test_zero_claim_report(self):
        data = self.ok(self.extracted(0), "write_report_card")
        self.assertEqual(data["report"]["claims"], [])
        self.assertTrue(data["verification_complete"])

    def test_empty_catalog_honest_operational_report(self):
        self.assets["evaluators"].update(evaluators=[], harnesses=[])
        stage3.write_release(self.base / "release", self.assets)
        data = self.selected()
        self.assertEqual(data["outcome"], "implementation_required")
        self.assertEqual(self.ok(data, "write_report_card")["report"]["operational_claims"], 1)

    def test_mixed_claim_cancel_preserves_completed_result(self):
        data = self.assigned(2)
        routes = data["routing"]["routes"]
        data, plan = self.audited(self.planned(self.selected(data, routes[0])))
        data, plan = self.executed(data, plan)
        data = self.committed(data, plan)
        cancelled = self.runtime.call("cancel_verifier_run", {"run_id": data["run_id"]})
        self.assertEqual(cancelled["status"], "ok", cancelled)
        report = cancelled["data"]["report"]
        self.assertEqual((report["evaluated_claims"], report["operational_claims"]), (1, 1))
        outcome = next(row["operational_outcome"] for row in report["claims"] if row["operational_outcome"])
        self.assertEqual(outcome["category"], "cancelled")

    def test_changed_subject_and_method_do_not_execute(self):
        data, plan = self.audited()
        self.subject.identity["model_id"] = "changed"
        data, _ = self.executed(data, plan)
        self.assertEqual(data["outcome"], "subject_runner_unavailable")
        self.assertEqual(self.subject.calls, [])

    def test_changed_installed_method_does_not_execute(self):
        data, plan = self.audited()
        with patch("sci_ai_verifier.execution.method_current", return_value=False):
            data, _ = self.executed(data, plan)
        self.assertEqual(data["outcome"], "implementation_required")
        self.assertEqual(self.subject.calls, [])

    def test_original_source_changes_do_not_change_subject_snapshot(self):
        data, plan = self.audited()
        (self.skill / "SKILL.md").write_text("Live source changed", encoding="utf-8")
        self.executed(data, plan)
        self.assertEqual(self.subject.calls[0]["source"][0]["content"], "\n".join(QUOTES))

    def test_tampered_locked_resource_prevents_execution(self):
        data, plan = self.audited()
        state, _ = self.runtime.store.read(data["run_id"])
        key = state["resource_assets"]["nist-chnops-isotopes"]["sha256"]
        (self.runtime.store.root / "store" / key).write_bytes(b"changed")
        result = self.call(data, "execute_evaluation_plan", **self.parents(plan),
                           audit_id=data["audit"]["id"], request_budget=7)
        self.assertEqual(result["status"], "fatal")
        self.assertEqual(self.subject.calls, [])

    def test_mismatched_response_identity_is_operational(self):
        self.subject.mode = "identity"
        data, _ = self.executed()
        self.assertEqual((data["outcome"], len(self.subject.calls)), ("operational_failure", 1))

    def test_report_cannot_run_before_claim_terminal(self):
        data = self.assigned()
        result = self.call(data, "write_report_card")
        self.assertEqual(result["error"]["code"], "illegal_transition")

    def test_stale_audit_and_wrong_budget_prevent_subject_calls(self):
        data, plan = self.audited()
        audit_id = data["audit"]["id"]
        for field, value, code in (("audit_id", "audit-stale", "stale_audit"),
                                   ("request_budget", 6, "execution_budget")):
            args = {**self.parents(plan), "audit_id": audit_id, "request_budget": 7, field: value}
            result = self.call(data, "execute_evaluation_plan", **args)
            self.assertEqual(result["error"]["code"], code)
            data.update(result["error"])
        self.assertEqual(self.subject.calls, [])

    def test_plan_and_run_subject_budgets(self):
        data = self.selected()
        selection = data["selection"]
        result = self.call(data, "commit_evaluation_plan", claim_id=selection["claim_id"],
                           selection_id=selection["selection_id"], match_index=0, scope=SCOPE,
                           trial_count=10, report_note="Too many calls")
        self.assertEqual(result["error"]["code"], "execution_budget")
        data = self.assigned(2)
        routes = data["routing"]["routes"]
        data, plan = self.audited(self.planned(self.selected(data, routes[0]), trials=5))
        data, plan = self.executed(data, plan)
        data = self.committed(data, plan)
        data, plan = self.audited(self.planned(self.selected(data, routes[1]), trials=5))
        data, _ = self.executed(data, plan)
        self.assertEqual(data["outcome"], "operational_failure")
        self.assertEqual(len(self.subject.calls), 35)
        report = self.ok(data, "write_report_card")["report"]
        self.assertEqual((report["evaluated_claims"], report["operational_claims"]), (1, 1))

    def test_invalid_runner_bounds_are_operational(self):
        self.assets["subject_runners"]["subject_runners"][0]["max_trials"] = "ten"
        stage3.write_release(self.base / "release", self.assets)
        self.assertEqual(self.planned()["outcome"], "subject_runner_unavailable")

    def test_wrong_resource_and_method_pins_are_operational(self):
        self.assets["evaluators"]["evaluators"][0]["resources"][0]["sha256"] = "0" * 64
        stage3.write_release(self.base / "release", self.assets)
        self.assertEqual(self.planned()["outcome"], "resource_unavailable")
        self.assets["evaluators"]["evaluators"][0]["method"] = "uninstalled"
        stage3.write_release(self.base / "release", self.assets)
        self.assertEqual(self.planned()["outcome"], "implementation_required")

    def test_documentary_assessor_absence_has_no_grade(self):
        entry = stage3.fixture_assets()["evaluators"]["harnesses"][0]
        entry["scopes"] = [SCOPE]
        self.assets["evaluators"].update(evaluators=[], harnesses=[entry])
        stage3.write_release(self.base / "release", self.assets)
        data = self.planned()
        self.assertEqual(data["outcome"], "assessor_unavailable")
        report = self.ok(data, "write_report_card")["report"]
        self.assertIsNone(report["claims"][0]["operational_outcome"]["evidence_grade"])

    def test_two_results_make_one_unbroken_markdown_table(self):
        data = self.assigned(2)
        routes = data["routing"]["routes"]
        for route in routes:
            data, plan = self.audited(self.planned(self.selected(data, route)))
            data, plan = self.executed(data, plan)
            data = self.committed(data, plan)
        data = self.ok(data, "write_report_card")
        lines = Path(data["report_markdown_path"]).read_text(encoding="utf-8").splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("| Claim |"))
        self.assertTrue(all(line.startswith("|") for line in lines[index:index+4]))
        self.assertEqual(data["report"]["evaluated_claims"], 2)

    def test_complete_bootstrap_includes_execution_contract_and_rubric(self):
        data = self.start()
        identities = {entry["identity"] for entry in data["context_blocks"]}
        self.assertIn("references/verification-contract.md", identities)
        self.assertIn("references/evidence-rubric.md", identities)
        self.assertLess(len(canonical(data)), 200_000)

    def test_installed_scoring_tolerance_and_grammar(self):
        self.assertEqual(score("18.01056568403", "18.01056468403")["status"], "pass")
        self.assertEqual(score("18.010565684031", "18.01056468403")["status"], "fail")
        for text in ("NaN", "Infinity", "-1", "1e1", "18 Da", '{"mass":18}'):
            self.assertEqual(score(text, "18")["status"], "invalid")
        for formula in ("NaCl", "H0", "(OH)2", "H2H", "H1001", "H2O+", "13C", "C.2H2O"):
            with self.assertRaises(ValueError):
                composition(formula)

    def test_replay_configuration_pinned_and_answer_file_not_submitted(self):
        source = stage2.ROOT / "examples/chemical-mass-fixture/subject.json"
        adapter = ReplaySubject(source)
        self.assertTrue(adapter.identity["synthetic"])
        self.assertIn(digest(source.read_bytes()), adapter.identity["adapter_id"])
        result = adapter.observe(source=[], case_input={"formula": "H2O"}, config=adapter.identity, timeout_seconds=1)
        self.assertEqual(result["text"], ANSWERS["H2O"])
        self.assertFalse((source.parent / "submitted/subject.json").exists())

    def test_nonfinite_reference_rejected_at_pin_time(self):
        asset = json.loads((stage2.ROOT / "src/sci_ai_verifier/assets/chemical-reference.json").read_bytes())
        asset["isotopes"]["H"]["mass_da"] = "NaN"
        directory = self.base / "bad-resource"
        directory.mkdir()
        (directory / "chemical-reference.json").write_bytes(canonical(asset))
        with self.assertRaises(Fault):
            pin_assets(self.runtime.store, {"objects": []}, directory)


if __name__ == "__main__":
    unittest.main()
