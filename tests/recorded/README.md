# Recorded independent-session replies

These are **not synthetic fixtures**. Each `.jsonl` file is the verbatim
Claude Code stream-json event sequence that a real session emitted, captured
either by the workflow log of a local run or by a live replay of a real run's
packet through the code that reads it.

They exist because every other test in this suite writes the model's reply by
hand, in a shape that already satisfies the validator. That is how
`critic_response_invalid` reached a live run and discarded three completed
critiques: 215 tests passed while the real boundary failed on its first
contact with a real reply. A recorded reply cannot be written to match the
code, so it is the only test data here that can actually falsify the parser.

| File | Role | Source | What it captures |
| --- | --- | --- | --- |
| `critic-task-structured.jsonl` | critic | live replay, 2026-10-15 | Run `3f073fec` claim 1's packet, a demo skill's made-up QC score and 7.2 cut-off whose four tasks tested only the score's inputs, with the live rubric `local-task-critique-v8` in place of v7. `claude-opus-5` at `high` answered for $0.57, accepted first time: grade B against the live critique's A, one task a duplicate, and in `unsourced_rules` the score formula and the cut-off, each quoted exactly from the claim's section and marked `searched: false`, since the run's search record held no search for either. Under v7 the same rules were U; under v8 they are not looked up. Earlier recordings, among them the v7 one and `cfe9e57a`'s two-step packet, are in Git history |
| `judge-structured.jsonl` | judge | live replay, 2026-10-13 | The first of two judges of a packet built from run `3f073fec`'s phospho-blocking task: its job, a real trial's answer, and two criteria quoted from the vendor guide its keys rested on. Both judges answered yes to both criteria ($0.037 and $0.029). Its first reply was wrapped in a stray `$PARAMETER_NAME` key; refused and resent |
| `critic-structured.jsonl` | critic | live replay, 2026-10-01 | Run `d416f79d`'s pIC50 critique under the question rubric v13, retired with question tests on 2026-10-05. Kept only as live evidence of Claude Code's correction loop: its first reply added a stray `StructuredOutput` key, which the schema refused, and the session resent it. Its packet and the earlier recordings are in Git history |
| `critic-refused-tool.jsonl` | critic | `4f16f74d`, 2026-10-12 | Claim 1's task critique at `high`, rebuilt from the run's events journal. Started with `StructuredOutput` only, it asked for `bash` to recompute the extinction coefficients; Claude Code refused ("No such tool available: bash"), and it replied in shape, supporting A. The verifier counted the refused call as a boundary violation and the claim ended with no grade, as claim 4 of run `b573cd15` did. Its reply predates rubric v7, so the live schema refuses it (no `unsourced_rules`): it proves the refused-call boundary only, and a critique that asks for a tool under the live rubric should replace it |
| `assessor-structured.jsonl` | assessor | live replay, 2026-10-13 | Run `3f073fec` claim 3's documentary packet, a made-up "Hartwell-Nakamura" fade correction against a general blot review, under rubric `local-documentary-v2`. Live under v1 it settled at D, inconclusive; here all seven statements are not addressed, so Python gives `no_evidence`, grade U. $0.12, accepted first time. `a392ea65`'s v1 recording is in Git history |
| `claim-probe-structured.jsonl` | claim-only | live replay, 2026-09-28 | Run `d416f79d`'s `pic50-one-nanomolar` case answered from its claim alone, a check retired with question tests. Kept, like the critique, for the correction loop: its first reply added a stray `a` key; refused and resent |
| `subject-safety-refusal.jsonl` | subject | `e035eef6` | Provider safety refusal, category `bio`, with a fallback model that also refused |
| `planner-session-limit.jsonl` | planner | `7f88fbef` | The planner's last two events: the CLI's `rate_limit` message and a `result` with `terminal_reason` `api_error`, HTTP 429, "You've hit your session limit" |
| `subject-refusal-fallback.jsonl` | subject | `3dc02567` | Opus 5 refused an R-group question after the skill loaded; a `model_refusal_fallback` event, then `claude-opus-4-8` wrote the answer `R1` and the session succeeded |
| `subject-refusal-recovered.jsonl` | subject | `3dc02567` | The same case: `model_refusal_no_fallback`, a `<synthetic>` refusal notice, then `claude-opus-5` answered `R1` itself |

`assessor-packet.json`, `critic-task-packet.json` and `judge-packet.json` are the exact packets
those sessions were given, so each reply can be checked against the bytes it actually saw.

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
model's answer, which was scored as the pinned model's. The `b573cd15` and `4f16f74d`
critiques each lost a claim to a `bash` call Claude Code had already refused.

## Rules for this directory

- Never hand-edit a recorded file to make a test pass. If the code must
  change to accept it, change the code; if the reply is genuinely
  non-conforming, the test asserting its rejection is the point.
- A structured reply is checked against the live schema. If a later schema
  refuses a recording, record a new one from a real session rather than editing
  it or keeping an old reader to accept it. The two recordings kept only for the
  correction loop are the exception: their schemas were retired, so nothing
  checks their replies.
- Add new recordings from real sessions only, a run or a live replay of a real
  run's packet, with the source noted above.
- Recordings are scanned for credential-like bytes by
  `test_recorded_replies.py` before any other assertion runs.
