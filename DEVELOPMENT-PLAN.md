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

**Live acceptance is partial.** These runs have completed end to end:

| Run | Skill | Result |
| --- | --- | --- |
| `76ce4af1` (2026-09-16) | glycoengineering | 4 claims at grade A, 1 operational limitation |
| `1bb3f07a` (2026-09-18) | sar-analysis | 1 at A, 1 at D, 2 voided by faults |
| `e13f50ee` (2026-09-21) | sar-analysis | 4 at A, 1 at B, 1 voided by a fault |
| `fb64115f` (2026-09-22) | sar-analysis | 2 at A, 2 at B, no faults, 51 of 51 observed |
| `7efbdd8c` (2026-09-22) | sar-analysis | 3 at A, 1 at B; 57 of 57 answered correctly, 5 misread |
| `b43780be` (2026-09-22) | sar-analysis | 3 at A, 2 at B, 1 at D; 63 observed, 0 misread, 18 never run |

Every run above used Opus 5, and the verifier is still pinned to it. A move to
`claude-opus-5-5` was made and reverted the same day: the installed Claude Code, 2.1.268,
cannot serve that model, which needs 2.1.280, and WinGet does not yet offer 2.1.280.

What that does and does not establish: the **A and B branches** both carry settled grades
from live runs, and the planner has now used all three comparison methods, including an
open `exact` case written specifically to make the subject generate an answer rather than
recognise one. **Grade C and `qualify_local_evaluator` have never been exercised.** The
documentary path has now run three times: once to completion, once rejected, and once in
`b43780be` for a claim that should have executed first and could not.

**Reply-format noise is gone.** It appeared three times in three forms — a plural in
`e13f50ee`, a capital letter in `fb64115f`, markdown bold in `7efbdd8c` — each a correct
answer the scorer could not read. Run `b43780be` is the first with **zero `invalid`**, and it
exercised the fix rather than avoiding it: nine replies put the answer on the first line and
explained below, which the old reader would have scored `invalid`.

That run still had one false `fail`, of a new kind: a case asking about a consequence the
claim never states, so a subject faithfully applying the skill had nothing to answer from.
That and the reason its D claim never ran are both fixed, in commit `4457ddc`; the full
account is the 2026-09-22 entry in the archive. **Neither fix has been seen on a live
subject yet** — the 2026-09-23 entry below is what to check.

Automated suite: **270 passed, 2 skipped**. Fixtures remain synthetic, reviewed registries
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
- **Claude 2026-09-21 (continued)** — Run `e13f50ee`: six claims, five graded, first
  settled B. Its two `fail` verdicts were answer-wording artifacts, so an exact answer was
  required to have one surface form, and a naming case was ruled out of the representative
  cases grade A needs. Model pin confirmed live; `subject_model_changed` recurred on a
  different claim from a single-session CLI fallback.
- **Claude 2026-09-22** — Four sar-analysis runs. Closed choices became indexed (`choice`),
  replies are read from their first line with markdown removed, and every false failure of
  the week traced to a correct answer the scorer could not read — a plural, a capital, bold.
  An Opus 5.5 switch failed (CLI 2.1.268 cannot serve it) and was reverted. A general review
  made `local-contract.md` authoritative and gave every duplicated fact one owner. The day
  ended with cases required to test no less and no more than their claim, as a mandatory
  sixth reviewer criterion, and with no-grade plans able to run instead of being trapped.

## Claude: 2026-09-23 (handoff: what to check on the next sar-analysis run)

### Current stage and status

A handoff entry. The operator is moving to a new session, and it has none of the previous
session's context, so this entry states what the next session must check rather than
leaving it to be rediscovered.

The code is at `4457ddc`, committed 2026-09-22 16:08 -07:00. Three fixes from that commit
are proven by tests and mutation but **have never met a live subject**:

1. **Reviewer criterion 6 (rubric v3).** Every case must test what its claim asserts — no
   less (only what something is named) and no more (a consequence the claim never states).
   The reviewer must answer it or its whole critique is rejected.
2. **Accepting a D verdict.** A critique supporting D used to trap the planner: D cannot be
   proposed, and reproposing the ceiling was refused. Now reproposing the ceiling accepts a D
   exactly as it accepts "none", and the plan runs ungraded.
3. **The documentary guard.** A qualified candidate that has not been run now blocks the
   documentary path, whether or not it was selected.

One earlier fix has been seen live, but only partly. **The reply reader** was exercised by
run `b43780be` — nine replies with an explanation under the answer, zero `invalid` — but
that run had no bold replies, so the bold branch is proven only by replay and tests.

### What has been done

This session: this entry, plus moving the 2026-09-22 entry to the archive with a condensed
history line. No code changed today. The work it describes is the 2026-09-22 entry, in full
in [DEVELOPMENT-LOG-ARCHIVE.md](DEVELOPMENT-LOG-ARCHIVE.md).

### Before the next run

Check all of these; each one has cost this project a run.

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`
   (`python:3.12-slim`). The preflight does not catch a stopped daemon; run `769b0722`
   lost everything to one.
2. **The verifier server is running current code.** The Python runtime lives in the
   `serve-local` process and does not reload modules. Its start time must be *after* the
   last commit that changed `src/` — currently `4457ddc`, 16:08 on 2026-09-22. Read it with
   PowerShell:
   `Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like '*serve-local*' }`.
   A new chat in a running app reuses the same server. If it predates the commit, restart
   Claude Desktop. At handoff it was pid 40536, started 2026-09-23 00:19, which is current.
3. **The model is `claude-opus-5`.** Read it from the same command line (`--model`). Do not
   move to `claude-opus-5-5`: it needs Claude Code 2.1.280, this machine has 2.1.268, and
   WinGet does not offer 2.1.280 yet (`claude update` defers to WinGet). Run `a8036722` died
   in three seconds on exactly this.
4. **The working tree is clean** at `4457ddc` or a later commit that did not touch `src/`.

### Cleaning the previous sar-analysis run

Move, do not delete — into the session scratchpad. The previous run is `b43780be`:

- `.verifier/runs/b43780be-7a3b-4c6d-b37c-d649fba918bb`
- `.verifier/attempts/04e2ded5-12d3-4942-a73c-3e44f197aedd`
- `.verifier/subject-runs/b43780be-7a3b-4c6d-b37c-d649fba918bb`
- the **eight** candidates in `.verifier/candidates/` whose `method_version` is
  `local-reference-comparison-4`

**Keep** the glycoengineering run: `.verifier/runs/76ce4af1-…`, its attempt `a1ec3e49-…`, its
subject-runs, and the five candidates at `local-reference-comparison-1`. Leave
`.verifier/store/` alone; it is shared and content-addressed.

### What to check in the run

`verify_skill` returns 150–230 KB, which overflows the tool result. Read
`.verifier/runs/<run>/report-card.json` on disk instead.

1. **The run used the new code.** Every critique's `rubric_ref` — at
   `claims[i].audit.critique.rubric_ref` in `report-card.json` — must be
   `07140328e5a3cbdd4eec803717fa0c71e0b05c0c5394d4f73b72b1f581c8663e` (v3). If it is
   `91f33b72c208817675e458838093f10c73d156067e64d10e299509fe8feacd36` (v2), an old server
   ran it and **nothing below counts**. Check this first. (Run `b43780be` shows v2 on all
   six claims, as it should: it ran before `4457ddc`.)
2. **Criterion 6.** Each critique should carry at least six findings, the sixth about case
   scope. Did any critique lower a grade on scope? That is the live evidence the criterion
   binds; a critique that answers it and settles anyway is the failure to look for.
3. **No-grade plans run.** For any claim whose critique supported D or `none`: are its
   observed trials above zero before its documentary assessment? Last time 18 planned
   trials stayed at zero. If no claim is critiqued down that far, say so — the fix is then
   proven by tests only.
4. **`invalid` is still zero.** If not, read the verbatim reply. A new presentation form is
   a gap in the reader; a number inside prose is the reader working as designed.
5. **Claim count.** Recent history is six, four, four, six. Record it; a fall back to four
   would reopen the coverage question.

### Reading the results without fooling yourself

- **Before calling any `fail` a finding about the skill, read the observed reply, the
  expected answer and the reference quote verbatim.** Every misleading result so far looked
  like a real one: a plural and a capital letter scored `fail`, bold scored `invalid`, and a
  case that asked beyond its claim scored `fail`.
- **A unanimous `none of these`** means a broken case far more often than a wrong subject:
  either the options omit the answer or the case asks something the claim never asserts.
- **`claim-00N` directories under `subject-runs/` are numbered in processing order**, not
  in the report's order. Map them by `case_id`.
- **`subject_model_changed`** is upstream fallback inside one CLI session, not a verifier
  bug. The guard is right to void the claim.
- **A `planner_incomplete` recorded as "The operator cancelled this run" can be false.** The
  runner closes any planner that dies early that way (open question 4). The true cause is
  the `process_diagnostic` event in the attempt's `workflow.jsonl`.
- **A clean run is not proof of a fix** if the model simply did not produce the case the fix
  handles.

### Open questions for the operator

Restated from the 2026-09-22 entry, so that entry could move to the archive.

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct for
   every claim seen.
2. **Claim coverage.** Largely answered — six, four, four, six on one model looks like
   variation in extraction, not the rubric. Kept open one more run, because the planner now
   also reads the scope rule and criterion 6 before extracting.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. Their case is semantic, but a subject could
   still lowercase one.
4. **The runner blames the operator for a planner that never started.** Recorded, not
   fixed; it is in the runtime's recovery path. The preflight also never asks the CLI
   whether it can serve the pinned model.
5. **Recognition is untouched.** A `choice` can be passed by spotting the
   conventional-looking option, and distractor quality stays a planner assertion.

### Deferred, and why

- **Opus 5.5** — until WinGet offers Claude Code 2.1.280. Before switching, run
  `claude.exe -p "Reply OK" --model claude-opus-5-5` and look for `unrecognized_model`, as
  `LOCAL-INSTALL.md` describes; treat the first run after as a new series.
- **The case-level contract** — flagged do-not-implement until four or five case-type
  rules accumulate. There are two (naming, scope). Design in the archive, 2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-23"). It is the handoff from the previous session: it lists the
preflight, exactly what to clean, what our recent fixes are, and how to check each
one. Follow it.

Then clean the previous run on sar-analysis as that entry describes, and use
scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\sar-analysis"

Show me the new report and workflow-log paths and the observation counts. Tell me
whether it's a good run or you would recommend another round, and whether our fixes
work — go through the entry's "What to check in the run" list item by item, starting
with the rubric_ref check. Before concluding anything from a `fail`, an `invalid` or
a unanimous "none of these", quote the verbatim reply behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None. The server running at handoff already has current code; the preflight above
re-checks it rather than trusting this entry.

### Suggested next move

Run `sar-analysis` once, and read the planner's and the critique's behaviour, not the
grades. The grades have been established across five runs. What is unknown is whether
criterion 6 lowers an out-of-scope design, and whether a D-critiqued claim now runs.

### Recommended next action

Use the prompt above in a fresh session. It is finished when all five items under "What
to check in the run" have a recorded answer, with item 1 confirmed first.
