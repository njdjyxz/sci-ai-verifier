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
from sci_ai_verifier.safety import scan  # noqa: E402

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
                       "uncounted_cases": [verdicts[1]], "limitations": ["recorded limit"],
                       "unsourced_rules": [{"rule": "Keep preps scoring 7.2 or higher.", "reason": "No source states it.",
                                            "quoted": True, "grade": "U"},
                                           {"rule": "Re-purify anything below 7.2.", "reason": "No search sought it.",
                                            "quoted": True, "searched": False, "grade": None}]},
            "audit": {"critique": {"case_verdicts": verdicts, "coverage_gaps": ["one fact untested"],
                                   "claim_probe": {"cases": [{"case_id": "c_choice", "outcome": "reached",
                                                              "samples": [{"answer": "2"}, {"answer": "2"}]}]}}},
            "references": {REFERENCE: {"url": "javascript:alert(1)", "version": "a hostile source"}},
            "tests": [trial("c_choice", 1, "2", "pass"),
                      {**trial("c_choice", 2, "2", "pass"), "disagreement": "Step 2 picks alpha. " + HOSTILE},
                      {**trial("c_choice", 3, HOSTILE, "fail"), "disagreement": "Step 2 picks alpha. " + HOSTILE},
                      trial("c_term", 1, "beta", "pass", counted=False)]}
        documentary = {
            "claim": {"claim_id": "claim-2", "statement": "Second claim"}, "sections": ["Later"], "tests": [],
            "record": {"evidence_grade": "D", "scientific_status": "inconclusive"}, "audit": None,
            "documentary_assessment": {"assessment": {"status": "inconclusive", "findings": ["a finding"],
                                                      "citations": [{"quote": "cited words"}],
                                                      "statements": [{"statement": "The method is cleared.",
                                                                      "verdict": "not_addressed"}]}}}
        safety = scan([("SKILL.md", "The script makes no network calls.\n<!-- agents: " + HOSTILE + " -->\n"),
                       ("tool.py", "import urllib.request\nurllib.request.urlopen('https://x.example.invalid/a')\n")])
        report = {"run_id": RUN, "claims": [tested, documentary], "workflow_log": {}, "safety": safety,
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
        self.assertIn("No — it gives away the answer or the rule", page)
        self.assertIn("2 of 3", page)
        self.assertIn("A→B", page, "the planner's grade and the reviewer's, per round")
        self.assertIn("No tests ran", page)
        self.assertIn("1 of 3 sections of the skill had no claim: Untouched.", page)

    def test_a_rule_no_source_states_shows_as_u_beside_the_grade(self):
        """"Rules no source states" in evidence-rubric.md: a grade never stands for a rule nothing tested."""
        page = self.render()
        # U says the run looked and found none, never that none exists; a rule nothing sought has no grade.
        self.assertIn("Rules no source was found for:</span> this run looked for a source and found none", page)
        self.assertIn("That does not show that none exists.", page)
        self.assertIn("Keep preps scoring 7.2 or higher.", page)
        self.assertIn("Rules not looked up:</span> no search in this run sought a source", page)
        self.assertIn("Re-purify anything below 7.2.", page)
        self.assertIn('>U</span><span class="dim"> ×1</span>', page)  # the badge counts U rules only
        # The notes the agent fills say so beside the grade, and the documentary claim shows its statements.
        notes = report_html.skeleton(report_html.Run(self.workspace, RUN[:8]))
        self.assertIn("U: 1 rule no source was found for · 1 rule not looked up", notes["claims"]["1"]["result"])
        self.assertIn("The claim, statement by statement", page)
        self.assertIn("not_addressed: The method is cleared.", page)

    def test_a_near_miss_is_flagged_beside_a_fail_that_stands(self):
        """"Near misses" in local-tasks.md: run 0d15e36c's 0.53 where 0.54 to 0.66 passed."""
        output = {"field": "fold", "type": "number", "expected": "0.6", "absolute_tolerance": "0.06"}
        rows = [{"case_id": "t1", "trial": n, "observed": "done", "comparison_status": status, "counted": True,
                 "input": "Measure the blot.", "expected": {"fold": "0.6"},
                 "outputs": [{**output, "present": True, "found": found, "status": status, **extra}]}
                for n, found, status, extra in ((1, 0.531, "fail", {"near_miss": True}), (2, 0.58, "pass", {}))]
        task = report_html.task_view(1, "t1", rows, {"outputs": [output]}, {}, None, {}, {})
        self.assertTrue(task["near_miss"])
        self.assertIn("Near miss: within one and a half times the tolerance.", report_html.test_details(task))
        view = {**report_html.views(report_html.Run(self.workspace, RUN[:8]), {})[0], "tests": [task], "tasks": True}
        self.assertIn("Failed on a near miss:</span> t1. An answer missed its range", report_html.chapter(view, "Claude"))

    def test_safety_findings_show_once_for_the_skill_with_broken_promises_first(self):
        """"Safety findings" in local-contract.md: facts about the skill as software, beside the grades."""
        page = self.render()
        self.assertIn('<a href="#safety">Safety</a>', page)
        section = page[page.index('<section id="safety">'):page.index('<section id="claim-1"')]
        self.assertLess(section.index("The skill says one thing and its code does another"),
                        section.index("<table>"))
        self.assertIn("Promises no network use, at SKILL.md:1", section)
        self.assertIn("tool.py:2 urllib.request.urlopen to x.example.invalid", section)
        self.assertIn("Hidden comment addressed to AI agents", section)
        self.assertIn("The skill makes 1 promise its own code breaks; see Safety findings.", page)
        # A report from before the scan has no section and no link to one.
        report = json.loads((self.run_dir / "report-card.json").read_text(encoding="utf-8"))
        del report["safety"]
        (self.run_dir / "report-card.json").write_text(json.dumps(report), encoding="utf-8")
        page = self.render()
        self.assertNotIn('id="safety"', page)
        self.assertNotIn("#safety", page)

    def test_what_the_test_ai_said_is_wrong_with_the_skill_shows_under_its_claim(self):
        """"Disagreements" in local-tasks.md: beside the verdicts, which it never moves."""
        page = self.render()
        self.assertIn("The test AI disagreed with the skill</span> in 2 of 4 tries", page)
        # Run 7cfc4df5's 27 tries repeated one warning: the same words are shown once, naming every try.
        self.assertIn("c_choice, try 2; c_choice, try 3</b><span class=\"dim\"> · the same words in 2 tries</span>", page)
        self.assertEqual(page.count("Step 2 picks alpha. &lt;script&gt;"), 1)
        self.assertNotIn(HOSTILE, page)

    def test_a_passing_counted_test_most_tries_disputed_is_flagged_and_its_pass_stands(self):
        """Run 86d4e632: every try followed the skill's Lipinski rule, passed its key, and said the rule is wrong.
        The flag is display only; nothing else reads it."""
        output = {"field": "passes", "type": "boolean", "expected": False}
        def row(n, said):
            return {"case_id": "lip", "trial": n, "observed": "done", "comparison_status": "pass", "counted": True,
                    "input": "Apply the rule.", "expected": {"passes": False}, "disagreement": said,
                    "outputs": [{**output, "present": True, "found": False, "status": "pass"}]}
        rows = [row(1, "Lipinski tolerates one violation."), row(2, "The rule allows one failure."), row(3, None)]
        task = report_html.task_view(1, "lip", rows, {"outputs": [output]}, {}, None, {}, {})
        self.assertTrue(task["disputed"])
        self.assertEqual(task["passed"], 3)
        view = {**report_html.views(report_html.Run(self.workspace, RUN[:8]), {})[0], "tests": [task], "tasks": True,
                "disagreements": rows[:2], "trials_run": 3}
        chapter = report_html.chapter(view, "Claude")
        self.assertIn("Testers disputed:</span> lip. These tests passed, counted", chapter)
        self.assertIn("Testers disputed this test", report_html.task_table(view))
        # One disagreeing try, a failing try, or an uncounted test is not a dispute.
        for changed in (rows[:1] + [row(2, None), row(3, None)],
                        [rows[0], rows[1], {**row(3, None), "comparison_status": "fail"}],
                        [{**item, "counted": False} for item in rows]):
            self.assertFalse(report_html.task_view(1, "lip", changed, {"outputs": [output]}, {}, None, {}, {})["disputed"])

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
