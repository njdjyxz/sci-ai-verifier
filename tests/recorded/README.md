# Recorded independent-session replies

These are **not synthetic fixtures**. Each `.jsonl` file is the verbatim
Claude Code stream-json event sequence that a real session emitted, captured
either by the workflow log of a local run or by a live replay of a real run's
packet through the code that reads it. `subject-replies.json` holds the verbatim
reply text of real subject sessions, taken from the report cards that scored them.

They exist because every other test in this suite writes the model's reply by
hand, in a shape that already satisfies the validator. That is how
`critic_response_invalid` reached a live run and discarded three completed
critiques: 215 tests passed while the real boundary failed on its first
contact with a real reply. A recorded reply cannot be written to match the
code, so it is the only test data here that can actually falsify the parser.

| File | Role | Source | What it captures |
| --- | --- | --- | --- |
| `critic-structured.jsonl` | critic | live replay, 2026-09-29 | Run `d416f79d`'s pIC50 critique packet under rubric v9, with each case's answer type, answered through the reply schema: supported grade B, all three cases counted, as under v8. Its first reply was accepted. The v8 recording, whose first reply a stray `$PARAMETER_NAME` key broke, is in Git history |
| `assessor-structured.jsonl` | assessor | live replay, 2026-09-28 | Run `a392ea65`'s documentary packet answered through the reply schema: `inconclusive` with six exact packet citations, accepted first time |
| `claim-probe-structured.jsonl` | claim-only | live replay, 2026-09-28 | Run `d416f79d`'s `pic50-one-nanomolar` case with its claim: answer `9`. Its first reply added a stray `a` key; refused and resent |
| `subject-safety-refusal.jsonl` | subject | `e035eef6` | Provider safety refusal, category `bio`, with a fallback model that also refused |
| `planner-session-limit.jsonl` | planner | `7f88fbef` | The planner's last two events: the CLI's `rate_limit` message and a `result` with `terminal_reason` `api_error`, HTTP 429, "You've hit your session limit" |
| `subject-refusal-fallback.jsonl` | subject | `3dc02567` | Opus 5 refused an R-group question after the skill loaded; a `model_refusal_fallback` event, then `claude-opus-4-8` wrote the answer `R1` and the session succeeded |
| `subject-refusal-recovered.jsonl` | subject | `3dc02567` | The same case: `model_refusal_no_fallback`, a `<synthetic>` refusal notice, then `claude-opus-5` answered `R1` itself |
| `reader-matches.jsonl` | reader | live reading, 2026-09-29 | Run `1bb3f07a`'s reply `MolOps::adjustQueryProperties` to a question whose key is `adjustQueryProperties` and which asked for no namespace prefix: `matches`, called "a formatting difference" |
| `reader-differs.jsonl` | reader | live reading, 2026-09-29 | Run `1bb3f07a`'s paraphrase of a documented sentence the question asked for verbatim: `differs` |
| `subject-replies.json` | subject | 17 runs, `76ce4af1` to `0aeca4c6` | Every scored subject reply in those runs' report cards, 945 trials as 496 distinct replies, each with its case's key, options and the verdict it received, labelled right, wrong or paraphrase. `test_answers.py` replays them through today's reader: every right answer passes, including 19 trials misread when they ran, and no wrong one does |

`critic-structured-packet.json`, `assessor-packet.json`, `claim-probe-packet.json` and
`reader-packets.json` are the exact packets those sessions were given, so each reply can be
checked against the bytes it actually saw.

Each recording is here because the code got it wrong, or to prove the fix. Until
2026-09-28 the verifier's own sessions answered in free text, and Python learned
their shapes one lost reply at a time: three `a392ea65` critiques were rejected over
a code fence and a list-shaped `required_revisions`, an `e035eef6` critique for
answering every question and adding one more, which cost a grade A and 27 planned
trials, and two `0a243b7e` critiques for one empty extra key inside a case verdict,
which lost claim 1 of that run. Those recordings tested the free-text reader and were
removed with it; they remain in Git history. The structured recordings show a schema
catching the same kind of slip live and the session correcting it. The `e035eef6`
safety refusal was reported as an indistinguishable "incomplete observation", hiding
that the provider, not the skill, was the thing that failed. The `7f88fbef` planner
stopped on the subscription session limit, and the runner recorded that as the
operator cancelling the run. The first `3dc02567` subject stream succeeded with another
model's answer, which was scored as the pinned model's.

## Rules for this directory

- Never hand-edit a recorded file to make a test pass. If the code must
  change to accept it, change the code; if the reply is genuinely
  non-conforming, the test asserting its rejection is the point.
- A structured reply is checked against the live schema. If a later schema
  refuses a recording, record a new one from a real session rather than editing
  it or keeping an old reader to accept it.
- Add new recordings from real sessions only, a run or a live replay of a real
  run's packet, with the source noted above.
- Recordings are scanned for credential-like bytes by
  `test_recorded_replies.py` before any other assertion runs.
