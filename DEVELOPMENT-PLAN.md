# Development plan and log

## Rules for maintaining this file

1. Read the latest entry before planning or implementing project changes. Treat it as development context; the reviewed workflow and contracts remain authoritative.
2. Each agent may create only one log entry per calendar day by default. After substantial work, a review that changes the plan, or an agreed change of direction, first look for that agent's entry for today and edit it in place. Create a new daily entry only when none exists. Use a consistent author name across sessions; another session is not a reason to create another entry. Keep entries in chronological order, oldest first.
3. Begin each entry with `## <Author>: YYYY-MM-DD`, for example `## Codex: 2026-09-08`. Use the actual author and the date in `America/Los_Angeles`. Preserve earlier days' entries and record later corrections in the current day's entry. When editing today's entry, briefly identify significant superseded decisions and their replacements. If a significant change would benefit from a separate same-day entry, the agent may ask the user for approval, explaining why; create that additional entry only after explicit approval, and include a time and the approval reference. Otherwise, continue updating the existing daily entry.
4. Include these five fields in every entry:
   - **Current stage and status:** where development stands and what completion means.
   - **What has been done:** completed work, relevant files or commits, verification performed, and material limitations. Distinguish work done in this session from earlier work being summarized.
   - **Urgent next steps, if any:** blockers or prerequisites that must be addressed before dependent work. Write `None` when there are none; distinguish immediate urgency from a prerequisite for later work.
   - **Suggested next move:** the next development direction and its intended outcome.
   - **Recommended next action:** the specific, bounded task to begin next, including how to recognize that it is finished.
5. Keep entries concise and use plain English. Separate confirmed facts, approved decisions, and recommendations. Do not present a proposed task as implemented, approved, or tested.
6. Record unresolved choices that could change scientific meaning or development scope. Recommendations in this log do not themselves authorize implementation or override user decisions.
7. Link relevant repository files with relative paths. Record meaningful validation limits and distinguish local changes from work committed or pushed to GitHub.
8. This file records project development. The future runtime must separately record tool calls, results, state changes, and evidence references for individual verification runs.
9. Entries older than the current one live in [DEVELOPMENT-LOG-ARCHIVE.md](DEVELOPMENT-LOG-ARCHIVE.md), condensed below under "History". Move an entry there once its work is finished and its open questions are settled or restated in a later entry. Condense; never delete.

## Current state

Version 0.7.0 implements the local workflow. `verify` and `serve-local` provide one public
action; Claude Code owns the planner loop and fresh subject sessions; Python owns
deterministic tools, bounded processes and saved evidence.

**Live acceptance is partial.** Three runs have completed end to end:

| Run | Skill | Result |
| --- | --- | --- |
| `76ce4af1` (2026-09-16) | glycoengineering | 4 claims at grade A, 1 operational limitation |
| `1bb3f07a` (2026-09-18) | sar-analysis | 1 at A, 1 at D, 2 voided by faults |
| `e13f50ee` (2026-09-21) | sar-analysis | 4 at A, 1 at B, 1 voided by a fault |

What that does and does not establish: the **A and B branches** both now carry settled
grades from live runs. **Grade C and `qualify_local_evaluator` have never been exercised.**
The documentary path has run twice, once to completion and once rejected, and not at all in
the most recent run. No run has yet exercised the evaluator-quality rules added on
2026-09-21, so their effect on a live planner is unmeasured.

Automated suite: **257 passed, 2 skipped**. Fixtures remain synthetic, reviewed registries
remain empty, and nothing in the automated suite establishes scientific acceptance.

## History

Full text in [DEVELOPMENT-LOG-ARCHIVE.md](DEVELOPMENT-LOG-ARCHIVE.md). Condensed, oldest
first. Designs described here were often later changed; the archive records how, and the
reviewed contracts under `skills/scientific-verifier/references/` outrank both.

- **Codex 2026-09-08** — Stage 1 complete as a reviewed Markdown specification: seven
  contract documents, no runtime. Established the three-stage plan and the log itself.
- **Codex 2026-09-09** — Stage 2's deterministic implementation and Claude Desktop
  installation packages ready; live acceptance pending, no scientific evaluation yet.
- **Claude 2026-09-10** — Reviewed Stage 2 against the contracts, reproduced the main
  failures, and published two bounded repair batches.
- **Codex 2026-09-10** — Version 0.3.0: claim routing, catalog release verification, cache
  activation, immutable pins, per-claim evaluator selection. Stopped at `stage3_complete`.
- **Codex 2026-09-11** — User direction: retire the demo branch and build the
  personal/local first version on `main`. Superseded the demo-first recommendation.
- **Codex 2026-09-11 19:32 PDT** — Authorized same-day entry. Removed the narrow goal
  files and retired the text-only, chemical-only and demo completion boundaries.
- **Codex 2026-09-12** — Version 0.7.0: computation, resources, evaluator construction,
  repeated trials, scientific eligibility, independent documentary assessment, catalog
  reuse and workflow logs, ready for manual acceptance.
- **Codex 2026-09-14** — Install guide corrected to one Docker path plus upgrade
  instructions, after an explanatory question was mistakenly expanded into alternatives.
- **Claude 2026-09-15** — Requested repair and full code review: three design defects
  fixed, dead files removed, `tmp/legacy_fixed_workflow/`, `reviews/` and the superseded
  `evaluators/chemical_mass/` helper deleted.
- **Claude 2026-09-16** — First live run reached real Claude Code and failed before
  snapshotting (`source_not_authorized`). Two host-boundary defects fixed with tests.
- **Claude 2026-09-16 (rerun)** — Run `76ce4af1` completed end to end: four claims at
  grade A, 66 of 66 trials passed. First live run carrying a claim from snapshot to
  settled grade to report. Acceptance declared **partial**, A-branch only.
- **Claude 2026-09-18** — Two sar-analysis runs; the second graded but discarded its most
  useful finding. Proposed the six-axis report card. Also recorded the automatic
  dependency-resolution design, flagged do-not-implement.
- **Claude 2026-09-21 (six-axis implemented)** — The redesign built, contracts first.
  `decide()` no longer welds grade to behaviour; a claim scoring 13 of 15 now reports
  grade A, status `fail`, consistency `split`. Suite 240 → 251.

## Claude: 2026-09-21 (continued: live rerun and two evaluator-quality fixes)

This continues the same calendar day as the six-axis entry, which is now in the archive.

### Current stage and status

The rerun that entry asked for happened and **completed end to end**. Run
`e13f50ee-a390-4130-83e6-8641cfd28367` closed as `completed` with
`completion_reason: local_report_complete`: six claims extracted, **five settled with a
grade and a status**, one closed as an operational limitation, 69 scored trials of which 66
passed, and a full report written. It ran against `main` at `536733d` plus the
unused-import cleanup then in the working tree, started 2026-09-21T23:17:25Z, finished
2026-09-22T00:14:08Z, about 57 minutes, recorded cost $15.32, 53 steps, 78 subject calls,
observed planner model `claude-opus-5`.

Three things the previous two entries were waiting on all landed. The `rdFMCS threshold`
claim reached **A with 12 of 12 executed trials** rather than the predicted B. The
`makeDummiesQueries` claim produced **grade A, status `fail`, consistency `split`** instead
of vanishing — the defect the six-axis card was built to fix, confirmed live. And
`RGroupDecompose` settled at **B**, the first settled B grade in the project's history.

The substance of this entry is not the grades. It is that **the run's two `fail` verdicts
were artifacts of how the tests were written rather than findings about the skill**, and
the two fixes that follow from that. Both are committed.

### What has been done

**1. Claim by claim, against run `1bb3f07a`.**

Same submission, byte-identical snapshot (`SKILL.md`, 23,276 bytes). Trial count 3.

| Claim | `1bb3f07a` | `e13f50ee` |
| --- | --- | --- |
| pIC50 definition | A / pass, 12 of 12 | **A / pass**, 15 of 15 |
| `rdFMCS` threshold | no grade, `subject_model_changed`, 5 of 12 | **A / pass**, 12 of 12 |
| `DrawMoleculeACS1996` | D / inconclusive (documentary) | **A / fail / split**, 18 of 18 |
| `makeDummiesQueries` | no grade, `assessor_response_invalid`, 15 of 15 | **A / fail / split**, 12 of 12 |
| `RGroupDecompose` | not extracted | **B / pass**, 12 of 12 |
| `GenerateDepictionMatching2DStructure` | not extracted | no grade, `subject_model_changed`, 9 of 15 |

Every claim that carried a fault last time now carries a grade. `DrawMoleculeACS1996` moved
off the documentary path entirely, which is why the malformed-assessor-reply fault stopped
mattering on its own, as predicted. `overall_scientific_grade` is `None` only because the
sixth claim is ungraded.

**2. The model pin was necessary and not sufficient.**

Open question 2 of the six-axis entry is closed: the MCP server is re-registered with
`--model claude-opus-5`, and `subject_config.model_id` and the controller receipt both
record it.

The `subject_model_changed` fault did not go away. **It moved.** The failing observation is
`claim-002/009-response.json`, case `depiction-reference-needs-coords`: `model_id` is
`claude-opus-5` as requested, but `observed_model_ids` is
`["claude-opus-4-8", "claude-opus-5"]` — the CLI served part of **one session** from another
model. That is upstream fallback inside a single session, not alias resolution differing
between sessions, so pinning on this side cannot prevent it. The guard behaved correctly:
`status_withheld_reason: unattributable_observations`, eight completed trials discarded.

A navigation trap worth recording: `subject-runs/<run>/claim-00N` directories are numbered
in processing order and **do not** match claim-id hash order in the card. The faulted claim
was `claim-006` in the report and `claim-002` on disk. Map by `case_id`.

**3. Two `fail` verdicts that a chemist would not endorse.**

Both came from documentation-phrasing recall under exact string comparison:

- `dummies-conversion-target`: expected `"any-atom queries"`, one trial answered
  `"any-atom query"`. Singular against plural.
- `acs1996-guideline-target`: expected `"ACS 1996 guidelines"`, two trials of three
  answered `"ACS 1996 mode"`.

Under `unanimity` a single such trial fails the claim. The run's own critique on claim 1 had
already named the general problem: the oracle "measures recitation fidelity as a proxy for a
semantic claim," and a behavioural oracle was "available and unused."

**4. Fix one: an exact answer must have one correct surface form** (`e5329de`).

Contracts first. `qualify()` already required every expected value to be a verbatim quote
from a fetched reference, which keeps the answer key out of the model's hands and should not
be relaxed. Its unstated side effect: the only askable questions are ones whose answer is a
literal string in a document, so cases drift toward reciting prose, and
`actual.strip() == expected.strip()` cannot tell a paraphrase of a right answer from a wrong
one. Nothing constrained the *form* of the answer that rule produces.

`qualify_local_candidate` now requires two forms only: a whitespace-free token, or a closed
choice, where the case lists `options` and its `input` presents every one of them verbatim
so the subject selects rather than phrases. `options` is an optional schema field, so
existing token cases are unchanged. Controls probe each rejected option as well as the near
misses. Numeric answers take no options. Whether a distractor is genuinely wrong stays a
planner assertion, recorded in `QUALIFICATION_LIMITS`.

Replayed against the **64 real cases** from all live runs, the rule flags 8 and leaves 56
untouched. The 8 are both verdicts above, the prose case belonging to the claim voided for
the model swap, `"fraction of the dataset that must contain the MCS"` in both runs,
`"SVG molecule drawer"`, and `"unsigned int"`. The last four passed on luck.

Six tests added, mutation-tested: disabling the rule fails four of the six, the other two
being the positive control and the probe-count assertion.

**5. Fix two: a naming case does not test a behavioural claim.**

Fix one removes the wording lottery. It does **not** remove recitation. "What is the flag
called?" is a single token, passes the new rule cleanly, scores 3 of 3, and says nothing
about whether the claim is true. Three such cases scored perfectly in this run.

The structural cause is incentive, not laziness. The planner must propose the strongest
grade its design supports, and a naming case satisfies every mechanical A requirement
trivially — the name is in the docs, it is one clean token, exact match compares it
perfectly. Naming cases were the cheapest route to an A.

Python cannot separate them: once quoted, `51` (a glycosylation position, a real scientific
fact) and `makeDummiesQueries` (pure vocabulary) are the same shape. So this is left where
judgment already lives. `evidence-rubric.md` now states that a case testing what something
is *named* does not count toward the representative cases grade A requires when the claim is
about behaviour, meaning or a numeric relationship, and that naming cases remain legitimate
where the claim is itself about an API surface. The critique packet note
(`local.py`) points at that rule and says plainly that a finding which does not move the
grade changes nothing. `coverage` in the planner's justification must now state which cases
test what the claim asserts rather than what it is named.

No new mechanism was needed. The revision loop already exists: the critique lowering the
grade fires `local_grade_revision_required`, which returns `objections`,
`required_revisions` and `rounds_remaining` to the planner, and the rubric already lists
"cases that cover the stated scope" as a legal way to strengthen a design. It never fired in
this run because the trigger is `settled_ceiling != target_grade`: the planner proposed A,
the critique supported A, so the objection was recorded as a finding and changed nothing.

### Decisions taken 2026-09-21 (continued)

**1. Fault discards, bad accuracy keeps. Confirmed, not changed.** The operator restated the
principle: a fault inside the verifier, such as a model switch, throws the evidence away,
while poor accuracy or consistency is a finding about the skill or the world and keeps
everything. That is what the code does, and this run demonstrates both halves — two claims
with failing trials kept all their observations and were graded, and the faulted claim
discarded its eight. A refinement to retry only the affected trial rather than discard the
claim was raised and **not adopted**; it remains available if the 1-in-5 claim loss rate
across two runs becomes annoying.

**2. No machinery for computed ground truth. Decided: let the grade fall.** The question was
how to support a behavioural oracle whose expected value no document states. The operator's
answer: if nobody published it, the evidence genuinely is weaker, so it should earn a low
grade and be left to the AI to propose and the critique to settle. Building a mechanism to
manufacture an answer key is rejected. Note that behavioural tests **are** reachable today
where the reference itself publishes a worked example with its output; that path is
underused rather than blocked.

**3. The grade covers the whole evidence design, not the reference alone.** The six-axis
entry said the grade "answers one question, how good the reference was." That phrasing is
narrower than the code, which already grades case count, token-exactness, comparison
determinism and trial count alongside reference origin, and `POLICY["axes"]` says "reference
and test bundle." The operator confirmed the broader reading: the grade should reflect the
whole testing process, including how the tests were built, because a reader cannot be
expected to audit cases one by one. The contrast the earlier entry was drawing — against
*behavioural and operational* reasons — still holds exactly.

**4. Relevance, not strictness.** A proposal to instruct the planner toward "the strictest
kind of test" was considered and **rejected**. A naming case is already maximally strict:
exact match, zero tolerance, no partial credit, and it still tests nothing. Strictness
invites trick questions; the property wanted is whether the case tests what the claim
asserts.

### Open questions for the operator

**1. Should the aggregation rule become a plan field?** Carried forward unchanged from the
six-axis entry. Still `unanimity`, still recorded on every card, still correct for every
claim seen so far. Two triggers reopen it: a claim genuinely worded as typical behaviour, or
a trial count raised far enough that unanimity fails sound skills on noise.

**2. Does the naming rule actually change what the planner writes?** This is the one real
unknown. Both fixes are enforced at different strengths: fix one is mechanical and cannot be
ignored, fix two is a rule the critique must choose to apply — and the last critique named
the problem and waived it anyway. The check is cheap and exact, because the report card saves
both the critique's findings and the settled grade.

### Urgent next steps, if any

None. Everything above is committed and pushed, the suite is green at 257 passed, 2 skipped,
and nothing is half-applied.

### Suggested next move

Rerun `sar-analysis` against the current `main` and read the planner's behaviour rather than
the grades. Four of the grades are established twice over and are not the point.

### Recommended next action

Run `sar-analysis` once and answer two questions from the saved card. First: what did the
planner write for the eight cases fix one now rejects — closed choices that still settle at a
grade, or narrower claims that dodge the rule? Second: for any claim whose cases are mostly
naming, did the critique object **and lower the grade**, or object and settle anyway? It is
finished when both have a recorded answer. If the second answer is "objected and settled
anyway," the cheap fix has failed and the next step is forcing the planner to declare
per-case intent in the schema, which is a larger change and should not be paid for until
this one is shown insufficient.
