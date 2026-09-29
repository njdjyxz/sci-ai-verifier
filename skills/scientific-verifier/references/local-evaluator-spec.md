# Local evaluator specification

`qualify_local_evaluator` takes `specification_json`, a JSON string with exactly
these fields. This document is supplied to the planner in the pinned context.

| Field | Meaning |
| --- | --- |
| `name`, `scope`, `limitations` | Bounded nonempty descriptions |
| `method` | `python` |
| `code` | Complete Python program, at most 32,000 characters |
| `absolute_tolerance`, `relative_tolerance` | Nonnegative bounded decimal strings |
| `cases` | 3–100 distinct source-backed cases |
| `controls` | 5–100 scoring controls, covering every class below |

Each case has exactly `case_id`, `input`, `expected`, `reference_ref`,
`source_quote` and `applicability`, all nonempty strings. IDs and inputs are unique.
The quote must occur in the fetched/imported reference text, and the expected
value must occur in that quote. This checks provenance, not scientific meaning.
For an imported binary benchmark, first provide a pinned text/JSON/CSV manifest
that maps the independently produced expected values to their inputs, units and
binary assets. Never invent an oracle from subject outputs.

Each control has exactly `case_id`, `actual`, `expected_status` and `group`.
`expected_status` is `pass`, `fail` or `invalid`. All three statuses must appear.
Groups `positive`, `negative`, `boundary`, `invalid` and `held_out` must all appear.
`actual` is a string of at most 16,000 characters. Positive checks establish
acceptance, negative checks establish rejection, and boundary/invalid checks
exercise tolerance equality and malformed output. A held-out designation is a
mechanical category; scientific independence still needs review.

The scoring program receives one JSON object on standard input:

```json
{
  "input": "the frozen case input",
  "actual": "the subject's observed answer",
  "expected": "the independently sourced expected answer",
  "absolute_tolerance": "0.000001",
  "relative_tolerance": "0",
  "artifacts": [],
  "artifact_root": "/work/observed"
}
```

When generated artifacts exist, their manifest entries contain `path`, `sha256`
and `bytes`; the files are copied under `artifact_root` in the evaluator's own
container. The evaluator does not receive the submitted skill or planning
conversation. Return exactly one plain JSON object to stdout:

```json
{"status":"pass"}
```

The other valid values are `fail` and `invalid`. A crash, timeout, malformed JSON
or unknown status is an operational evaluator failure. Do not use `invalid` for
missing infrastructure. The Python program runs in a new pinned container for
each control and score. No package installation, network or host access is
available. Put scientific dependencies in the operator-prepared image.

Mechanical controls authorize provisional use only. Grade A/B/C requires the
separate exact-candidate and exact-scope scientific review described in the local
contract. Rejected code may be revised and qualified as a new immutable candidate;
observations from a different selected plan cannot be silently reused.
