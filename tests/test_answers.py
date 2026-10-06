"""An expected value and its quote: the reading every quoted task value rests on.

A task design's quoted values must appear in their quotes, and its numbers compare as exact
decimals (`local-tasks.md`). Until 2026-10-05 this file also tested how a free-text reply was read
by answer type, replaying 945 live trials; that reader was retired with question tests, and its
tests and recordings are in Git history.
"""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.answers import forced_surface_form, in_quote, item_type, key_items, number, parsed, whole_token_in


class NumberTests(unittest.TestCase):
    def test_a_number_is_a_bounded_plain_decimal(self):
        self.assertEqual(number(" 7.60 "), Decimal("7.60"))
        self.assertEqual(number("-0.5"), Decimal("-0.5"))
        self.assertEqual(number("1e-3"), Decimal("0.001"))
        for text in ("7.6 nM", "1,000", "NaN", "Infinity", "1e999", "", None, "0x10", "1" * 33):
            with self.subTest(text=text):
                self.assertIsNone(parsed(text))


class QuoteTests(unittest.TestCase):
    def test_a_quoted_number_is_found_only_as_a_whole_token(self):
        quote = "alpha is 1.0, beta is 2.0."
        self.assertTrue(whole_token_in("1.0", quote))
        self.assertTrue(whole_token_in("2.0", quote))  # A full stop after it ends the token.
        self.assertTrue(whole_token_in("7.5", "7.5"))
        for value, text in (("1.0", "the value 21.09 was reported"), ("1.0", "1.05 at most"),
                            ("5", "pH 5.5"), ("5", "-5 degrees"), ("", "anything")):
            with self.subTest(value=value, text=text):
                self.assertFalse(whole_token_in(value, text))

    def test_a_term_is_found_in_its_quote_as_its_words(self):
        self.assertTrue(in_quote("term", "molar", "Units: Molar concentration."))
        self.assertTrue(in_quote("term", "any-atom queries", "turns dummies into any-atom query atoms"))
        self.assertTrue(in_quote("term", "The Kaplan-Meier estimators", "uses the Kaplan–Meier estimator"))
        self.assertFalse(in_quote("term", "molar", "molarity"))

    def test_a_set_is_found_item_by_item_each_by_its_own_form(self):
        self.assertEqual(key_items("R1, R2; Core"), ["R1", "R2", "Core"])
        self.assertEqual([item_type(item) for item in ("7.5", "R1", "rgroup_label", "molar")],
                         ["numeric", "exact", "exact", "term"])
        self.assertTrue(in_quote("set", "R1, R2", "keys R1 and R2", tokens=True))
        self.assertFalse(in_quote("set", "R1, R3", "keys R1 and R2", tokens=True))
        self.assertFalse(in_quote("exact", "R1", "R12", tokens=True))
        self.assertTrue(in_quote("exact", "R1", "R12"))  # Without tokens, verbatim anywhere.

    def test_only_a_token_with_one_way_to_write_it_has_a_forced_form(self):
        for text in ("R1", "rgroup_label", "pKa", "Molar", "7.5"):
            self.assertTrue(forced_surface_form(text), text)
        for text in ("molar", "two words", ""):
            self.assertFalse(forced_surface_form(text), text)


if __name__ == "__main__":
    unittest.main()
