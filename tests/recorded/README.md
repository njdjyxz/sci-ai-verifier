# Recorded independent-session replies

These are **not synthetic fixtures**. Each `.jsonl` file is the verbatim
Claude Code stream-json event sequence that a real session emitted, captured
by the workflow log of a local run while verifying the `glycoengineering`
example submission.

They exist because every other test in this suite writes the model's reply by
hand, in a shape that already satisfies the validator. That is how
`critic_response_invalid` reached a live run and discarded three completed
critiques: 215 tests passed while the real boundary failed on its first
contact with a real reply. A recorded reply cannot be written to match the
code, so it is the only test data here that can actually falsify the parser.

| File | Role | Run | What it captures |
| --- | --- | --- | --- |
| `critic-fenced-revision-list.jsonl` | critic | `a392ea65` | Reply wrapped in a ` ```json ` fence; `required_revisions` a 5-item list; supported grade B |
| `critic-fenced-revision-list-2.jsonl` | critic | `a392ea65` | Same fence, 4-item `required_revisions`; supported grade B |
| `critic-bare-empty-revisions.jsonl` | critic | `a392ea65` | Bare JSON, no fence; `required_revisions` an empty list; supported grade A |
| `assessor-bare.jsonl` | assessor | `a392ea65` | Bare JSON documentary assessment; `inconclusive` with six packet citations |
| `critic-extra-finding.jsonl` | critic | `e035eef6` | All five rubric criteria answered, then a sixth observation that fitted none of them; supported grade A |
| `subject-safety-refusal.jsonl` | subject | `e035eef6` | Provider safety refusal, category `bio`, with a fallback model that also refused |
| `critic-case-verdict-extra-key.jsonl` | critic | `0a243b7e` | Complete rubric v5 reply supporting B; two case verdicts carry an extra, empty `verdict_note` |
| `critic-case-verdict-extra-key-2.jsonl` | critic | `0a243b7e` | The retry against the same packet; one case verdict carries an extra, empty `case_id_note` |

`assessor-packet.json` is the real evidence packet the recorded assessor was
given, so its citations can be checked against the bytes it actually saw. `critic-case-verdict-packet.json` is the real
critique packet both `0a243b7e` replies answered: its case IDs are what their verdicts
must match, and its rubric is the live v5 one.

Each recording is here because the code got it wrong. The three `a392ea65`
critiques were rejected over a code fence and a list-shaped
`required_revisions`. The `e035eef6` critique was rejected for answering every
question and adding one more, which cost a grade A and 27 planned trials. The two
`0a243b7e` critiques were rejected for one empty extra key inside a case verdict, and
claim 1 of that run was lost with them. The
refusal was reported as an indistinguishable "incomplete observation", hiding
that the provider, not the skill, was the thing that failed.

## Rules for this directory

- Never hand-edit a recorded file to make a test pass. If the code must
  change to accept it, change the code; if the reply is genuinely
  non-conforming, the test asserting its rejection is the point.
- A critic recording is judged against the rubric it was **answering**, not the
  current one. Every critic recording here answered rubric v2. v3 appended a sixth
  criterion, on whether each case stays inside what its claim asserts, so these
  replies are complete answers to v2 and incomplete answers to v3 — and the tests
  assert both. The v2 rubric is rebuilt from the live one and pinned by its digest,
  which only holds while criteria are appended rather than inserted or reordered.
  The scope criterion was not invented here: `critic-extra-finding.jsonl`'s
  unprompted sixth finding, that its cases "test facts the claim does not print",
  is that criterion, raised by a real reviewer before it existed.
- Add new recordings from real runs only, with the run ID noted above.
- Recordings are scanned for credential-like bytes by
  `test_recorded_replies.py` before any other assertion runs.
