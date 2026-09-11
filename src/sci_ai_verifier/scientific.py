"""Installed numerical method. Catalog approval and audited bindings remain mandatory."""

import re
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from .common import Fault, canonical, digest
from .catalog import decode, bounded_read

METHOD = "chemical_mass_v1"
SCOPE = "neutral CHNOPS formulas; H-1 C-12 N-14 O-16 P-31 S-32"
POLICY = {"id": "chemical-mass-comparison", "version": "1", "supported_grades": ["C"],
          "tolerance_da": "0.000001", "aggregation": "all_trials_all_cases",
          "minimum_usable_case_fraction": "1", "invalid_observation": "no_supported_execution_grade",
          "grade_basis": "Independent deterministic tool comparison on the declared pilot cases",
          "stronger_grades": "not_supported_by_this_pilot_policy"}
FORMULAS = ["H2O", "CO2", "NH3", "CH4", "C6H12O6", "H3PO4", "C2H6OS"]
TOKEN = re.compile(r"([CHNOPS])([1-9][0-9]{0,3})?")


def composition(formula):
    if not isinstance(formula, str) or not 1 <= len(formula) <= 128:
        raise ValueError("Invalid formula length.")
    counts, offset = {}, 0
    while offset < len(formula):
        found = TOKEN.match(formula, offset)
        if found is None:
            raise ValueError("Formula is outside the pilot grammar.")
        symbol, count = found.groups()
        count = int(count or "1")
        if symbol in counts or count > 1000:
            raise ValueError("Repeated element or count outside 1-1000.")
        counts[symbol], offset = count, found.end()
    return counts


def mass(formula, reference):
    with localcontext() as context:
        context.prec = 50
        return sum((Decimal(reference["isotopes"][key]["mass_da"]) * count
                    for key, count in composition(formula).items()), Decimal(0))


def score(raw_text, expected):
    # The fixed output contract is a plain decimal in Da; prose/units/JSON is an invalid observation.
    raw = raw_text.strip() if isinstance(raw_text, str) else ""
    if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,32})?", raw):
        return {"status": "invalid", "reason": "Expected a plain nonnegative decimal mass in Da."}
    try:
        actual = Decimal(raw)
        with localcontext() as context:
            context.prec = 80
            error = abs(actual - Decimal(expected))
    except InvalidOperation:
        return {"status": "invalid", "reason": "Invalid numeric observation."}
    return {"status": "pass" if error <= Decimal(POLICY["tolerance_da"]) else "fail",
            "absolute_error_da": str(error)}


def pin_assets(store, state, asset_root):
    raw = bounded_read(Path(asset_root) / "chemical-reference.json")
    reference = decode(raw)
    if (not isinstance(reference, dict) or not isinstance(reference.get("version"), str)
            or not isinstance(reference.get("isotopes"), dict)
            or set(reference["isotopes"]) != set("CHNOPS")):
        raise Fault("resource_invalid", "The installed isotope reference is invalid.", fatal=True)
    for entry in reference["isotopes"].values():
        value = entry.get("mass_da") if isinstance(entry, dict) else None
        if (not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,3}(?:\.[0-9]{1,32})?", value)
                or Decimal(value) <= 0):
            raise Fault("resource_invalid", "Isotope masses must be finite positive decimal strings.", fatal=True)
    cases = canonical({"version": "chemical-pilot-cases-1", "formulas": FORMULAS,
                       "scope": SCOPE,
                       "coverage": "Seven illustrative formulas; not representative of every allowed count.",
                       "provenance": "Developer-selected pilot cases; independent scientific review required"})
    # Pin code bytes as well as data. A later host must verify these before execution.
    method_bytes = implementation_bytes()
    state["method_ref"] = store.put(method_bytes)
    state["resource_assets"] = {}
    for resource_id, version, payload in (("nist-chnops-isotopes", reference["version"], raw),
                                          ("chemical-pilot-cases", "chemical-pilot-cases-1", cases)):
        key = store.put(payload)
        state["objects"].append(key)
        state["resource_assets"][resource_id] = {"id": resource_id, "version": version, "sha256": key,
            "provenance": reference.get("description", "") if resource_id == "nist-chnops-isotopes" else
            "Developer-selected pilot cases", "license": "Source attribution retained; review required"}
    state["objects"].append(state["method_ref"])
    state["case_formulas"] = FORMULAS


def resource_requirements(state):
    return sorted(({key: entry[key] for key in ("id", "version", "sha256")}
                   for entry in state["resource_assets"].values()), key=lambda entry: entry["id"])


def method_current(state):
    return digest(implementation_bytes()) == state["method_ref"]


def implementation_bytes():
    # A changed host/scorer must not reuse an earlier audit's execution authority.
    return canonical({path.name: path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
                      for path in sorted(Path(__file__).parent.glob("*.py"))})
