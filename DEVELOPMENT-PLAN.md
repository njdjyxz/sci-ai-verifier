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
| `3dc02567` (2026-09-24) | sar-analysis | 4 at A, 1 at B, 1 voided by a refusal fallback; 95 of 95 scored trials passed |

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
work live and exposed four problems, fixed the same day. Run `3dc02567` saw three of those
four work, and exposed a refusal fallback that let another model's answers be scored as the
pinned model's. The fix for that, an end-of-run re-run and four smaller fixes are **not yet
seen live**; the 2026-09-24 entry below has the details.

Automated suite: **315 passed, 2 skipped**. Fixtures remain synthetic, reviewed registries
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
- **Claude 2026-09-23** — Handoff checklist, then runs `7f88fbef` (stopped on the subscription
  session limit) and `b0955d2f` (A, B, B, D; 54 of 54 passed). Planner notes that told the
  critique earlier outcomes are refused before a session, pages may hold 2 MiB with 40 KiB
  replies, a run the runner closes names who stopped it, and the rubric asks for a spare
  case. Other sessions that day committed `a202146` and `041552c`.

## Claude: 2026-09-24 (run 3dc02567; one model per trial, an end-of-run re-run, four smaller fixes)

### Current stage and status

Version 0.7.0, local workflow. Run `3dc02567`, on commit `18ef2b9`, completed: six claims at
A, A, A, B and A, and one voided; 95 of 95 scored trials passed, with no `invalid`. It saw
three of `18ef2b9`'s four fixes work live. The page limits admitted the RGD tutorial that
`b0955d2f` had refused, and cut two long pages to 40 KiB. The spare case kept claims 3 and 6
at A after the critique rejected one case each. The prior-review refusal fired once, on a false
positive. The stop-reason fix did not come up.

Claim 4 exposed a real hole. It was voided as `subject_model_changed`, but the cause was
Opus 5's safety filter refusing an R-group question, after which Claude Code answered two
trials with `claude-opus-4-8`. The guard pinned the first trial's mixed model set, so trial 2
was scored as stable, and only trial 3, which Opus 5 answered itself, voided the claim.

This session's fixes, contracts first, are tested and **pushed to `main` in the commit that
carries this entry, but have not met a live run**:

1. **One model per trial.** Subject sessions run with Claude Code's substitution switched off,
   and Python refuses any trial another model answered. A refusal another model answered is
   `subject_refused`, naming that model. A `<synthetic>` notice is not a model, so a refusal
   Opus 5 then answered itself counts, with the refusal noted on the trial. "Subject boundary"
   in `local-contract.md` owns the rule.
2. **One disclosed re-run at the end.** `write_report_card` re-runs once, in full, each claim a
   subject-trial fault stopped. A wrong answer, a security fault and a failure of Python's own
   checks are never re-run. A claim is skipped, with the reason recorded, when its plan settled
   no grade, the call budget cannot cover it, or the time left cannot. Both attempts are
   reported.
3. **The prior-review trigger** now needs `settled at`, not bare `settled`.
4. **Leak patterns**, taken from the reviewers' own reasons, in "Cases each grade requires".
5. **Section and resource-preview replies** get the 40 KiB reply limit in the local profile.
6. **A startup model probe**: a CLI that cannot serve the pin stops the run as
   `model_unavailable` before any planner or subject cost.

Superseded today: a safety refusal "is never retried", because "the identical request refuses
again". Trial 3 of claim 4 disproved that, and the operator chose one disclosed re-run at the
end instead. Also superseded: the earlier reading of `subject_model_changed` as random CLI
fallback. It was a refusal fallback, and the 2026-09-21 case may have been one too.

### What has been done

This session:

- Cleaned `b0955d2f` into the session scratchpad and ran `3dc02567`. Report
  `.verifier/runs/3dc02567-756f-4b76-9ae7-7de1d964b915/report-card.md`, workflow log
  `.verifier/attempts/e8507224-d9b0-4e11-8abc-88a9e58c5411/workflow.md`. About $35 at API
  rates: planner $22.11, subjects $10.11, critiques $2.78.
- It took 90 minutes, and the planner finished 8 seconds inside the app's 5,400-second limit.
  The planner's own thinking took 41 minutes, 96 sequential trials took 29 minutes (18 s each),
  and nine critiques took 19. Six critiques ran 121–147 s, past the old two-minute deadline.
- Implemented the six fixes above. `artifact-contracts.md` describes the new `refusals` and
  `retry_ref` fields. `LOCAL-INSTALL.md` notes that the model check is now automatic.
- Verification: suite 301 → 315 passed, 2 skipped. Seventeen one-line mutations of the fixes
  were each caught. Two new real recordings from `3dc02567`,
  `tests/recorded/subject-refusal-fallback.jsonl` and `subject-refusal-recovered.jsonl`, are
  replayed through the real subject adapter.
- Not verified: whether `CLAUDE_CODE_NO_MODEL_FALLBACK` and
  `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK` stop the fallback at the source. Testing that needs a
  live subject session with the desktop app's token. The stream check enforces the rule
  either way.
- Considered and not done: lowering grade A's case count, cutting review rounds, fewer trials,
  a verdict that sticks across rounds, and not running rejected cases. Each weakens what a grade
  means or breaks the rule that everything observed is reported.

### Before the next run

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`
   (`python:3.12-slim`).
2. **The verifier server started after the commit that carries these fixes.** Read the start
   time with
   `Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like '*serve-local*' }`,
   and restart Claude Desktop if it predates the commit.
3. **The model is `claude-opus-5`.** Claude Code 2.1.268 cannot serve `claude-opus-5-5`; the new
   probe now stops such a run in seconds.
4. **The working tree is clean** at that commit, or at a later one that did not touch `src/`.
5. **The plan's 5-hour window has room**; a run costs about $35 at API rates.
6. **The timeout.** The app passes `--timeout 5400` to `serve-local`, and `3dc02567` used all but
   8 seconds of it. The end-of-run re-run also needs time left, one minute per trial plus five.
   Raising it is the operator's setting.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `3dc02567`:

- `.verifier/runs/3dc02567-756f-4b76-9ae7-7de1d964b915`
- `.verifier/attempts/e8507224-d9b0-4e11-8abc-88a9e58c5411`
- `.verifier/subject-runs/3dc02567-756f-4b76-9ae7-7de1d964b915`
- the **twelve** candidates in `.verifier/candidates/` at `local-reference-comparison-5`

**Keep** the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs, and
the five candidates at `local-reference-comparison-1`. Leave `.verifier/store/` alone. Do not
leave a shell inside a directory you are moving.

### What to check in the run

`verify_skill` returns 190–350 KB, which overflows the tool result; read
`.verifier/runs/<run>/report-card.json` on disk.

1. **The new code ran.** The server's start time shows it. `controller-receipt.json` also carries
   `preflight.model_probe`, and a subject response carries `refusals`.
2. **Refusals.** Did any subject stream record `model_refusal_fallback`? If the switches work, a
   refusal shows only `model_refusal_no_fallback`. Quote the events.
3. **The re-run.** Did `write_report_card` re-run a stopped claim, did it fit in the time left,
   and what did it return? Read the claim's `retry`.
4. **Leaks.** Is `leaked` still most of the critiques' rejections (seven of eleven in `3dc02567`)?
5. **The prior-review refusal.** Any refusal left, and was it a real leak or a false positive?
6. **`invalid` is still zero**, and record the claim count (`3dc02567` extracted six) and the
   run time against the timeout.

### Reading the results without fooling yourself

- **Before calling any `fail` a finding about the skill, read the observed reply, the expected
  answer and the reference quote verbatim.**
- **A unanimous `none of these`** means a broken case far more often than a wrong subject.
- **`claim-00N` directories under `subject-runs/` do not follow the report's order**, and a
  re-run's trials sit in `claim-NNN-retry`. Map them by `case_id`.
- **`subject_refused` or `subject_model_changed`: read the trial's `system` events** in the
  workflow log (`model_refusal_*`) before advising anything. A refusal may or may not recur.
- **A run the runner closed should say `agent_unavailable`** with the planner's own reason; one
  that still says "The operator cancelled this run." for a stop nobody made means old code.
- **`workflow.jsonl` truncates long tool results** at about 16 KB; every tool call's whole
  request and result, including every critique round, is in `.verifier/runs/<run>/events/`.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct.
2. **Claim coverage.** `3dc02567` extracted six claims; `74eadedd` extracted three.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. Their case is semantic, but a subject could still
   lowercase one.
4. **Recognition is untouched.** The leak guidance is the first planner-side response; a choice
   can still be passed by spotting the conventional-looking option.
5. **Reviewers disagree on unchanged cases.** Spare cases absorbed two rejections in `3dc02567`;
   keep watching whether that is enough.
6. **A claim Opus 5 refuses cannot be verified on Opus 5.** If the re-run is refused too, the
   report says so, and that is the finding: a provider limitation, not the skill's.

Settled today: the preflight now asks the CLI whether it can serve the pinned model (formerly
open question 4), and the local section reader is held to the reply limit (formerly 6).

### Deferred, and why

- **Parallel trials** — the operator agreed it is a good design. It is not built: the sandbox is
  configured with one CPU, and parallel sessions spend the usage window faster, so both need a
  decision first. Running a case's three trials at once would cut about 29 minutes of trials to
  about 10.
- **Opus 5.5** — until WinGet offers Claude Code 2.1.280; the startup probe now catches a
  premature switch.
- **The case-level contract** — flagged do-not-implement until four or five case-type rules
  accumulate; `a202146`'s answer forms and case verdicts overlap it, unreviewed. Design in the
  archive, 2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-24"). Follow its preflight, clean the previous run as it
describes, and use scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\sar-analysis"

Show me the report and workflow-log paths, a table with one row per claim
(grade, accuracy, consistency, status and the other measurements) and, for each
claim, a table with one row per test. Tell me whether it is a good run, and
whether our fixes work: go through the entry's "What to check in the run" list
item by item. Before concluding anything from a `fail`, an `invalid`, a refusal
or a unanimous "none of these", quote the verbatim reply or event behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None now. Before the next live run, restart Claude Desktop so `serve-local` loads the commit
that carries these fixes, and consider raising the timeout.

### Suggested next move

Run `sar-analysis` once on the new code and read the refusal path, the end-of-run re-run and
the probe rather than the grades.

### Recommended next action

Restart Claude Desktop, confirm the server started after this commit, raise the timeout if
the operator agrees, clean `3dc02567` as above, and run once. It is finished when every item under "What to check in the
run" has a recorded answer.
