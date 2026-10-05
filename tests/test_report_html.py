"""The HTML run report: drawn only from a run's records, every recorded string escaped, text written
after the run marked as such, and written after every completed run unless the caller declines."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci_ai_verifier import report_html  # noqa: E402
from sci_ai_verifier.common import Fault, validate  # noqa: E402
from sci_ai_verifier.local_entry import PublicRuntime, verify  # noqa: E402

RUN = "11111111-2222-3333-4444-555555555555"
CANDIDATE, REFERENCE = "c" * 64, "r" * 64
HOSTILE = "<script>alert(1)</script>"
QUESTION = "Two forms are on the blot. One of them is modified. Which one is the answer? 1. alpha 2. beta"


def trial(case_id, number, observed, status, counted=True):
    return {"case_id": case_id, "trial": number, "observed": observed, "comparison_status": status,
            "python_status": status, "read_by": "python", "counted": counted, "input": QUESTION,
            "expected": "2" if case_id == "c_choice" else "beta", "reference_ref": REFERENCE,
            "reference_quote": "beta is the answer", "session_id": f"{case_id}-{number}"}


class ReportHtmlTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / ".verifier" / "test-work"
        parent.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix="html-", dir=parent)
        self.addCleanup(temp.cleanup)
        self.workspace = Path(temp.name)
        verifier = self.workspace / ".verifier"
        self.run_dir = verifier / "runs" / RUN
        (self.run_dir / "events").mkdir(parents=True)
        (verifier / "store").mkdir()
        (verifier / "store" / CANDIDATE).write_text(json.dumps({"method": "mixed", "cases": [
            {"case_id": "c_choice", "method": "choice", "options": ["alpha", "beta", "none of these"]},
            {"case_id": "c_term", "method": "term"}]}), encoding="utf-8")
        verdicts = [{"case_id": "c_choice", "verdict": "counts", "reason": "tests the claim"},
                    {"case_id": "c_term", "verdict": "leaked", "reason": "the stem names it"}]
        tested = {
            "claim": {"claim_id": "claim-1", "statement": "First claim <b>bold</b>",
                      "scope": "Covers the first rule. Not specified for anything else."}, "sections": ["Intro"],
            "record": {"evidence_grade": "B", "scientific_status": "fail", "candidate_ref": CANDIDATE,
                       "accuracy": {"evaluated": 3, "matched": 2}, "consistency": {"label": "split"},
                       "uncounted_cases": [verdicts[1]], "limitations": ["recorded limit"]},
            "audit": {"critique": {"case_verdicts": verdicts, "coverage_gaps": ["one fact untested"],
                                   "claim_probe": {"cases": [{"case_id": "c_choice", "outcome": "reached",
                                                              "samples": [{"answer": "2"}, {"answer": "2"}]}]}}},
            "references": {REFERENCE: {"url": "javascript:alert(1)", "version": "a hostile source"}},
            "tests": [trial("c_choice", 1, "2", "pass"), trial("c_choice", 2, "2", "pass"),
                      trial("c_choice", 3, HOSTILE, "fail"), trial("c_term", 1, "beta", "pass", counted=False)]}
        documentary = {
            "claim": {"claim_id": "claim-2", "statement": "Second claim"}, "sections": ["Later"], "tests": [],
            "record": {"evidence_grade": "D", "scientific_status": "inconclusive"}, "audit": None,
            "documentary_assessment": {"assessment": {"status": "inconclusive", "findings": ["a finding"],
                                                      "citations": [{"quote": "cited words"}]}}}
        report = {"run_id": RUN, "claims": [tested, documentary], "workflow_log": {},
                  "subject": {"model_id": "fixture-model"}, "environment": {},
                  "host_limitations": ["evidence_grade_is_an_evidence_strength_indicator_not_an_endorsement"],
                  "coverage": {"sections": [{"heading": "Intro", "level": 1, "claims": ["claim-1"]},
                                            {"heading": "Later", "level": 1, "claims": ["claim-2"]},
                                            {"heading": "Untouched", "level": 1, "claims": []}]}}
        (self.run_dir / "report-card.json").write_text(json.dumps(report), encoding="utf-8")
        (self.run_dir / "run.json").write_text(json.dumps({
            "run_id": RUN, "source_path": "C:/skills/fixture-skill", "created_at": "2026-10-01T00:00:00+00:00",
            "subject_calls_used": 4, "local_method_ref": "abcdef1234567890"}), encoding="utf-8")
        (self.run_dir / "events" / "00000001.json").write_text(json.dumps({
            "created_at": "2026-10-01T00:01:00+00:00",
            "request": {"tool": "select_local_candidate", "arguments": {"claim_id": "claim-1", "target_grade": "A"}},
            "result": {"status": "ok", "data": {"outcome": "local_plan_fixed", "audit": {"critique": {
                "supported_grade": "B", "case_verdicts": verdicts, "coverage_gaps": ["one fact untested"]}}}}}),
            encoding="utf-8")

    def render(self, notes=None):
        return report_html.page(report_html.Run(self.workspace, RUN[:8]), notes or {})

    def test_every_recorded_string_is_escaped_and_nothing_can_run(self):
        page = self.render()
        self.assertNotIn("<script", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertNotIn('href="javascript', page)
        self.assertIn("First claim &lt;b&gt;bold&lt;/b&gt;", page)

    def test_each_claim_is_a_chapter_with_one_row_per_test(self):
        page = self.render()
        self.assertIn('id="claim-1"', page)
        self.assertIn('id="claim-2"', page)
        self.assertEqual(page.count("<div class=\"id\">"), 2, "one row per test, not per try")
        self.assertIn("2 · beta", page, "a choice key shows the option it names")
        self.assertIn("No — the question gives the answer away", page)
        self.assertIn("2 of 3", page)
        self.assertIn("A→B", page, "the planner's grade and the reviewer's, per round")
        self.assertIn("No tests ran", page)
        self.assertIn("1 of 3 sections of the skill had no claim: Untouched.", page)

    def test_without_notes_the_long_claim_folds_away_and_a_test_shows_its_question(self):
        """The planner's statement is written to be tested, not read: 150 words in run 90c60cbe."""
        page = self.render()
        self.assertIn("No plain summary yet", page)
        self.assertIn("The planner's scope: Covers the first rule.", page)
        self.assertNotIn("Not specified for anything else", page)
        statement = page.index("First claim &lt;b&gt;")
        self.assertGreater(statement, page.index("The full claim, as the planner wrote it"))
        self.assertIn("Which one is the answer?", page)
        self.assertNotIn("Two forms are on the blot. One of them is modified. Which", page.split("<h3>Each test")[0])

    def test_text_written_after_the_run_is_shown_and_marked(self):
        notes = {"by": "Claude", "author": "Written by Claude after the fixture run",
                 "skill": {"name": "Fixture skill", "summary": ["It does one thing."]},
                 "claims": {"1": {"title": "The first rule", "says": ["It says this."], "summary": ["It went so."],
                                  "tests": {"c_choice": {"asks": "Which one?", "review": "The key holds."}}}},
                 "cautions": ["Read with care."]}
        page = self.render(notes)
        for words in ("Fixture skill", "It does one thing.", "The first rule", "It says this.", "It went so.",
                      "Which one?", "The key holds.", "Read with care.", "Written by Claude after the fixture run"):
            self.assertIn(words, page)
        self.assertIn("✎ written by Claude", page)
        self.assertEqual(page.count("No plain summary yet"), 1, "only the unsummarized second claim says so")

    def test_the_same_records_give_the_same_page(self):
        self.assertEqual(self.render(), self.render())

    def test_publishing_writes_the_page_and_notes_to_fill_and_keeps_written_notes(self):
        published = report_html.publish(self.workspace, RUN)
        page, notes = Path(published["path"]), Path(published["notes_path"])
        self.assertTrue(page.is_file())
        self.assertNotIn(b"\r\n", page.read_bytes())
        template = json.loads(notes.read_text(encoding="utf-8"))
        claim = template["claims"]["1"]
        self.assertEqual((claim["title"], claim["says"], claim["summary"]), ("", [], []))
        self.assertEqual(claim["claim_as_written"], "First claim <b>bold</b>")
        self.assertEqual(claim["tests"]["c_choice"]["question"], QUESTION)
        self.assertEqual(claim["tests"]["c_choice"]["asks"], "")
        self.assertIn("Do not quote the skill", template["guide"])
        self.assertIn(RUN, published["render_command"])
        self.assertIn("notes_path", published["next_step"])
        # A written summary survives publishing again, and the page shows it.
        template["claims"]["1"]["title"] = "The first rule"
        notes.write_text(json.dumps(template), encoding="utf-8")
        report_html.publish(self.workspace, RUN)
        self.assertEqual(json.loads(notes.read_text(encoding="utf-8"))["claims"]["1"]["title"], "The first rule")
        self.assertIn("The first rule", page.read_text(encoding="utf-8"))

    def test_a_run_without_a_report_card_says_so(self):
        (self.run_dir / "report-card.json").unlink()
        (self.run_dir / "partial-report.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(report_html.ReportUnavailable) as stopped:
            report_html.Run(self.workspace, RUN)
        self.assertIn("stopped early", str(stopped.exception))
        with self.assertRaises(SystemExit) as command:
            report_html.main([RUN, "--workspace", str(self.workspace)])
        self.assertIn("stopped early", str(command.exception))

    def test_a_completed_verification_gets_its_page_unless_the_caller_declines(self):
        finished = {"status": "ok", "data": {"run_id": RUN, "verification_complete": True}}
        settings = {"workspace": self.workspace, "instructions": ROOT / "skills/scientific-verifier"}
        with patch("sci_ai_verifier.local_entry._verify", return_value=json.loads(json.dumps(finished))):
            declined = verify("C:/skills/fixture-skill", html_report=False, **settings)
        self.assertNotIn("html_report", declined["data"])
        self.assertFalse((self.workspace / ".verifier" / "reports" / f"{RUN}.html").exists())
        with patch("sci_ai_verifier.local_entry._verify", return_value=json.loads(json.dumps(finished))):
            result = verify("C:/skills/fixture-skill", **settings)
        self.assertTrue(Path(result["data"]["html_report"]["path"]).is_file())
        # A page that cannot be drawn is reported beside the result, which stands.
        (self.run_dir / "report-card.json").unlink()
        with patch("sci_ai_verifier.local_entry._verify", return_value=json.loads(json.dumps(finished))):
            result = verify("C:/skills/fixture-skill", **settings)
        self.assertEqual(result["status"], "ok")
        self.assertIn("could not be written", result["data"]["html_report"]["error"])

    def test_the_public_tool_takes_an_optional_html_report_switch(self):
        schema = PublicRuntime.definitions[0]["inputSchema"]
        validate({"source_path": "C:/skills/fixture-skill"}, schema)
        validate({"source_path": "C:/skills/fixture-skill", "html_report": False}, schema)
        with self.assertRaises(Fault):
            validate({"source_path": "C:/skills/fixture-skill", "html_report": "no"}, schema)
        self.assertIn("html_report", PublicRuntime.instructions)


if __name__ == "__main__":
    unittest.main()
