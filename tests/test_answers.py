"""How a subject's reply is read, one answer type at a time, and what the AI reader may change.

"Reading a reply" under `qualify_local_candidate` in tool-contracts.md owns the reading rules and
"Reading replies" in local-contract.md owns the AI reader. The replay test below runs every scored
reply of seventeen live runs through today's reader: that is the acceptance test the reader was
built against, and it uses real replies, which a hand-written test cannot imitate.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.answers import (answer_block, compare, in_quote, instruction, key_problem, probe_passed,
                                     probes, readings, settles_otherwise)
from sci_ai_verifier.common import Fault

RECORDED = Path(__file__).resolve().parent / "recorded"
OPTIONS = ["alpha one", "beta two", "gamma three", "delta four", "none of these"]


class ReplayTests(unittest.TestCase):
    """Every saved reply of runs 76ce4af1 through 0aeca4c6, read as its case's type would read it now."""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((RECORDED / "subject-replies.json").read_text(encoding="utf-8"))

    def verdict(self, item):
        case = self.data["cases"][item["case"]]
        return compare(case["method"], item["reply"], case["expected"], case.get("options"), case.get("unit"))

    def test_every_right_answer_passes_and_no_wrong_one_does(self):
        replies = self.data["replies"]
        self.assertEqual(sum(item["trials"] for item in replies), 945)
        for item in replies:
            with self.subTest(case=item["case"], reply=item["reply"][:60]):
                if item["answer"] == "right":
                    self.assertEqual(self.verdict(item), "pass")
                else:
                    self.assertNotEqual(self.verdict(item), "pass")

    def test_each_reply_form_that_misread_a_right_answer_now_passes(self):
        """A plural (e13f50ee), `Molar` (fb64115f), `**1**` (7efbdd8c), an explanation below the
        answer (0a243b7e) and a code fence (0aeca4c6): 19 trials the reader of the day got wrong."""
        misread = [item for item in self.data["replies"] if item["answer"] == "right" and item["recorded_status"] != "pass"]
        self.assertEqual(sum(item["trials"] for item in misread), 19)
        self.assertEqual({item["case"].split("/")[0] for item in misread},
                         {"e13f50ee", "fb64115f", "7efbdd8c", "0a243b7e", "0aeca4c6", "1bb3f07a"})
        self.assertTrue(all(self.verdict(item) == "pass" for item in misread))

    def test_the_wrong_answers_still_fail_and_the_paraphrases_are_left_to_the_ai_reader(self):
        wrong = [item for item in self.data["replies"] if item["answer"] == "wrong"]
        self.assertEqual(sum(item["trials"] for item in wrong), 10)
        self.assertTrue(all(self.verdict(item) == "fail" for item in wrong))
        paraphrases = [item for item in self.data["replies"] if item["answer"] == "paraphrase"]
        self.assertEqual({item["reply"] for item in paraphrases},
                         {"Explicitly finishes drawing, allowing us to return the drawing text",
                          "convert dummies in the input structure into query atoms", "MolOps::adjustQueryProperties"})
        self.assertTrue(all(self.verdict(item) == "fail" for item in paraphrases))


class AnswerLineTests(unittest.TestCase):
    def test_the_answer_line_is_found_past_fences_and_labels_and_above_explanations(self):
        for reply in ("R1", "\n\n  R1  \n", "R1\n\nThe fragment is R1.", "```\nR1\n```", "```python\nR1\n```\n\nWhy.",
                      "~~~\nR1\n~~~", "```text\n\nR1\n", "Answer: R1", "**Answer:** R1", "**Final answer**: R1",
                      "## Answer\n\nR1", "Answer:\n```\nR1\n```", "**Answer: R1**", "*Answer: R1*"):
            with self.subTest(reply=reply):
                self.assertEqual(answer_block(reply)[0], "R1")
        self.assertEqual(answer_block(""), [])
        self.assertEqual(answer_block("```\n```\n\nR1"), [])
        # A label's emphasis must be followed by a space, so an answer's own underscores survive.
        self.assertEqual(answer_block("Answer: __init__")[0], "__init__")

    def test_readings_take_one_layer_off_both_ends_and_never_search_inside(self):
        self.assertEqual(readings("**`R1`**"), ["**`R1`**", "`R1`", "R1"])
        self.assertEqual(readings("__init__"), ["__init__", "init"])
        self.assertEqual(readings('"molar".'), ['"molar".', '"molar"', "molar"])
        # Two spans are not one wrapper, and nothing inside the line is pulled out.
        self.assertEqual(readings("`a` and `b`"), ["`a` and `b`"])
        self.assertEqual(readings("The answer is 1"), ["The answer is 1"])


class TypeTests(unittest.TestCase):
    def test_numeric_reads_a_number_and_the_case_s_unit(self):
        self.assertEqual(compare("numeric", "7.6", "7.60"), "pass")
        self.assertEqual(compare("numeric", "−0.5", "-0.5"), "pass")
        self.assertEqual(compare("numeric", "7.6 nM", "7.6", unit="nM"), "pass")
        self.assertEqual(compare("numeric", "**7.6** nM", "7.6", unit="nM"), "pass")
        self.assertEqual(compare("numeric", "7.6nM", "7.6", unit="nM"), "pass")
        self.assertEqual(compare("numeric", "7.6 nM", "7.6"), "invalid")
        self.assertEqual(compare("numeric", "7.6 uM", "7.6", unit="nM"), "invalid")
        self.assertEqual(compare("numeric", "7.61", "7.60"), "fail")

    def test_choice_reads_the_option_however_it_is_named(self):
        for reply in ("2", "**2**", "2.", "2)", "(2)", "[2]", "Option 2", "option 2: beta two", "beta two",
                      "Beta Two.", "2. beta two", "```\n2\n```"):
            with self.subTest(reply=reply):
                self.assertEqual(compare("choice", reply, "2", OPTIONS), "pass")
        self.assertEqual(compare("choice", "3", "2", OPTIONS), "fail")
        self.assertEqual(compare("choice", "none of these", "2", OPTIONS), "fail")
        # A number followed by another option's text contradicts itself.
        self.assertEqual(compare("choice", "2. gamma three", "2", OPTIONS), "invalid")
        self.assertEqual(compare("choice", "B", "2", OPTIONS), "invalid")

    def test_an_option_whose_text_is_a_number_is_read_by_position_first(self):
        options = ["1.0", "0.8", "0.5", "0.0", "3600", "none of these"]
        self.assertEqual(compare("choice", "1.0", "1", options), "pass")  # position 1, and its text
        self.assertEqual(compare("choice", "0.8", "2", options), "pass")  # not a position: its text
        self.assertEqual(compare("choice", "3600", "5", options), "pass")  # past the list: its text

    def test_term_ignores_case_hyphens_articles_and_plurals_but_not_words(self):
        for reply, key in (("Molar", "molar"), ("MOLAR", "molar"), ("molars", "molar"), ("the molar", "molar"),
                           ("any-atom query", "any-atom queries"), ("Any atom queries.", "any-atom queries"),
                           ("returns the SVG", "return the SVG"), ("Kaplan–Meier estimators", "Kaplan-Meier estimator")):
            with self.subTest(reply=reply):
                self.assertEqual(compare("term", reply, key), "pass")
        for reply, key in (("ACS 1996 mode", "ACS 1996 guidelines"), ("molal", "molar"), ("not molar", "molar"),
                           ("molar concentration", "molar")):
            with self.subTest(reply=reply):
                self.assertEqual(compare("term", reply, key), "fail")

    def test_expression_compares_syntax_trees_and_never_runs_them(self):
        self.assertEqual(compare("expression", "np.log10( x )", "np.log10(x)"), "pass")
        self.assertEqual(compare("expression", "```python\n-np.log10((ic50))\n```", "-np.log10(ic50)"), "pass")
        self.assertEqual(compare("expression", "y=x+1", "y = x + 1"), "pass")
        self.assertEqual(compare("expression", "'a'", '"a"'), "pass")
        self.assertEqual(compare("expression", "numpy.log10(x)", "np.log10(x)"), "fail")
        self.assertEqual(compare("expression", "log base ten of x", "np.log10(x)"), "invalid")
        with patch("builtins.eval", side_effect=AssertionError("never evaluated")), \
             patch("builtins.exec", side_effect=AssertionError("never executed")):
            self.assertEqual(compare("expression", "__import__('os').system('x')", "x"), "fail")

    def test_lists_keep_their_order_and_sets_do_not(self):
        for reply in ("time, event, cause", "time; event; cause", "- time\n- event\n- cause", "1. time\n2. event\n3. cause",
                      "time, event and cause", "`time`, `event`, `cause`", "**time, event, cause**"):
            with self.subTest(reply=reply):
                self.assertEqual(compare("list", reply, "time, event, cause"), "pass")
        self.assertEqual(compare("list", "cause, event, time", "time, event, cause"), "fail")
        self.assertEqual(compare("set", "cause, event, time", "time, event, cause"), "pass")
        self.assertEqual(compare("set", "R1 and R2", "R1, R2"), "pass")
        self.assertEqual(compare("set", "R1", "R1, R2"), "fail")
        self.assertEqual(compare("set", "R1, R2, R3", "R1, R2"), "fail")
        self.assertEqual(compare("set", "8.00, 7.5", "7.5, 8.0"), "pass")
        self.assertEqual(compare("set", "", "R1, R2"), "invalid")


class QualificationRuleTests(unittest.TestCase):
    def test_each_type_s_controls_pass_on_its_own_keys(self):
        """The controls are what prove the reader for a case; a key its own controls fail is refused."""
        keys = [("numeric", {"expected": "7.60"}), ("numeric", {"expected": "7.6", "unit": "nM"}),
                ("numeric", {"expected": "-0.5"}), ("exact", {"expected": "R1"}), ("exact", {"expected": "rgroup_label"}),
                ("exact", {"expected": "__init__"}), ("exact", {"expected": "[*:1]"}),
                ("exact", {"expected": "cum_incidence[1:]"}), ("term", {"expected": "molar"}),
                ("term", {"expected": "any-atom queries"}), ("term", {"expected": "ACS 1996 guidelines"}),
                ("term", {"expected": "Kaplan-Meier estimator"}), ("term", {"expected": "the gas"}),
                ("expression", {"expected": "cum_incidence[1:]"}), ("expression", {"expected": "-np.log10(ic50)"}),
                ("expression", {"expected": "y = x + 1"}), ("list", {"expected": "time, event, cause"}),
                ("set", {"expected": "R1, R2, Core"}), ("set", {"expected": "7.5, 8.0"}),
                ("choice", {"expected": "2", "options": OPTIONS}),
                ("choice", {"expected": "5", "options": ["1.0", "0.8", "0.5", "0.0", "3600", "none of these"]})]
        for method, case in keys:
            self.assertIsNone(key_problem(method, case), (method, case))
            for reply, wanted in probes(method, case):
                with self.subTest(method=method, key=case["expected"], reply=reply):
                    self.assertTrue(probe_passed(compare(method, reply, case["expected"], case.get("options"),
                                                         case.get("unit")), wanted), wanted)

    def test_a_key_is_refused_where_its_type_would_misjudge_it(self):
        refused = [("exact", {"expected": "molar"}, "is a `term`"),
                   ("term", {"expected": "nM"}, "capital after its first letter"),
                   ("term", {"expected": "pKa value"}, "capital after its first letter"),
                   ("term", {"expected": "M"}, "lone letter"),
                   ("term", {"expected": "7.5"}, "`numeric`"),
                   ("term", {"expected": "g/mol"}, "letters, digits, hyphens"),
                   ("term", {"expected": "one two three four five six seven eight nine"}, "at most 8 words"),
                   ("expression", {"expected": "log base ten"}, "parses"),
                   ("numeric", {"expected": "7.6", "unit": "7 nM"}, "unit"),
                   ("list", {"expected": "R1"}, "2 to 20"),
                   ("set", {"expected": "molar, molars"}, "distinct"),
                   ("set", {"expected": "7.5, 7.50"}, "distinct")]
        for method, case, message in refused:
            with self.subTest(method=method, key=case["expected"]):
                self.assertIn(message, key_problem(method, case) or "")

    def test_a_term_is_found_in_its_quote_as_its_words(self):
        self.assertTrue(in_quote("term", "molar", "Units: Molar concentration."))
        self.assertTrue(in_quote("term", "any-atom queries", "turns dummies into any-atom query atoms"))
        self.assertFalse(in_quote("term", "molar", "molarity"))
        self.assertTrue(in_quote("set", "R1, R2", "keys R1 and R2", tokens=True))
        self.assertFalse(in_quote("exact", "R1", "R12", tokens=True))

    def test_the_subject_is_told_each_answer_form(self):
        self.assertEqual(instruction("choice"), "Write only the answer on the first line of your reply: "
                                                "the number of the correct option.")
        self.assertEqual(instruction("numeric", "nM"), "Write only the answer on the first line of your reply: "
                                                       "the number in nM.")
        self.assertIn("not in a code block", instruction("expression"))
        self.assertIn("in any order", instruction("set"))

    def test_only_numbers_and_options_settle_that_a_reply_gave_another_answer(self):
        self.assertTrue(settles_otherwise("numeric", "7.5", "7.60"))
        self.assertFalse(settles_otherwise("numeric", "about seven and a half", "7.60"))
        self.assertTrue(settles_otherwise("choice", "3", "2", OPTIONS))
        self.assertTrue(settles_otherwise("choice", "gamma three", "2", OPTIONS))
        self.assertFalse(settles_otherwise("exact", "MolOps::adjustQueryProperties", "adjustQueryProperties"))
        self.assertFalse(settles_otherwise("term", "molal", "molar"))


class ReaderTests(unittest.TestCase):
    """read_reply with each Claude Code session replaced by a scripted reply."""

    CASE = {"case_id": "c", "input": "What is the pIC50 of 25 nM?", "expected": "7.60"}

    def read(self, value, reply="It is about 7.6.", models=("pinned-model",), method="numeric", case=None,
             python_status="invalid", error=None):
        from sci_ai_verifier.documentary import read_reply
        adapter = type("Pinned", (), {"model": "pinned-model"})()
        seen = []

        def answer(adapter, packet, *, role, system_prompt, schema, timeout, limit=64000):
            seen.append((role, packet))
            if error:
                raise error
            return ({"structured_output": value, "observed_model_ids": list(models), "usage": None,
                     "total_cost_usd": 0.01}, "reader-session")
        with patch("sci_ai_verifier.documentary.isolated_answer", side_effect=answer):
            record = read_reply(adapter, method, case or self.CASE, reply, python_status)
        return record, seen

    def test_an_accepted_reading_decides_the_trial(self):
        record, seen = self.read({"reading": "matches", "answer": "7.6", "reason": "It gives 7.6."})
        self.assertEqual((record["status"], record["final_status"], record["python_status"]), ("used", "pass", "invalid"))
        role, packet = seen[0]
        self.assertEqual(role, "reader")
        self.assertEqual(packet, {"question": "What is the pIC50 of 25 nM?",
                                  "answer_format": "Write only the answer on the first line of your reply: the number.",
                                  "answer_type": "numeric", "expected_answer": "7.60", "reply": "It is about 7.6."})
        record, _ = self.read({"reading": "no_single_answer", "answer": "", "reason": "It hedges."},
                              reply="Either 7.6 or 7.9.", python_status="invalid")
        self.assertEqual((record["status"], record["final_status"]), ("used", "invalid"))

    def test_python_refuses_a_reading_its_own_reader_or_the_reply_contradicts(self):
        cases = [({"reading": "matches", "answer": "7.9", "reason": "r"}, "It is 7.9.", ("pinned-model",),
                  "python_reads_another_answer"),
                 ({"reading": "matches", "answer": "7.60", "reason": "r"}, "It is about 7.6.", ("pinned-model",),
                  "answer_not_in_reply"),
                 ({"reading": "differs", "answer": "7.6", "reason": "r"}, "It is about 7.6.", ("pinned-model",),
                  "python_reads_the_expected_answer"),
                 ({"reading": "matches", "answer": "7.6", "reason": "r"}, "It is about 7.6.", ("other-model",),
                  "model_changed")]
        for value, reply, models, refusal in cases:
            with self.subTest(refusal=refusal):
                record, _ = self.read(value, reply=reply, models=models)
                self.assertEqual((record["status"], record["refusal"], record["final_status"]),
                                 ("refused", refusal, "invalid"))

    def test_a_failed_session_keeps_python_s_verdict_and_a_stop_ends_the_reading(self):
        record, _ = self.read(None, error=Fault("reader_unavailable", "slow"), python_status="fail")
        self.assertEqual((record["status"], record["error"], record["final_status"]), ("unavailable", "reader_unavailable", "fail"))
        record, _ = self.read({"reading": "sure", "answer": "7.6", "reason": "r"})
        self.assertEqual((record["status"], record["error"]), ("unavailable", "reader_response_invalid"))
        with self.assertRaises(Fault) as caught:
            self.read(None, error=Fault("verification_cancelled", "stop"))
        self.assertEqual(caught.exception.code, "verification_cancelled")

    def test_a_choice_is_shown_to_the_reader_with_its_option_text(self):
        case = {"case_id": "c", "input": "Which?", "expected": "2", "options": OPTIONS}
        record, seen = self.read({"reading": "matches", "answer": "the second one, beta", "reason": "r"},
                                 reply="I pick the second one, beta.", method="choice", case=case)
        self.assertEqual(seen[0][1]["expected_answer"], "option 2: beta two")
        self.assertEqual(record["final_status"], "pass")


if __name__ == "__main__":
    unittest.main()
