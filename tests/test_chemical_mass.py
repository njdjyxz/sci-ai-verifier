"""Independent expected examples for candidate primitives, not live subject results."""

import importlib.util
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("chemical_mass_candidate", ROOT / "evaluators/chemical_mass/core.py")
mass = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mass)


class ChemicalMassCandidateTests(unittest.TestCase):
    def test_reference_examples(self):
        cases = {"H2O": "18.01056468403", "CO2": "43.98982923914", "NH3": "17.02654910112",
                 "CH4": "16.03130012892", "C6H12O6": "180.06338810418",
                 "H3PO4": "97.97689557339", "C2H6OS": "78.01393598735"}
        for formula, expected in cases.items():
            with self.subTest(formula=formula):
                self.assertEqual(mass.monoisotopic_mass(formula), Decimal(expected))
        self.assertEqual(mass.composition("C6H12O6"), {"C": 6, "H": 12, "O": 6})

    def test_explicit_grammar_boundaries(self):
        for formula in ("", "H0", "H01", "H1001", "H2O ", " H2O", "H2O+", "NaCl", "[13C]H4",
                        "(CH3)2O", "CuSO4.5H2O", "2H2O", "H2OH2", "carbon", "C1.5", None):
            with self.subTest(formula=formula), self.assertRaises(ValueError):
                mass.composition(formula)
        self.assertEqual(mass.composition("C1H1000"), {"C": 1, "H": 1000})

    def test_boundary_inclusive_tolerance_and_average_cannot_hide_failures(self):
        scored = mass.score_trials("H2O", ["18.01056568403", "18.0105656840301"])
        self.assertTrue(scored["observations"][0]["matches_reference"])
        self.assertFalse(scored["observations"][1]["matches_reference"])
        # Mean equals the reference, but both independently scored trials are wrong.
        scored = mass.score_trials("H2O", ["17.01056468403", "19.01056468403"])
        self.assertFalse(scored["all_trials_match"])
        self.assertFalse(any(item["matches_reference"] for item in scored["observations"]))
        self.assertNotIn("evidence_grade", scored)

    def test_invalid_observations_never_count_as_correct(self):
        for values in ([], ["NaN"], ["Infinity"], ["-1"], ["1e100000"], [True], [18.01056468403],
                       ["18"] * 11, ["invalid"], ["9" * 65]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                mass.score_trials("H2O", values)


if __name__ == "__main__":
    unittest.main()
