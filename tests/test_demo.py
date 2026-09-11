"""General-skill demo protocol tests; scripted outputs are not a live Chat acceptance."""

import json
import tempfile
import unittest
from pathlib import Path

import test_stage2 as stage2
from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import canonical

QUOTE = "Convert comma-separated words into a JSON list of trimmed nonempty strings."


class DemoTests(unittest.TestCase):
    start = stage2.Stage2Tests.start
    call = stage2.Stage2Tests.call
    load = stage2.Stage2Tests.load
    parent_args = stage2.Stage2Tests.parent_args

    def setUp(self):
        parent = stage2.ROOT / ".verifier/test-work"
        parent.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="general-demo-", dir=parent)
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.sources = self.base / "default-submissions"
        self.sources.mkdir()
        self.skill = self.base / "user-selected-skill-outside-default-folder"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text(QUOTE, encoding="utf-8")
        self.runtime = Runtime(self.base / "data", self.sources, stage2.INSTRUCTIONS, profile="demo")

    def ok(self, data, name, **args):
        result = self.call(data, name, **args)
        self.assertEqual(result["status"], "ok", result)
        return result["data"]

    def claimed(self, *, inline=False, empty=False):
        if inline:
            response = self.runtime.call("start_inline_demo_run", {"source_name": "Attached list skill", "source_text": QUOTE})
            self.assertEqual(response["status"], "ok", response)
            data = response["data"]
            path = next(block["content"]["source_path"] for block in data["context_blocks"] if block["identity"] == "authorized-parameters")
            data = self.ok(data, "load_submitted_skill", source_path=path)
        else:
            data = self.load()
        return self.ok(data, "commit_claim_manifest", **self.parent_args(data), claims=[] if empty else [
            {"statement": QUOTE, "scope": "comma-separated text", "expected_behavior": "JSON list of trimmed nonempty strings",
             "source_path": "SKILL.md", "source_quote": QUOTE, "report_note": "General behavior; no scientific assertion"}])

    def planned(self, count=1, inline=False):
        data = self.claimed(inline=inline)
        claim = data["manifest"]["claims"][0]
        return self.ok(data, "commit_demo_plan", manifest_id=data["manifest"]["id"], summary="Demonstrate list conversion",
                       tests=[{"claim_id": claim["claim_id"], "input": "apple, pear, , orange", "purpose": f"Whitespace/empty entry case {i+1}",
                               "checks": [{"kind": "json", "description": "Valid complete JSON", "expected": ""},
                                          {"kind": "review", "description": "Trim words and remove empty entries", "expected": ""}]}
                              for i in range(count)])

    def observed(self, data=None, *, output='["apple", "pear", "orange"]', assessment="met_expectations", test_index=0):
        data = data or self.planned()
        plan = data["demo_plan"]
        return self.ok(data, "record_demo_observation", plan_id=plan["id"], test_id=plan["tests"][test_index]["test_id"],
                       output=output, assessment=assessment, reason="Scripted protocol acceptance; no live Chat execution claimed")

    def test_general_nonchemical_skill_to_complete_report(self):
        data = self.ok(self.observed(), "write_report_card")
        self.assertEqual(data["run_state"], "completed")
        report = data["report"]
        self.assertEqual(report["counts"]["met_expectations"], 1)
        self.assertFalse(report["independent_verification"])
        self.assertIsNone(report["scientific_grade"])
        self.assertEqual(report["assessment_basis"], "same_chat_demo")
        self.assertEqual(report["examples"][0]["observation"]["output"], '["apple", "pear", "orange"]')
        self.assertIn("Same-chat demo", Path(data["report_markdown_path"]).read_text(encoding="utf-8"))
        state, _ = self.runtime.store.read(data["run_id"])
        self.assertNotIn("catalog_ref", state)

    def test_attached_text_reaches_report(self):
        data = self.ok(self.observed(self.planned(inline=True)), "write_report_card")
        self.assertEqual(data["report"]["submission_origin"]["kind"], "chat_supplied_text")
        self.assertFalse(data["report"]["submission_origin"]["original_attachment_attested"])

    def test_deterministic_failure_overrides_chat_success(self):
        data = self.observed(output="Not JSON")
        self.assertEqual(data["observation"]["proposed_assessment"], "met_expectations")
        self.assertEqual(data["observation"]["assessment"], "did_not_meet_expectations")

    def test_unavailable_capability_is_not_tested(self):
        data = self.ok(self.observed(output="", assessment="not_tested"), "write_report_card")
        self.assertEqual(data["report"]["counts"]["not_tested"], 1)
        self.assertTrue(data["report"]["claims"][0]["untested"])

    def test_duplicate_observation_cannot_replace_sample(self):
        data = self.planned(count=2)
        plan = data["demo_plan"]
        data = self.observed(data)
        result = self.call(data, "record_demo_observation", plan_id=plan["id"], test_id=plan["tests"][0]["test_id"],
                           output="changed", assessment="not_tested", reason="overwrite attempt")
        self.assertEqual(result["error"]["code"], "demo_observation_exists")
        resumed = self.runtime.call("get_verifier_context", {"run_id": data["run_id"]})["data"]
        self.assertEqual(resumed["demo_observations"][plan["tests"][0]["test_id"]]["output"], '["apple", "pear", "orange"]')
        data = self.observed(resumed, test_index=1)
        self.assertEqual(data["run_state"], "reporting")

    def test_cancel_preserves_previous_outputs(self):
        data = self.observed(self.planned(count=2))
        result = self.runtime.call("cancel_verifier_run", {"run_id": data["run_id"]})
        self.assertEqual(result["status"], "ok", result)
        report = result["data"]["report"]
        self.assertEqual((report["counts"]["met_expectations"], report["counts"]["not_tested"]), (1, 1))
        self.assertTrue(report["cancelled"])

    def test_cancel_before_plan_records_untested_claim(self):
        data = self.claimed()
        result = self.runtime.call("cancel_verifier_run", {"run_id": data["run_id"]})
        self.assertTrue(result["data"]["report"]["claims"][0]["untested"])

    def test_empty_behavior_report(self):
        data = self.ok(self.claimed(empty=True), "write_report_card")
        self.assertEqual(data["report"]["claims"], [])
        self.assertEqual(data["report"]["examples"], [])

    def test_report_and_plan_projections_recover(self):
        data = self.ok(self.observed(), "write_report_card")
        directory = self.runtime.store.run_dir(data["run_id"])
        (directory / "report-card.md").unlink()
        (directory / "demo-plan.json").unlink()
        self.runtime = Runtime(self.base / "data", self.sources, stage2.INSTRUCTIONS, profile="demo")
        result = self.runtime.call("resume_verifier_run", {"run_id": data["run_id"]})
        self.assertEqual(result["data"]["report"], data["report"])
        self.assertTrue((directory / "report-card.md").exists())
        self.assertTrue((directory / "demo-plan.json").exists())

    def test_missing_checks_and_unknown_claims_rejected(self):
        data = self.claimed()
        result = self.call(data, "commit_demo_plan", manifest_id=data["manifest"]["id"], summary="Invalid",
                           tests=[{"claim_id": data["manifest"]["claims"][0]["claim_id"], "input": "a", "purpose": "b", "checks": []}])
        self.assertEqual(result["error"]["code"], "invalid_arguments")
        data.update(result["error"])
        result = self.call(data, "commit_demo_plan", manifest_id=data["manifest"]["id"], summary="Invalid",
                           tests=[{"claim_id": "unknown", "input": "a", "purpose": "b", "checks": [{"kind":"review","description":"c","expected":""}]}])
        self.assertEqual(result["error"]["code"], "demo_coverage")

    def test_plans_cannot_be_changed_after_observation_begins(self):
        data = self.planned()
        result = self.call(data, "commit_demo_plan")
        self.assertEqual(result["error"]["code"], "illegal_transition")

    def test_original_source_is_immutable_after_load(self):
        data = self.planned()
        (self.skill / "SKILL.md").write_text("Changed source", encoding="utf-8")
        resumed = self.runtime.call("get_verifier_context", {"run_id": data["run_id"]})["data"]
        content = [b for b in resumed["context_blocks"] if b["identity"].startswith("snapshot:")]
        self.assertEqual(content[0]["content"]["content"], QUOTE)

    def test_demo_does_not_enable_scientific_tools(self):
        data = self.claimed()
        result = self.call(data, "find_registered_evaluators")
        self.assertEqual(result["error"]["code"], "illegal_transition")

    def test_inline_submission_not_enabled_in_legacy_profile(self):
        runtime = Runtime(self.base / "legacy-data", self.sources, stage2.INSTRUCTIONS)
        result = runtime.call("start_inline_demo_run", {"source_name": "test", "source_text": QUOTE})
        self.assertEqual(result["error"]["code"], "demo_profile_required")

    def test_report_output_fences_do_not_allow_markdown_escape(self):
        output = '```\n<script>untrusted</script>\n```'
        data = self.ok(self.observed(output=output), "write_report_card")
        text = Path(data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn('````\n' + output + '\n````', text)

    def test_bootstrap_has_demo_contract_and_stays_compact(self):
        data = self.start()
        self.assertIn("references/demo-contract.md", {block["identity"] for block in data["context_blocks"]})
        self.assertLess(len(canonical(data)), 140_000)


if __name__ == "__main__":
    unittest.main()
