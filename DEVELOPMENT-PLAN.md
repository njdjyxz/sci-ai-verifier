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
| `b0955d2f` (2026-09-23) | sar-analysis | 1 at A, 2 at B, 1 at D; 54 of 54 passed, 0 invalid, 0 faults |

Four more sar-analysis runs on 2026-09-23 (`28d19f8a`, `d87a6d5c`, `0a243b7e`, `74eadedd`) are
described only in the messages of commits `a202146` and `041552c`. Run `7f88fbef` stopped on
the subscription session limit.

Every run above used Opus 5, and the verifier is still pinned to it. A move to
`claude-opus-5-5` was made and reverted the same day: the installed Claude Code, 2.1.268,
cannot serve that model, which needs 2.1.280, and WinGet does not yet offer 2.1.280.

What that does and does not establish: the **A and B branches** both carry settled grades
from live runs, and the planner has now used all three comparison methods, including an
open `exact` case written specifically to make the subject generate an answer rather than
recognise one. **Grade C and `qualify_local_evaluator` have never been exercised.** The
documentary path has now run four times: once to completion, once rejected, once in
`b43780be` for a claim that should have executed first and could not, and once in `b0955d2f`
after that claim's ungraded plan had executed first, as it now must.

**Reply-format noise is gone.** It appeared three times in three forms — a plural in
`e13f50ee`, a capital letter in `fb64115f`, markdown bold in `7efbdd8c` — each a correct
answer the scorer could not read. Run `b43780be` is the first with **zero `invalid`**, and it
exercised the fix rather than avoiding it: nine replies put the answer on the first line and
explained below, which the old reader would have scored `invalid`.

That run still had one false `fail`, of a new kind: a case asking about a consequence the
claim never states, so a subject faithfully applying the skill had nothing to answer from.
That and the reason its D claim never ran were fixed in commit `4457ddc`; the full account
is the 2026-09-22 entry in the archive. Run `b0955d2f` then saw several of the week's fixes
work live, including the no-grade path and the scope verdict, and exposed four problems
fixed the same day but **not yet seen live**. The 2026-09-23 entry below has both.

Automated suite: **301 passed, 2 skipped**. Fixtures remain synthetic, reviewed registries
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

## Claude: 2026-09-23 (handoff, run b0955d2f, four fixes)

### Current stage and status

Version 0.7.0, local workflow. This entry began at 00:25 as a handoff checklist for a fresh
session and now records the day. Superseded from that version: the rubric digest to check is
v5 (`bf944269…`), not v3, because commit `a202146` moved the critique rubric on; the run to
clean is `b0955d2f`, not `b43780be`; and the runner no longer blames the operator for a
planner that stopped by itself (formerly open question 4), pending a live run.

Run `b0955d2f`, on commit `041552c`, completed cleanly: four claims at A, B, B and D, 54 of 54
trials passed, no `invalid`, no faults, every trial on `claude-opus-5`. It proved live:

- the five-minute critique deadline: two critiques took 123 s and 124 s and completed;
- a no-grade plan running before its documentary assessment: claim 3's nine trials ran first;
- case verdicts binding: a `beyond_scope` case and a `duplicate` case each stayed out of a grade;
- an exhausted replacement budget: claim 3's third critique settled it.

It did not exercise four fixes from `041552c`, which stay proven by tests only: an `exact`
answer followed by an explanation (all 54 replies were a single line), extra keys in a case
verdict (none of seven critiques added one), the varied-position rule (all nine designs
varied unprompted), and a `choice` case with no options.

It exposed four problems, fixed in this session with contracts first. **The fixes are tested
and pushed to `main` in the commit that carries this entry, but have not met a live run.**

### What has been done

Earlier today, by other sessions, summarised from their commit messages:

- `593ff24`: this entry's original handoff checklist.
- `a202146`: grades counted over the cases the critique counts ("Cases each grade requires"
  in `evidence-rubric.md`), a verdict per case, two replacement rounds, `mixed` designs,
  rubric v5, policy `evidence-strength-v4`, the rubric's case sections pinned to the planner,
  and retried temporary-directory cleanup. Runs `28d19f8a` and `d87a6d5c`.
- `041552c`: `exact` read from the first line, up to four extra keys in a case verdict, varied
  `choice` positions, a five-minute critique deadline, and a `choice` without options refused
  at qualification, under qualification version `-5`. Runs `0a243b7e` and `74eadedd`.

This session:

- Run `7f88fbef`, on `041552c`, stopped after 40 minutes: its planner hit the subscription
  session limit (HTTP 429), and the runner recorded that as the operator's cancellation. Its
  files were moved to the session scratchpad.
- Run `b0955d2f`: results above. Report
  `.verifier/runs/b0955d2f-fb7a-4e47-8cec-e8495f1b12e8/report-card.md`, workflow log
  `.verifier/attempts/7f6b7cd3-b609-4247-90e3-be450496454b/workflow.md`. About $20.89 at API
  rates, $13.14 of it the planner.
- Problems it exposed:
  1. The planner told reviewers what earlier reviews decided, three times, through its own
     notes: "The previous round settled at C…", "…the previous no-grade outcome", and "Two
     independent critiques have given this case the verdict counts." The hidden-grade rule
     was enforced only on what Python itself carries.
  2. Two pages were refused under one message naming two possible causes. Both were size: a
     974 KB tutorial holding 21 KB of text, and a 344 KB source listing holding 88 KB. The
     planner guessed the cause, and its guess reached the documentary packet as fact.
  3. Claim 3's D followed one verdict on an unchanged case: counted by two reviewers, then
     called `leaked` by the third, correctly (the question named `makeDummiesQueries`, and
     only the right option mentioned dummy atoms). Its design held exactly the minimum.
  4. `7f88fbef`'s false "operator cancelled" record.
- Considered and dropped because they contradict the reviewed design: changing
  `replacement_rounds_remaining` (`local-contract.md` counts a round when its critique rejects
  cases, so the counter is right), hiding the justification from the critique, a
  Python-computed leak hint (judging cases is the critique's job), and a bigger page limit
  without bounding the reply. The operator declined lowering grade A's case count and chose
  to keep earlier grades hidden from reviewers.
- The four fixes:
  1. **Hidden grade enforced against planner notes.** Step 3 of "Negotiating the grade" in
     `evidence-rubric.md` owns the rule. `select_local_candidate` refuses
     `prior_review_in_packet`, naming the field and phrase, before a critique session starts.
  2. **Page limits.** `reference_too_large` and `reference_credential_material` replace the
     single refusal, pages may hold up to 2 MiB, and the reply carries at most 40 KiB of text
     with `text_truncated` while the whole page is pinned. `tool-contracts.md` owns the numbers.
  3. **Who stopped a run.** `cancelled` only for the operator, `timeout` for the deadline, and
     otherwise `agent_unavailable` with the planner's own last result, as
     `artifact-contracts.md` already required. The runner passes it by a keyword no tool
     argument can set, so no tool schema changed. New real recording
     `tests/recorded/planner-session-limit.jsonl`.
  4. **A spare case**, in "Cases each grade requires".
- Verification: suite 294 → 301 passed, 2 skipped. The new tests fail against the old code,
  except the one proving that accepting a settled grade is never refused. Six one-line
  mutations of the fixes were each caught. One test replays `7f88fbef`'s real stream through
  `verify()` and checks the saved outcome and partial report.

### Before the next run

Check all of these; each one has cost this project a run.

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`
   (`python:3.12-slim`). The preflight does not catch a stopped daemon.
2. **The verifier server is running current code.** This session changed `src/`, so the
   `serve-local` process must have started after the commit that carries these fixes. Python
   does not reload modules, and a new chat in a running app reuses the same server. Read the
   start time with PowerShell:
   `Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like '*serve-local*' }`,
   and restart Claude Desktop if it predates the commit.
3. **The model is `claude-opus-5`**, read from the same command line. Claude Code 2.1.268
   cannot serve `claude-opus-5-5`, and WinGet does not yet offer 2.1.280.
4. **The working tree is clean** at that commit, or at a later one that did not touch `src/`.
5. **The plan's 5-hour window has room.** `7f88fbef` died on it, and a run costs about $21 at
   API rates.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `b0955d2f`:

- `.verifier/runs/b0955d2f-fb7a-4e47-8cec-e8495f1b12e8`
- `.verifier/attempts/7f6b7cd3-b609-4247-90e3-be450496454b`
- `.verifier/subject-runs/b0955d2f-fb7a-4e47-8cec-e8495f1b12e8`
- the **nine** candidates in `.verifier/candidates/` whose `method_version` is
  `local-reference-comparison-5`

**Keep** the glycoengineering run: `.verifier/runs/76ce4af1-…`, its attempt `a1ec3e49-…`, its
subject-runs, and the five candidates at `local-reference-comparison-1`. Leave
`.verifier/store/` alone; it is shared and content-addressed. Do not leave a shell inside a
directory you are moving: on Windows that blocks its removal.

### What to check in the run

`verify_skill` returns about 190 KB, which overflows the tool result. Read
`.verifier/runs/<run>/report-card.json` on disk instead.

1. **The new code ran.** The critique rubric did not change (`bf944269…`, v5), so its digest
   cannot show this; the server's start time can (item 2 above). A cut fetch reply carries
   `text_truncated`, and a refused note returns `prior_review_in_packet`.
2. **The new refusal.** Did the planner meet `prior_review_in_packet`, and did it rewrite the
   note and continue without looping? Quote the note it rewrote.
3. **Pages.** Any `reference_too_large`, `reference_credential_material` or `text_truncated`?
   Did a cut page still give the planner the quotes it needed?
4. **Spare cases.** Did designs hold one more independent case than their grade needs, and
   did one absorb a rejected case?
5. **Still unexercised from `041552c`:** an `exact` answer followed by an explanation, extra
   keys in a case verdict, the varied-position refusal, and a `choice` with no options. Say
   which, if any, occurred.
6. **`invalid` is still zero.** Record the claim count too: `b0955d2f` extracted four,
   `74eadedd` three.

### Reading the results without fooling yourself

- **Before calling any `fail` a finding about the skill, read the observed reply, the
  expected answer and the reference quote verbatim.** Every misleading result so far looked
  like a real one.
- **A unanimous `none of these`** means a broken case far more often than a wrong subject.
- **`claim-00N` directories under `subject-runs/` do not follow the report's order.** Map them
  by `case_id`.
- **`subject_model_changed`** is upstream fallback inside one CLI session, not a verifier bug.
- **A run the runner closed should now say `agent_unavailable`** with the planner's own
  reason. If it still says "The operator cancelled this run." for a stop nobody made, the
  server is running old code.
- **`workflow.jsonl` truncates long tool results** at about 16 KB. The whole request and
  result of every tool call, including every critique round and not only the final one, is
  in `.verifier/runs/<run>/events/`.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct for
   every claim seen.
2. **Claim coverage.** `b0955d2f` extracted four claims and `74eadedd` three. Still open.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. Their case is semantic, but a subject could still
   lowercase one.
4. **The preflight never asks the CLI whether it can serve the pinned model.** The other half
   of the old question, the runner blaming the operator, is fixed today and awaits a live run.
5. **Recognition is untouched.** Claim 3's leaked case is an instance: the only option naming
   dummy atoms was the right one.
6. **The section reader can return up to 128 KiB** (`get_verifier_context` with `section`),
   above the 53 KB reply once spilled to a file. It has not been seen to fail.
7. **Reviewers disagree on unchanged cases.** The rule that the latest critique governs and
   may only lower the grade is the conservative one; the spare-case guidance is being tried.

### Deferred, and why

- **Opus 5.5** — until WinGet offers Claude Code 2.1.280. Before switching, run
  `claude.exe -p "Reply OK" --model claude-opus-5-5` and look for `unrecognized_model`, as
  `LOCAL-INSTALL.md` describes; treat the first run after as a new series.
- **The case-level contract** — flagged do-not-implement until four or five case-type rules
  accumulate. Commit `a202146` has since added answer forms and four case verdicts, which
  overlap this design; whether they settle it has not been reviewed. Design in the archive,
  2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-23"). Follow its preflight, clean the previous run as it
describes, and use scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\sar-analysis"

Show me the report and workflow-log paths, a table with one row per claim
(grade, accuracy, consistency, status and the other measurements) and, for each
claim, a table with one row per test. Tell me whether it is a good run, and
whether our fixes work: go through the entry's "What to check in the run" list
item by item. Before concluding anything from a `fail`, an `invalid` or a
unanimous "none of these", quote the verbatim reply behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None now. Before the next live run, restart Claude Desktop so `serve-local` loads the commit
that carries these fixes; the server running when it was made started before it.

### Suggested next move

Run `sar-analysis` once on the new code and read the planner's behaviour rather than the
grades: whether it meets the new refusal and recovers, whether a fetch reply is cut, and
whether designs carry a spare case.

### Recommended next action

Restart Claude Desktop, confirm the server started after this commit, clean `b0955d2f` as
above, and run once. It is finished when every item under "What to check in the run" has a
recorded answer.
