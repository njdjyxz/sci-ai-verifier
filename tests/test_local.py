"""Local workflow acceptance: real persistence, synthetic independent observations."""

import base64
import json
import re
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import Fault, canonical, digest
from sci_ai_verifier.local_entry import BoundRuntime, PublicRuntime
from sci_ai_verifier.local_candidates import fetch_public
from sci_ai_verifier.local_tasks import RESULTS_FILE, RESULTS_INSTRUCTION
from sci_ai_verifier.mcp import Server

ROOT = Path(__file__).resolve().parents[1]
QUOTE = "The skill returns a plain decimal for each reference-table query."
# Two sections, so a manifest can hold two claims ("Claims" in local-tasks.md).
SKILL = QUOTE + "\n\n## Notes\nThe skill also documents its decimal output.\n"
REFERENCE = "Independent fixture reference: alpha is 1.0, beta is 2.0, gamma is 3.0, zeta is 4.0, eta is 5.0."
TABLE = {"alpha": "1.0", "beta": "2.0", "gamma": "3.0", "zeta": "4.0", "eta": "5.0"}
# Two counting tasks suffice for B and C; grade A needs three, per evidence-rubric.md.
ROWS = ("alpha", "beta", "gamma")
FIVE_ROWS = ROWS + ("zeta", "eta")
IMAGE = "sha256:" + "b" * 64


def row_of(given):
    """The table row a task's job names."""
    return re.search(r"value for (\w+)\.", given["task"]).group(1)


def results(value):
    """A results file holding `value`, as a trial or the reference solution writes it."""
    return json.dumps({"value": value}).encode()


def task(name, sections, reference_ref):
    """One task: report a row of the fixture table, its value quoted from the fixture reference."""
    return {"case_id": name, "job": "Report the fixture table's value for " + name + ".", "sections": sections,
            "outputs": [{"field": "value", "type": "number", "value": TABLE[name], "reference_ref": reference_ref,
                         "source_quote": REFERENCE}],
            "applicability": "Fixture table row"}


class TableRunner:
    """Stands in for the operator's container: the reference solution looks each row up in the table."""

    def __init__(self, settings=None, *, log=None, sandbox_factory=None, solver_image=None):
        pass

    def generate(self, code, arguments):
        raise AssertionError("The fixture's tasks quote their values and have no generator.")

    def solve(self, code, given, files):
        return {"exit_code": 0, "stderr": "", "results": results(float(TABLE[row_of(given)])), "image_id": IMAGE}


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
        # "silent" writes no results file, so its trial is unreadable rather than wrong.
        value = 999.0 if self.mode == "wrong" else float(TABLE[row_of(request["case_input"])])
        written = [] if self.mode == "silent" else [results(value)]
        observation = {"text": "Wrote the results file.", "response_id": "synthetic-" + str(len(self.requests)),
                       "model_id": "synthetic", "invocation_verified": self.mode != "unverified", "synthetic": True,
                       "artifacts": [{"path": RESULTS_FILE, "sha256": digest(raw), "bytes": len(raw),
                                      "base64": base64.b64encode(raw).decode()} for raw in written]}
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
        (self.source / "SKILL.md").write_text(SKILL, encoding="utf-8")
        # No container runs here: the reference solution is the table lookup above.
        runner = patch("sci_ai_verifier.local_tasks.SandboxRunner", TableRunner)
        runner.start()
        self.addCleanup(runner.stop)
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
        # Every section goes in one claim, the last claim taking the rest; with no claim, all are set aside.
        from sci_ai_verifier.claims import skill_sections
        names = [item["section"] for item in skill_sections(self.runtime.store, self.snapshot)]
        groups = [names[i:i + 1] if i < count - 1 else names[i:] for i in range(count)]
        self.call("commit_claim_manifest", snapshot_id=self.snapshot["id"], snapshot_digest=self.snapshot["digest"],
                  claims=[{"statement": QUOTE if i == 0 else "The skill returns a decimal.", "scope": "Reference-table queries",
                           "expected_behavior": "Plain decimal", "source_path": "SKILL.md", "source_quote": QUOTE,
                           "report_note": "Synthetic acceptance", "sections": groups[i]} for i in range(count)],
                  set_aside=[] if count else [{"section": name, "reason": "Synthetic: nothing to test."} for name in names])
        self.claims = self.data["manifest"]["claims"]
        self.claim_id = self.claims[0]["claim_id"] if self.claims else None

    def candidate(self, *, lookup=True, rows=ROWS, **overrides):
        # Lookup is legal only in local_lookup, so a second qualification skips it and
        # reuses the reference this claim already retrieved.
        if lookup:
            self.call("list_local_candidates", claim_id=self.claim_id)
            with patch("sci_ai_verifier.local_candidates.fetch_public", return_value=(REFERENCE.encode(), REFERENCE)):
                self.call("fetch_local_reference", claim_id=self.claim_id, url="https://example.org/reference", version="fixture-v1", license="Unknown; private analysis only")
            self.reference_ref = self.data["reference_ref"]
        sections = next(claim["sections"] for claim in self.claims if claim["claim_id"] == self.claim_id)
        arguments = {"claim_id": self.claim_id, "name": "Fixture table", "scope": "Reference-table queries",
                     "limitations": "Fictional reference demonstrates mechanics only.",
                     "solver": {"code": "print('fixture reference solution')"},
                     "cases": [task(name, sections, self.reference_ref) for name in rows]}
        arguments.update(overrides)
        self.call("qualify_local_tasks", **arguments)
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
        # The fourth call swaps again, so the end-of-run re-run meets the same fault.
        self.subject.models = [["fixture-model"], ["swapped-model"], ["fixture-model"], ["swapped-model"]]
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
        row = self.data["report"]["claims"][0]
        self.assertEqual(row["record"]["code"], "subject_model_changed")
        self.assertIsNone(row["record"]["evidence_grade"])
        self.assertEqual((row["retry"]["status"], row["retry"]["outcome"]), ("retried", "subject_model_changed"))

    def test_a_trial_answered_by_two_models_is_refused_at_once(self):
        """Run 3dc02567 pinned [opus-4-8, opus-5] from trial 1 and scored trial 2 as stable."""
        self.subject.models = [["fixture-model", "other-model"]]
        self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["outcome"], "subject_model_changed")
        self.assertIn("not by exactly one model", self.data["limitation"]["reason"])
        self.assertEqual(len(self.subject.requests), 1)

    def test_a_cli_notice_is_not_a_model(self):
        """A refusal the pinned model then answered itself leaves a `<synthetic>` notice."""
        self.subject.models = [["<synthetic>", "fixture-model"], ["fixture-model"]]
        self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["result"]["comparison_status"], "pass")

    def test_empty_catalog_discovery_complete_report_and_offline_reuse(self):
        key = self.ready()
        self.call("execute_local_claim", claim_id=self.claim_id)
        self.assertEqual(self.data["result"]["comparison_status"], "pass")
        self.assertIsNone(self.data["result"]["evidence_grade"])
        self.call("write_report_card")
        self.assertTrue(self.data["verification_complete"])
        report_path = Path(self.data["report_markdown_path"])
        self.assertIn("SYNTHETIC", report_path.read_text())
        self.assertIn("| alpha | 1 | pass | none | none | yes |", report_path.read_text())
        first = self.data["report"]["claims"][0]["tests"][0]
        self.assertEqual((first["expected"], first["outputs"][0]["found"]), ({"value": "1.0"}, 1.0))
        report_path.unlink()
        resumed = self.runtime.call("resume_verifier_run", {"run_id": self.data["run_id"]})
        self.assertTrue(resumed["data"]["verification_complete"])
        report = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"],
                                                            "section": "report"})["data"]["section"]
        self.assertEqual(report["identity"], "report")
        self.assertIn("local", report["content"])
        self.assertTrue(report_path.exists())
        for request in self.subject.requests:
            # The task's job, paths and fields, and the line Python writes for every task, never the key.
            self.assertEqual(set(request["case_input"]),
                             {"task", "input_files", "results_file", "results_format", "answer_format"})
            self.assertEqual(request["case_input"]["answer_format"], RESULTS_INSTRUCTION)
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

    def test_a_design_qualified_under_retired_rules_is_not_offered(self):
        """Lookup reuses a saved design without re-qualifying it, so the version string is the only
        thing keeping one that passed retired rules, such as a design of questions, out of a later run."""
        from sci_ai_verifier.local_candidates import candidates, save_candidate
        key = self.ready()
        store = self.runtime.store
        self.assertTrue(any(item["candidate_ref"] == key for item in candidates(store)))
        stale = save_candidate(store, {**store.get_json(key), "method_version": "local-reference-comparison-3"})
        self.assertFalse(any(item["candidate_ref"] == stale for item in candidates(store)))

    def test_unfetched_or_invented_reference_fails_qualification(self):
        self.extract()
        self.call("list_local_candidates", claim_id=self.claim_id)
        self.reference_ref = "0" * 64  # Never fetched for this claim.
        self.candidate(lookup=False)
        self.assertEqual(self.data["outcome"], "rejected")
        self.assertIn("must be quoted exactly from a reference fetched for this claim",
                      " ".join(self.data["candidate"]["qualification_problems"]))

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

    def test_every_reply_to_the_planner_says_how_long_it_has_left(self):
        """Run 1d1c3b6e's planner, told nothing, called its deadline near with 62 of 120 minutes
        left, accepted a lowered grade and gave its last claim a documentary D untested."""
        import os
        import time
        from sci_ai_verifier.local import DEADLINE_ENV
        from sci_ai_verifier.local_entry import PLANNER_PROMPT
        bound = BoundRuntime(self.runtime, self.data["run_id"])
        with patch.dict(os.environ, {DEADLINE_ENV: str(int(time.time()) + 600)}):
            ok = bound.call("get_verifier_context", {"run_id": self.data["run_id"]})
            refused = bound.call("get_verifier_context", {"run_id": "other"})
        self.assertEqual(ok["status"], "ok")
        self.assertTrue(590 <= ok["data"]["attempt_seconds_remaining"] <= 600)
        self.assertTrue(590 <= refused["error"]["attempt_seconds_remaining"] <= 600)
        with patch.dict(os.environ, {DEADLINE_ENV: str(int(time.time()) - 5)}):
            self.assertEqual(bound.call("get_verifier_context", {"run_id": self.data["run_id"]})
                             ["data"]["attempt_seconds_remaining"], 0)
        # Nothing bounds an attempt the runner gave no deadline, so nothing is claimed.
        for value in (None, "", "not a time", "inf"):
            with self.subTest(deadline=value), patch.dict(os.environ, {}, clear=False):
                os.environ.pop(DEADLINE_ENV, None)
                if value is not None:
                    os.environ[DEADLINE_ENV] = value
                self.assertNotIn("attempt_seconds_remaining",
                                 bound.call("get_verifier_context", {"run_id": self.data["run_id"]})["data"])
        self.assertIn("attempt_seconds_remaining", " ".join(PLANNER_PROMPT.split()))
        pinned = dict(self.runtime._instruction_blocks())["references/local-contract.md"]
        self.assertIn("`attempt_seconds_remaining`", pinned)
        self.assertNotIn("90 minutes", pinned)

    def test_reference_url_rejects_private_credentials_and_redirects(self):
        for url in ("http://example.org", "https://user:pass@example.org", "https://example.org:44", "https://example.org/#fragment", "https://[bad"):
            with self.subTest(url=url), self.assertRaises(Fault):
                fetch_public(url)
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]), self.assertRaises(Fault):
            fetch_public("https://example.org")

    def test_a_refused_download_says_whether_it_was_size_or_a_credential(self):
        """Run b0955d2f's planner got one message for both causes and guessed which."""
        from sci_ai_verifier.local_candidates import bounded_download
        self.assertEqual(bounded_download(b"x" * 10, 10), b"x" * 10)
        with self.assertRaises(Fault) as caught:
            bounded_download(b"x" * 11, 10)
        self.assertEqual(caught.exception.code, "reference_too_large")
        with self.assertRaises(Fault) as caught:
            bounded_download(b"page " + b"sk-ant-" + b"x" * 30, 1000)
        self.assertEqual(caught.exception.code, "reference_credential_material")

    def test_every_pinned_instruction_document_fits_one_section_reply(self):
        """The planner reads each pinned document as one section, cut at the reply limit it cannot
        read past, so a document that outgrew the limit would lose its tail without a sign."""
        from sci_ai_verifier.local_candidates import REPLY_TEXT_BYTES
        for identity, content in self.runtime._instruction_blocks():
            with self.subTest(identity=identity):
                self.assertLessEqual(len(content.encode("utf-8")), REPLY_TEXT_BYTES)

    def test_a_long_page_is_pinned_whole_and_only_its_reply_is_cut(self):
        """A host spills a long reply to a file, and the planner has no tool to open it."""
        from sci_ai_verifier.local_candidates import REPLY_TEXT_BYTES
        self.extract()
        self.call("list_local_candidates", claim_id=self.claim_id)
        # The quoted rows sit past the cut, where only the pinned page holds them.
        page = "Filler line of a long documentation page.\n" * (REPLY_TEXT_BYTES // 40) + REFERENCE
        with patch("sci_ai_verifier.local_candidates.fetch_public", return_value=(page.encode(), page)):
            self.call("fetch_local_reference", claim_id=self.claim_id, url="https://example.org/long",
                      version="fixture-v1", license="Unknown; private analysis only")
        shown = self.data["untrusted_reference"]
        self.assertTrue(shown["text_truncated"])
        self.assertEqual(shown["text_bytes_total"], len(page.encode()))
        self.assertLessEqual(len(shown["text"].encode()), REPLY_TEXT_BYTES)
        self.assertNotIn(REFERENCE, shown["text"])
        # Quotes are checked against the whole pinned page, so its tail still qualifies.
        self.reference_ref = self.data["reference_ref"]
        self.candidate(lookup=False)
        self.assertEqual(self.data["outcome"], "qualified_local")
        # Re-reading the claim's artifacts as a section is held to the same reply limit.
        section = self.runtime.call("get_verifier_context", {"run_id": self.data["run_id"],
                                                              "section": "local_artifacts"})["data"]["section"]
        self.assertTrue(section["truncated"])
        self.assertLessEqual(len(section["content"].encode()), REPLY_TEXT_BYTES)

    def test_the_runner_records_who_closed_a_run(self):
        """Only the operator cancels; a planner that stopped by itself is agent_unavailable."""
        from sci_ai_verifier.partial_report import write_partial_report
        reason = "The planner stopped. Its last result reported api_error (HTTP 429): session limit."
        closed = self.runtime.call("cancel_verifier_run", {"run_id": self.data["run_id"]},
                                   closing=("agent_unavailable", reason))
        self.assertEqual((closed["error"]["code"], closed["error"]["message"]), ("agent_unavailable", reason))
        write_partial_report(self.runtime.store, self.data["run_id"], "planner_incomplete", reason)
        markdown = (self.runtime.store.run_dir(self.data["run_id"]) / "partial-report.md").read_text(encoding="utf-8")
        self.assertIn("Reason: " + reason, markdown)
        # With no runner reason the cancellation is the operator's, worded as it always was.
        second = self.runtime.call("start_verifier_run", {"source_path": str(self.source)})["data"]
        cancelled = self.runtime.call("cancel_verifier_run", {"run_id": second["run_id"]})
        self.assertEqual((cancelled["error"]["code"], cancelled["error"]["message"]),
                         ("cancelled", "The operator cancelled this run."))


class ClaimScopeTests(unittest.TestCase):
    """"Claims" in local-tasks.md: each claim a group of whole sections, nothing left out, at most twelve."""

    def setUp(self):
        self.h = LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)

    def claims(self, groups):
        return [{"statement": "The skill returns decimal number %d." % index, "scope": "Reference-table queries",
                 "expected_behavior": "Plain decimal", "source_path": "SKILL.md", "source_quote": QUOTE,
                 "report_note": "Synthetic acceptance", "sections": group} for index, group in enumerate(groups)]

    def commit(self, h, claims, set_aside=()):
        return h.runtime.call("commit_claim_manifest", {
            "run_id": h.data["run_id"], "state_token": h.data["state_token"], "snapshot_id": h.snapshot["id"],
            "snapshot_digest": h.snapshot["digest"], "claims": claims, "set_aside": list(set_aside)})

    def test_load_numbers_the_sections_a_manifest_must_hold(self):
        loaded = self.h.data  # load_submitted_skill's reply, from setUp
        self.assertEqual([(item["section"], item["heading"], item["level"], item["words"]) for item in loaded["sections"]],
                         [("S1", "(before the first heading)", 0, 11), ("S2", "Notes", 2, 7)])

    def test_every_section_goes_in_exactly_one_claim_or_is_set_aside(self):
        h = self.h
        for claims, aside, named in (
                (self.claims([["S1"]]), [], "left out: S2 'Notes'"),
                (self.claims([["S1", "S2"], ["S2"]]), [], "in more than one place: S2"),
                (self.claims([["S1"]]), [{"section": "S2", "reason": "x"}, {"section": "S9", "reason": "x"}],
                 "unknown: S9"),
                (self.claims([["S1", "S1", "S2"]]), [], "names one of its sections twice")):
            with self.subTest(named=named):
                refused = self.commit(h, claims, aside)
                self.assertEqual(refused["status"], "retryable", refused)
                self.assertEqual(refused["error"]["code"], "sections_incomplete")
                self.assertIn(named, refused["error"]["message"])
                h.data["state_token"] = refused["error"]["state_token"]
        accepted = self.commit(h, self.claims([["S1"]]), [{"section": "S2", "reason": "Notes only restate S1."}])
        self.assertEqual(accepted["status"], "ok", accepted)
        manifest = accepted["data"]["manifest"]
        self.assertEqual(manifest["claims"][0]["sections"], ["S1"])
        self.assertEqual(manifest["set_aside"], [{"section": "S2", "reason": "Notes only restate S1."}])
        self.assertEqual([item["section"] for item in manifest["sections"]], ["S1", "S2"])

    def test_a_local_manifest_holds_at_most_twelve_claims(self):
        from sci_ai_verifier.local import CLAIM_LIMIT_MESSAGE, MAX_CLAIMS
        self.assertEqual(MAX_CLAIMS, 12)
        h = self.h
        # A skill of thirteen sections, so thirteen claims can each hold one.
        (h.source / "SKILL.md").write_text(QUOTE + "".join("\n\n## Part %d\nText %d." % (n, n) for n in range(12)),
                                           encoding="utf-8")
        h.data = h.runtime.call("start_verifier_run", {"source_path": str(h.source)})["data"]
        h.call("load_submitted_skill", source_path=str(h.source))
        h.snapshot = h.data["snapshot"]
        self.assertEqual(len(h.data["sections"]), 13)
        refused = self.commit(h, self.claims([["S%d" % n] for n in range(1, 14)]))
        self.assertEqual((refused["error"]["code"], refused["error"]["message"]), ("too_many_claims", CLAIM_LIMIT_MESSAGE))
        h.data["state_token"] = refused["error"]["state_token"]
        accepted = self.commit(h, self.claims([["S%d" % n] for n in range(1, 13)]),
                               [{"section": "S13", "reason": "Synthetic: nothing to test."}])
        self.assertEqual(accepted["data"]["manifest"]["count"], 12)

    def test_the_local_planner_is_told_the_claim_scope_and_other_profiles_keep_theirs(self):
        from sci_ai_verifier.local_entry import BoundRuntime, PLANNER_PROMPT
        from sci_ai_verifier.tools import DEFINITIONS
        local = next(item for item in BoundRuntime.definitions if item["name"] == "commit_claim_manifest")
        self.assertIn("group of whole sections", local["description"])
        self.assertIn("at most 12", local["description"])
        self.assertIn("set_aside", local["inputSchema"]["properties"])
        self.assertIn("sections", local["inputSchema"]["properties"]["claims"]["items"]["properties"])
        shared = next(item for item in DEFINITIONS if item["name"] == "commit_claim_manifest")
        self.assertIn("atomic", shared["description"])
        self.assertNotIn("set_aside", shared["inputSchema"]["properties"])
        pinned = dict(self.h.runtime._instruction_blocks())["tool-definitions"]
        self.assertIn(json.dumps(local["description"])[1:-1], pinned)
        self.assertIn("every section in one", " ".join(PLANNER_PROMPT.split()))

    def test_the_local_planner_is_told_to_test_by_tasks_and_revise_before_accepting(self):
        """Claims covered 13% of the Western-blot skill's words, and run 90c60cbe's tries never ran the
        skill's own script, so each claim is now tested by tasks that run the skill."""
        from sci_ai_verifier.local_entry import PLANNER_PROMPT
        prompt = " ".join(PLANNER_PROMPT.split())
        self.assertIn("qualify_local_tasks", prompt)
        self.assertIn("Test each claim by running the skill", prompt)
        self.assertIn("answers every required revision", prompt)
        self.assertIn('"Negotiating the grade"', prompt)
        self.assertNotIn("fact by fact", prompt)
        pinned = dict(self.h.runtime._instruction_blocks())
        self.assertIn("**A claim is a group of whole sections**", pinned["references/local-tasks.md"])
        self.assertIn("## The reference solution", pinned["references/local-tasks.md"])
        self.assertNotIn("**Tested fact by fact.**", pinned["references/local-contract.md"])
        self.assertNotIn("At most five", pinned["references/local-contract.md"])
        self.assertIn("In the local profile a case is a task", pinned["references/evidence-rubric.md"])
        self.assertIn("**Revise before accepting.**", pinned["references/evidence-rubric.md"])
        self.assertIn("saving run time is no reason", pinned["references/evidence-rubric.md"])
        self.assertIn("`qualify_local_tasks`", pinned["references/tool-contracts.md"])

    def test_a_skill_file_s_sections_are_its_headings_outside_code(self):
        from sci_ai_verifier.claims import sections
        text = ("---\nname: fixture\n---\nIntro line.\n# Title\nAbout.\n## Concepts\n### Rings\nRing text.\n"
                "```python\n# not a heading\nx = 1\n```\n## Workflow ##\nSteps.\n")
        found = [(item["heading"], item["level"], item["line"]) for item in sections(text)]
        # Frontmatter is no section, an empty parent heading is skipped, and a closing `##` is dropped.
        self.assertEqual(found, [(None, 0, 4), ("Title", 1, 5), ("Rings", 3, 8), ("Workflow", 2, 14)])
        self.assertEqual(sections(text)[0]["body"], ["Intro line."])
        # Frontmatter straight before the first heading, as in sar-analysis, leaves no section behind.
        self.assertEqual([item["heading"] for item in sections("---\nname: fixture\n---\n# Title\nAbout.\n")],
                         ["Title"])

    def test_the_report_says_which_sections_the_claims_hold_and_which_are_set_aside(self):
        h = self.h
        h.ready()
        h.call("execute_local_claim", claim_id=h.claim_id)
        h.call("write_report_card")
        report = h.data["report"]
        self.assertEqual(report["coverage"]["uncovered"], [])
        self.assertEqual(report["claims"][0]["sections"], ["(before the first heading)", "Notes"])
        markdown = Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Skill sections: the claims hold 2 of the 2 sections of SKILL.md.", markdown)
        self.assertIn("Skill sections: (before the first heading); Notes", markdown)
        # With no claim, every section is set aside, and the report says why.
        h.data = h.runtime.call("start_verifier_run", {"source_path": str(h.source)})["data"]
        h.call("load_submitted_skill", source_path=str(h.source))
        h.snapshot = h.data["snapshot"]
        h.extract(0)
        h.call("write_report_card")
        aside = h.data["report"]["coverage"]["set_aside"]
        self.assertEqual([(item["section"], item["reason"]) for item in aside],
                         [("S1", "Synthetic: nothing to test."), ("S2", "Synthetic: nothing to test.")])
        self.assertIn("set aside: S1 (before the first heading) (Synthetic: nothing to test.)",
                      Path(h.data["report_markdown_path"]).read_text(encoding="utf-8"))


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
