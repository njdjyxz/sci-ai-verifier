"""Local workflow acceptance: real persistence, synthetic independent observations."""

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import Fault, canonical
from sci_ai_verifier.local_entry import BoundRuntime, PublicRuntime
from sci_ai_verifier.local_candidates import fetch_public
from sci_ai_verifier.mcp import Server

ROOT = Path(__file__).resolve().parents[1]
QUOTE = "The skill returns a plain decimal for each reference-table query."
REFERENCE = "Independent fixture reference: alpha is 1.0, beta is 2.0, gamma is 3.0."


class Subject:
    identity = {"adapter_id": "local-fixture", "model_id": "synthetic", "synthetic": True}

    def __init__(self, mode="correct", models=None):
        # `models` supplies one observed_model_ids list per call, as a real adapter
        # reports it from the CLI stream. Left None, the key is absent, which is what a
        # subject that observed no model identity returns.
        self.mode, self.requests, self.models = mode, [], models

    def observe(self, **request):
        self.requests.append(deepcopy(request))
        if self.mode == "interrupt":
            raise KeyboardInterrupt()
        if self.mode == "unavailable":
            raise Fault("claude_unavailable", "Unavailable fixture")
        answer = {"alpha": "1.0", "beta": "2.0", "gamma": "3.0"}[request["case_input"]["input"]]
        observation = {"text": "999" if self.mode == "wrong" else answer,
                       "response_id": "synthetic-" + str(len(self.requests)), "model_id": "synthetic",
                       "invocation_verified": self.mode != "unverified", "synthetic": True}
        if self.models is not None:
            observation["observed_model_ids"] = self.models[min(len(self.requests), len(self.models)) - 1]
        return observation


class LocalTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / ".verifier/test-work"
        parent.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix="local-", dir=parent)
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.source = self.base / "source"
        self.source.mkdir()
        (self.source / "SKILL.md").write_text(QUOTE, encoding="utf-8")
        self.subject = Subject()
        self.runtime = Runtime(self.base / "data", self.source, ROOT / "skills/scientific-verifier",
                               profile="local", subject_adapter=self.subject)
        self.data = self.runtime.call("start_verifier_run", {"source_path": str(self.source)})["data"]
        self.call("load_submitted_skill", source_path=str(self.source))
        self.snapshot = self.data["snapshot"]

    def call(self, tool_name, **args):
        result = self.runtime.call(tool_name, {"run_id": self.data["run_id"], "state_token": self.data["state_token"], **args})
        self.assertEqual(result["status"], "ok", result)
        self.data = result["data"]
        return self.data

    def extract(self, count=1):
        self.call("commit_claim_manifest", snapshot_id=self.snapshot["id"], snapshot_digest=self.snapshot["digest"],
                  claims=[{"statement": QUOTE if i == 0 else "The skill returns a decimal.", "scope": "Reference-table queries",
                           "expected_behavior": "Plain decimal", "source_path": "SKILL.md", "source_quote": QUOTE,
                           "report_note": "Synthetic acceptance"} for i in range(count)])
        self.claims = self.data["manifest"]["claims"]
        self.claim_id = self.claims[0]["claim_id"] if self.claims else None

    def candidate(self, *, lookup=True, **overrides):
        # Lookup is legal only in local_lookup, so a second qualification skips it and
        # reuses the reference this claim already retrieved.
        if lookup:
            self.call("list_local_candidates", claim_id=self.claim_id)
            with patch("sci_ai_verifier.local_candidates.fetch_public", return_value=(REFERENCE.encode(), REFERENCE)):
                self.call("fetch_local_reference", claim_id=self.claim_id, url="https://example.org/reference", version="fixture-v1", license="Unknown; private analysis only")
            self.reference_ref = self.data["reference_ref"]
        reference_ref = self.reference_ref
        arguments = {"claim_id": self.claim_id, "name": "Fixture table", "scope": "Reference-table queries", "method": "numeric",
                     "limitations": "Fictional reference demonstrates mechanics only.",
                     "cases": [{"case_id": name, "input": name, "expected": str(index)+".0", "reference_ref": reference_ref,
                                "source_quote": REFERENCE, "applicability": "Fixture table row"}
                               for index, name in enumerate(("alpha", "beta", "gamma"), 1)]}
        arguments.update(overrides)
        self.call("qualify_local_candidate", **arguments)
        return self.data["candidate_ref"]

    def select(self, key, target_grade="C", **overrides):
        arguments = {"claim_id": self.claim_id, "candidate_ref": key, "target_grade": target_grade,
                     "applicability": "Synthetic fixture scope",
                     "oracle_independence": "Fictional fixture table retrieved by Python, not written by the planner.",
                     "coverage": "Three of three documented table rows.",
                     "tolerance_basis": "Installed numeric tolerance of 1e-6.",
                     "uncertainty": "Fixture reference carries no stated uncertainty.",
                     "stronger_grade_considered": "One trial per case is configured, which caps this design at C."}
        arguments.update(overrides)
        return self.call("select_local_candidate", **arguments)

    def ready(self, target_grade="C"):
        self.extract()
        key = self.candidate()
        self.assertEqual(self.data["outcome"], "qualified_local")
        self.select(key, target_grade=target_grade)
        return key

    def test_a_stable_observed_model_identity_is_pinned_across_the_trial_set(self):
        # local.py pins the first observed identity and compares every later trial to it.
        # With no adapter reporting one, that guard has nothing to compare and never runs.
        self.subject.models = [["fixture-model"]] * 3
        self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["result"]["comparison_status"], "pass")
        work = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"]})["data"]["local_work"][self.claim_id]
        self.assertTrue(work["observed_models_ref"])

    def test_a_model_swap_inside_one_trial_set_is_operational_not_a_result(self):
        """A grade describes one subject. If the identity changes mid-set, there is no result."""
        self.subject.models = [["fixture-model"], ["swapped-model"], ["fixture-model"]]
        self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["outcome"], "subject_model_changed")
        limitation = self.data["limitation"]
        self.assertEqual(limitation["asserted_by"], "runtime")
        self.assertIsNone(limitation["scientific_status"])
        self.assertIsNone(limitation["evidence_grade"])
        # The observations taken before the swap are kept, not discarded.
        self.assertTrue(limitation["receipts"])
        self.call("write_report_card")
        record = self.data["report"]["claims"][0]["record"]
        self.assertEqual(record["code"], "subject_model_changed")
        self.assertIsNone(record["evidence_grade"])

    def test_empty_catalog_discovery_complete_report_and_offline_reuse(self):
        key = self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["result"]["comparison_status"], "pass")
        self.assertIsNone(self.data["result"]["evidence_grade"])
        self.call("write_report_card")
        self.assertTrue(self.data["verification_complete"])
        report_path = Path(self.data["report_markdown_path"])
        self.assertIn("SYNTHETIC", report_path.read_text())
        self.assertIn("| alpha | 1.0 | 1.0 | pass |", report_path.read_text())
        self.assertEqual(self.data["report"]["claims"][0]["tests"][0]["observed"], "1.0")
        report_path.unlink()
        resumed = self.runtime.call("resume_verifier_run", {"run_id": self.data["run_id"]})
        self.assertTrue(resumed["data"]["verification_complete"])
        report = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"],
                                                            "section": "report"})["data"]["section"]
        self.assertEqual(report["identity"], "report")
        self.assertIn("local", report["content"])
        self.assertTrue(report_path.exists())
        for request in self.subject.requests:
            self.assertEqual(set(request["case_input"]), {"input"})
            self.assertNotIn(REFERENCE, canonical(request).decode())
            self.assertNotIn("candidate_ref", canonical(request).decode())
        self.data = self.runtime.call("start_verifier_run", {"source_path": str(self.source)})["data"]
        self.call("load_submitted_skill", source_path=str(self.source))
        self.snapshot = self.data["snapshot"]
        self.extract()
        with patch("sci_ai_verifier.local_candidates.fetch_public", side_effect=AssertionError("Must reuse offline")):
            self.call("list_local_candidates", claim_id=self.claim_id)
            self.assertEqual(self.data["candidates"][0]["candidate_ref"], key)
            self.select(key)
            self.call("execute_local_claim", claim_id=self.claim_id)

    def test_wrong_answers_fail_without_scientific_grade(self):
        self.subject.mode = "wrong"
        self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["result"]["comparison_status"], "fail")
        self.assertIsNone(self.data["result"]["scientific_status"])

    def test_interrupted_trial_is_retained_and_never_replayed(self):
        self.subject.mode = "interrupt"
        self.ready()
        with self.assertRaises(KeyboardInterrupt):
            self.call("execute_local_claim", claim_id=self.claim_id)
        self.data = self.runtime.call("resume_verifier_run", {"run_id": self.data["run_id"]})["data"]
        self.subject.mode = "correct"
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["outcome"], "interrupted_subject_execution")
        self.assertEqual(len(self.subject.requests), 1)
        self.call("write_report_card")

    def test_unverified_invocation_is_operational(self):
        self.subject.mode = "unverified"
        self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["outcome"], "subject_response_invalid")
        self.assertEqual(len(self.subject.requests), 1)

    def test_zero_claims_complete_without_calls(self):
        self.extract(0)
        self.call("write_report_card")
        self.assertEqual(self.data["report"]["claims"], [])
        self.assertFalse(self.subject.requests)

    def test_mixed_claims_account_for_unsupported_work(self):
        self.extract(2)
        key = self.candidate()
        self.select(key)
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["run_state"], "active")
        self.call("record_local_limitation", claim_id=self.claims[1]["claim_id"], code="no_independent_reference_available", reason="No qualified independent method")
        self.call("write_report_card")
        self.assertEqual(len(self.data["report"]["claims"]), 2)

    def test_unsupported_method_saved_as_rejected(self):
        self.extract()
        self.candidate(method="execute-python")
        self.assertEqual(self.data["outcome"], "rejected")
        self.assertTrue(self.data["candidate"]["qualification_problems"])

    def test_unfetched_or_invented_reference_fails_qualification(self):
        self.extract()
        cases = [{"case_id": str(i), "input": str(i), "expected": str(i), "reference_ref": "0"*64,
                  "source_quote": "Invented quote", "applicability": "Unsupported"} for i in range(3)]
        self.candidate(cases=cases)
        self.assertEqual(self.data["outcome"], "rejected")

    def test_stale_token_cannot_execute_subject(self):
        self.ready()
        response = self.runtime.call("execute_local_claim", {"run_id": self.data["run_id"], "state_token": "old", "claim_id": self.claim_id})
        self.assertEqual(response["status"], "retryable")
        self.assertFalse(self.subject.requests)

    def test_context_recovery_returns_pinned_candidate_content(self):
        candidate_ref = self.ready()
        header = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"]})["data"]
        # The header must always fit inline: bulk sections are named, not inlined.
        self.assertLessEqual(len(canonical(header)), 8000)
        self.assertEqual(header["authorized_parameters"]["source_path"], str(self.source))
        self.assertNotIn("local_artifacts", header)
        self.assertIn("local_artifacts", header["fetchable_sections"])
        self.assertEqual(header["local_work"][self.claim_id]["candidate_ref"], candidate_ref)
        section = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"],
                                                             "section": "local_artifacts"})["data"]["section"]
        self.assertIn("Fixture table", section["content"])
        self.assertFalse(section["truncated"])
        unknown = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"],
                                                             "section": "nonexistent"})
        self.assertEqual(unknown["error"]["code"], "unknown_context_section")

    def test_runtime_change_cannot_reuse_existing_plan(self):
        self.ready()
        with patch("sci_ai_verifier.storage.implementation_bytes", return_value=b"changed"):
            self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["outcome"], "method_changed")
        self.assertFalse(self.subject.requests)

    def test_secret_in_proposal_is_not_saved(self):
        self.extract()
        self.call("list_local_candidates", claim_id=self.claim_id)
        secret = "sk-ant-" + "x"*30
        response = self.runtime.call("record_local_limitation", {"run_id": self.data["run_id"], "state_token": self.data["state_token"],
                          "claim_id": self.claim_id, "code": "reference_retrieval_failed", "reason": secret})
        self.assertEqual(response["status"], "retryable")
        for file in self.runtime.store.root.rglob("*"):
            if file.is_file():
                self.assertNotIn(secret.encode(), file.read_bytes())

    def test_candidate_projection_tampering_fails_closed(self):
        self.ready()
        path = next((self.runtime.store.root / "candidates").glob("*.json"))
        path.write_text("{}")
        from sci_ai_verifier.local_candidates import candidates
        with self.assertRaises(Fault):
            candidates(self.runtime.store)

    def test_no_bootstrap_reply_is_large_enough_for_a_host_to_spill(self):
        """The planner session has no file-read tool, so an oversized reply blocks it."""
        from sci_ai_verifier.agent import INLINE_BUDGET
        self.ready()
        for arguments in ({"run_id": self.data["run_id"]},
                          {"run_id": self.data["run_id"], "section": "local_artifacts"}):
            with self.subTest(arguments=sorted(arguments)):
                reply = self.runtime.call("get_verifier_context", arguments)
                self.assertEqual(reply["status"], "ok", reply)
                if "section" not in arguments:
                    self.assertLessEqual(len(canonical(reply)), INLINE_BUDGET)
        header = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"]})["data"]
        # The two things the planner cannot work without travel in the small reply.
        self.assertEqual(header["authorized_parameters"]["source_path"], str(self.source))
        self.assertTrue(header["state_token"])
        # Every pinned document is named with its digest and is separately fetchable.
        self.assertTrue(header["instructions"])
        for entry in header["instructions"]:
            section = self.runtime.call("get_verifier_context", {
                "run_id": self.data["run_id"], "section": entry["identity"]})["data"]["section"]
            self.assertEqual(section["trust_class"], "verifier_instruction")
            self.assertEqual(section["bytes_total"], entry["bytes"])

    def test_pinned_instructions_and_authorized_path_reach_the_planner_prompt(self):
        from sci_ai_verifier.local_entry import planner_prompt
        created = self.runtime.call("start_verifier_run", {"source_path": str(self.source)})["data"]
        prompt = planner_prompt(self.runtime, created["run_id"], created)
        self.assertIn(str(self.source), prompt)
        self.assertIn(created["state_token"], prompt)
        for entry in created["instructions"]:
            self.assertIn(entry["digest"], prompt)
        # The contracts themselves arrive, not just their names.
        self.assertIn("Local profile", prompt)
        self.assertGreater(len(prompt), 20000)

    def test_wrong_source_path_is_repairable_and_does_not_close_the_run(self):
        created = self.runtime.call("start_verifier_run", {"source_path": str(self.source)})["data"]
        refused = self.runtime.call("load_submitted_skill", {
            "run_id": created["run_id"], "state_token": created["state_token"],
            "source_path": "SKILL.md"})
        self.assertEqual(refused["status"], "retryable")
        self.assertEqual(refused["error"]["code"], "source_not_authorized")
        self.assertEqual(refused["error"]["repair_fields"], ["source_path"])
        # The message names the path, and the run is still usable with it.
        self.assertIn(str(self.source), refused["error"]["message"])
        self.assertEqual(refused["error"]["run_state"], "created")
        loaded = self.runtime.call("load_submitted_skill", {
            "run_id": created["run_id"], "state_token": refused["error"]["state_token"],
            "source_path": str(self.source)})
        self.assertEqual(loaded["status"], "ok", loaded)
        self.assertEqual(loaded["data"]["run_state"], "source_ready")

    def test_public_tool_surface_and_internal_run_binding(self):
        public = PublicRuntime(workspace=self.base, instructions=ROOT / "skills/scientific-verifier")
        self.assertEqual([tool["name"] for tool in public.definitions], ["verify_skill"])
        server = Server(public)
        server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools], ["verify_skill"])
        bound = BoundRuntime(self.runtime, self.data["run_id"])
        self.assertEqual(bound.call("get_verifier_context", {"run_id": "other"})["status"], "retryable")

    def test_reference_url_rejects_private_credentials_and_redirects(self):
        for url in ("http://example.org", "https://user:pass@example.org", "https://example.org:44", "https://example.org/#fragment", "https://[bad"):
            with self.subTest(url=url), self.assertRaises(Fault):
                fetch_public(url)
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]), self.assertRaises(Fault):
            fetch_public("https://example.org")


class ReportAxisTests(unittest.TestCase):
    """The card must render every axis shape, including ones that hold no measurement."""

    @staticmethod
    def render(record):
        from sci_ai_verifier.local import axis_lines
        return "\n".join(axis_lines(record, str))

    def test_a_flaky_claim_reports_its_grade_accuracy_and_split(self):
        text = self.render({"scientific_status": "fail", "evidence_grade": "A",
                            "accuracy": {"matched": 13, "evaluated": 15},
                            "consistency": {"label": "split", "unanimous_cases": 3, "split_cases": 2},
                            "completeness": {"obtained": 15, "planned": 15},
                            "aggregation_rule": "unanimity", "fault": None,
                            "execution_limit_reasons": ["trial_agreement_below_policy"]})
        self.assertIn("Accuracy: 13 of 15", text)
        self.assertIn("split (2 split of 5 cases)", text)
        self.assertIn("unanimity", text)
        self.assertIn("not the reference", text)

    def test_paths_that_never_measure_behaviour_render_their_sentinel(self):
        """`not_applicable` and `not_obtained` arrive as bare strings, not dicts."""
        for sentinel, withheld in (("not_applicable", None), ("not_obtained", "not_executed")):
            text = self.render({"scientific_status": None, "status_withheld_reason": withheld,
                                "accuracy": sentinel, "consistency": sentinel, "completeness": sentinel})
            self.assertIn("consistency: " + sentinel, text)
            self.assertEqual("withheld" in text, withheld is not None)

    def test_a_record_written_before_the_axes_existed_still_renders(self):
        self.assertEqual(self.render({"scientific_status": "pass", "evidence_grade": "A"}), "")

    def test_a_runner_fault_is_named_as_ours(self):
        text = self.render({"scientific_status": None, "status_withheld_reason": "unattributable_observations",
                            "evidence_grade": "B", "fault": "subject_model_changed"})
        self.assertIn("Status withheld: unattributable_observations", text)
        self.assertIn("ours, not the skill's", text)


class TruncatedRunTests(unittest.TestCase):
    """A fault discards the trials that completed before it; decided 2026-09-21.

    A prefix of a plan is not the plan the critique reviewed, and which cases survived is
    decided by where the failure landed. Reporting accuracy over that subset would look
    like a measurement while describing an arbitrary sample, so the observations stay in
    the receipts and are never promoted to an axis.
    """

    def record(self, code, receipts):
        from sci_ai_verifier.local import limitation
        captured = {}

        class Store:
            def get_json(self, key):
                return {}

            def put_json(self, value):
                captured.update(value)
                return "ref"
        state = {"local_work": {"c1": {}}, "claim_states": {}, "objects": []}
        with patch("sci_ai_verifier.local.keep", side_effect=lambda s, st, v: captured.update(v) or "ref"):
            limitation(Store(), state, "c1", code, "reason", receipts)
        return captured

    def test_surviving_trials_are_retained_as_receipts_but_never_scored(self):
        record = self.record("subject_model_changed", ["obs-1", "obs-2", "obs-3", "obs-4"])
        self.assertEqual(record["accuracy"], "not_obtained")
        self.assertEqual(record["consistency"], "not_obtained")
        self.assertIsNone(record["evidence_grade"])
        self.assertIsNone(record["scientific_status"])
        self.assertEqual(record["receipts"], ["obs-1", "obs-2", "obs-3", "obs-4"])

    def test_the_withheld_reason_names_the_fault_that_caused_it(self):
        self.assertEqual(self.record("subject_model_changed", [])["status_withheld_reason"],
                         "unattributable_observations")
        self.assertEqual(self.record("sandbox_image_unavailable", [])["status_withheld_reason"],
                         "not_executed")
        self.assertEqual(self.record("sandbox_image_unavailable", [])["fault"], "sandbox_image_unavailable")


if __name__ == "__main__":
    unittest.main()
