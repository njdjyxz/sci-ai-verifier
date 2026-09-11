# First complete verification family: chemical formula and mass calculations

The user selected this family on 2026-09-10. The candidate below makes a bounded first implementation reviewable. It is not a reviewed evaluator registration or a completed verification of a submitted skill.

## Candidate contract

Start with flat, neutral formulas containing C, H, N, O, P and S. Use exactly H-1, C-12, N-14, O-16, P-31 and S-32, with counts 1-1000 and each element written once. Reject explicit isotopic labels, charge/adduct notation, parentheses, hydrates, whitespace, unsupported elements and duplicate symbols. These are pilot coverage exclusions, not assertions that those chemical notations are invalid in general. A formula does not establish whether a molecule is physically realizable.

The candidate numerical tolerance is an inclusive absolute error of 0.000001 Da. This is a proposed software acceptance threshold, not a NIST uncertainty statement or a scientifically reviewed grade policy. Every subject trial must be scored separately; an average cannot conceal opposing errors. Grade eligibility, trial counts, independent coverage, invalid-case handling and the approved subject runner still require a committed plan and audit.

`evaluators/chemical_mass/core.py` remains the original unregistered review helper. Version 0.4.0 installs the bounded method in [scientific.py](../src/sci_ai_verifier/scientific.py), with the pinned [reference data](../src/sci_ai_verifier/assets/chemical-reference.json). The complete runtime requires an approved catalog capability and runner, exact resource pins, a committed plan and a passing audit before observations. Fixtures exercise this with explicitly synthetic approvals. Production registry approval is still pending.

## Reference values and provenance

The local [reference data](../evaluators/chemical_mass/reference.json) retains the decimal values, quoted uncertainties, isotope IDs, retrieval date and per-element source links. Values were checked against NIST's tables on 2026-09-10:

| Isotope | Selected mass (Da) | Primary source |
|---|---|---|
| H-1 | 1.00782503223 | [NIST hydrogen](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=H) |
| C-12 | 12 exactly | [NIST carbon](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=C) |
| N-14 | 14.00307400443 | [NIST nitrogen](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=N) |
| O-16 | 15.99491461957 | [NIST oxygen](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=O) |
| P-31 | 30.97376199842 | [NIST phosphorus](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=P) |
| S-32 | 31.9720711744 | [NIST sulfur](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=S) |

The numbers are pinned inputs for reproducibility, not a claim that this is the newest atomic-mass evaluation. Standard atomic weights, average formula mass, and monoisotopic mass remain distinct claim types. The submitted skill must state enough scope to justify the selected evaluator; the verifier must not insert this convention into an underspecified claim.

## Prepared routing examples

The three proposed types and two provisional harness descriptions are under [examples/catalog](../examples/catalog). They cover composition, monoisotopic mass and average mass separately. A monoisotopic claim matching the explicit CHNOPS convention is a potential numerical candidate after review. Average-mass claims, charged species, molecular structure predictions, and claims with unspecified scope must not match this narrow numeric capability. Documentary fallback requires a separate independent assessor and never upgrades metadata into a scientific result.

The Stage 3 tests use a separate synthetic catalog with clearly identified test approvals to exercise successful selection, lower grades and missing runners. The real candidate entries remain `provisional`, and the shipped reviewed registries remain empty. Promotion must be a maintainer-reviewed change.

## Implemented end-to-end fixture path

The user chose configurable execution with fixtures for now. [The demo](../scripts/run_fixture_demo.py) exercises target planning, resource locking, bundle validation, run-local registration, a second plan revision, audit, fourteen observations over seven formulas, independent per-trial comparison, result commitment and both report formats. Correct, wrong and invalid variants are available. The replay adapter never invokes a live submitted skill and every report is labeled synthetic.

The seven cases are H2O, CO2, NH3, CH4, C6H12O6, H3PO4 and C2H6OS. They are developer-selected examples, not a representative benchmark over the entire grammar. The fixed policy allows C only, uses all trials/cases, never averages raw answers, and requires every observation to be scientifically usable. Invalid observations retain their raw evidence and end operationally because this delivery has no independent D assessor. Repeated fixture answers do not establish model reproducibility.

## Review decisions still required for production

Review the reference attribution/license basis, isotope convention, parser boundaries, case coverage, tolerance and C-only grade basis. Confirm the actual submitted skill states the needed scope; never add it during extraction. Choose a live subject adapter and independently verify identity, configuration, deadline enforcement and isolation before use. The installed in-process interface is configurable but is not a sandbox. Only after those checks should a maintainer promote catalog entries and publish exact release pins. Scientific review and live-app acceptance cannot be inferred from the synthetic reports.
