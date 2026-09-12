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

    def __init__(self, mode="correct"):
        self.mode, self.requests = mode, []

    def observe(self, **request):
        self.requests.append(deepcopy(request))
        if self.mode == "interrupt":
            raise KeyboardInterrupt()
        if self.mode == "unavailable":
            raise Fault("claude_unavailable", "Unavailable fixture")
        answer = {"alpha": "1.0", "beta": "2.0", "gamma": "3.0"}[request["case_input"]["input"]]
        return {"text": "999" if self.mode == "wrong" else answer,
                "response_id": "synthetic-" + str(len(self.requests)), "model_id": "synthetic",
                "invocation_verified": self.mode != "unverified", "synthetic": True}


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

    def candidate(self, **overrides):
        self.call("list_local_candidates", claim_id=self.claim_id)
        with patch("sci_ai_verifier.local_candidates.fetch_public", return_value=(REFERENCE.encode(), REFERENCE)):
            self.call("fetch_local_reference", claim_id=self.claim_id, url="https://example.org/reference", version="fixture-v1", license="Unknown; private analysis only")
        reference_ref = self.data["reference_ref"]
        arguments = {"claim_id": self.claim_id, "name": "Fixture table", "scope": "Reference-table queries", "method": "numeric",
                     "limitations": "Fictional reference demonstrates mechanics only.",
                     "cases": [{"case_id": name, "input": name, "expected": str(index)+".0", "reference_ref": reference_ref,
                                "source_quote": REFERENCE, "applicability": "Fixture table row"}
                               for index, name in enumerate(("alpha", "beta", "gamma"), 1)]}
        arguments.update(overrides)
        self.call("qualify_local_candidate", **arguments)
        return self.data["candidate_ref"]

    def ready(self):
        self.extract()
        key = self.candidate()
        self.assertEqual(self.data["outcome"], "qualified_local")
        self.call("select_local_candidate", claim_id=self.claim_id, candidate_ref=key, applicability="Synthetic fixture scope")
        return key

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
        self.assertEqual(resumed["data"]["report"], self.data["report"])
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
            self.call("select_local_candidate", claim_id=self.claim_id, candidate_ref=key, applicability="Same scope")
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
        self.call("select_local_candidate", claim_id=self.claim_id, candidate_ref=key, applicability="Fixture scope")
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["run_state"], "active")
        self.call("record_local_limitation", claim_id=self.claims[1]["claim_id"], code="unsupported_method", reason="No qualified independent method")
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
        response = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"]})
        artifacts = response["data"]["local_artifacts"][self.claim_id]
        self.assertEqual(artifacts["candidate_ref"]["name"], "Fixture table")
        self.assertEqual(response["data"]["local_work"][self.claim_id]["candidate_ref"], candidate_ref)

    def test_runtime_change_cannot_reuse_existing_plan(self):
        self.ready()
        with patch("sci_ai_verifier.scientific.implementation_bytes", return_value=b"changed"):
            self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["outcome"], "method_changed")
        self.assertFalse(self.subject.requests)

    def test_secret_in_proposal_is_not_saved(self):
        self.extract()
        self.call("list_local_candidates", claim_id=self.claim_id)
        secret = "sk-ant-" + "x"*30
        response = self.runtime.call("record_local_limitation", {"run_id": self.data["run_id"], "state_token": self.data["state_token"],
                          "claim_id": self.claim_id, "code": "unavailable", "reason": secret})
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


if __name__ == "__main__":
    unittest.main()
