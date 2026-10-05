"""The HTML run report: drawn only from a run's records, every recorded string escaped, and text
written after the run marked as such."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("report_html", ROOT / "scripts" / "report_html.py")
report_html = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report_html)

RUN = "11111111-2222-3333-4444-555555555555"
CANDIDATE, REFERENCE = "c" * 64, "r" * 64
HOSTILE = "<script>alert(1)</script>"


def trial(case_id, number, observed, status, counted=True):
    return {"case_id": case_id, "trial": number, "observed": observed, "comparison_status": status,
            "python_status": status, "read_by": "python", "counted": counted, "input": "Pick one.\n1. alpha\n2. beta",
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
            "claim": {"claim_id": "claim-1", "statement": "First claim <b>bold</b>"}, "sections": ["Intro"],
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
        self.assertNotIn("First claim &lt;b&gt;", page, "a plain description replaces the raw statement")

    def test_the_same_records_give_the_same_page(self):
        self.assertEqual(self.render(), self.render())

    def test_a_run_without_a_report_card_says_so(self):
        (self.run_dir / "report-card.json").unlink()
        (self.run_dir / "partial-report.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(SystemExit) as stopped:
            report_html.Run(self.workspace, RUN)
        self.assertIn("stopped early", str(stopped.exception))


if __name__ == "__main__":
    unittest.main()
