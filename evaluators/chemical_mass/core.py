"""Candidate numeric evaluator primitives. Not registered or authorized for execution."""

import json
import re
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

REFERENCE = Path(__file__).with_name("reference.json")
TOKEN = re.compile(r"([CHNOPS])([1-9][0-9]{0,3})?")


def composition(formula):
    """Parse the deliberately narrow, flat neutral-CHNOPS pilot grammar."""
    if not isinstance(formula, str) or not 1 <= len(formula) <= 128:
        raise ValueError("Formula must be 1-128 characters.")
    counts, offset = {}, 0
    while offset < len(formula):
        match = TOKEN.match(formula, offset)
        if match is None:
            raise ValueError("Outside pilot grammar: use flat, unlabeled CHNOPS formulas.")
        symbol, raw_count = match.groups()
        count = int(raw_count or "1")
        if symbol in counts or count > 1000:
            raise ValueError("Each element appears once, with a count from 1 to 1000.")
        counts[symbol] = count
        offset = match.end()
    return counts


def monoisotopic_mass(formula):
    """Sum specified NIST isotope masses as decimals; this does not run a subject."""
    counts = composition(formula)
    reference = json.loads(REFERENCE.read_bytes())
    with localcontext() as context:
        context.prec = 50
        return sum((Decimal(reference["isotopes"][symbol]["mass_da"]) * count
                    for symbol, count in counts.items()), Decimal(0))


def score_trials(formula, observed_masses):
    """Score every submitted trial separately against a fixed candidate tolerance."""
    if not isinstance(observed_masses, list) or not 1 <= len(observed_masses) <= 10:
        raise ValueError("Supply 1-10 separate trial observations.")
    expected = monoisotopic_mass(formula)
    tolerance = Decimal("0.000001")
    observations = []
    for raw in observed_masses:
        if not isinstance(raw, str) or not 1 <= len(raw) <= 64:
            raise ValueError("Observed mass must be a bounded decimal string in daltons.")
        try:
            actual = Decimal(raw)
        except InvalidOperation:
            raise ValueError("Invalid observed mass.") from None
        if not actual.is_finite() or not 0 <= actual <= Decimal("1000000000"):
            raise ValueError("Observed mass must be finite and within the pilot numeric bound.")
        with localcontext() as context:
            context.prec = 80
            error = abs(actual - expected)
        observations.append({"observed_mass_da": raw, "absolute_error_da": str(error),
                             "matches_reference": error <= tolerance})
    return {"formula": formula, "reference_mass_da": str(expected),
            "absolute_tolerance_da": str(tolerance), "observations": observations,
            "all_trials_match": all(o["matches_reference"] for o in observations),
            "scientific_verification": "not_established_by_this_candidate_helper"}
