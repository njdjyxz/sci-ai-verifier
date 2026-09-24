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
| `84e90683` (2026-09-24) | sar-analysis | 1 at A, 1 at B, 1 at D with no trials, 1 voided by two timeouts; 27 of 27 counted trials passed |

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
documentary path has now run five times: once to completion, once rejected, once in
`b43780be` for a claim that should have executed first and could not, once in `b0955d2f`
after that claim's ungraded plan had executed first, as it now must, and once in `84e90683`
for a claim the planner never tried to execute, which the operator accepts: D is AI judgment
by design.

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
pinned model's. Run `84e90683` saw the end-of-run re-run and the model probe work live; no
refusal came up. It exposed a critique that counted a case its own objection placed outside
the claim, a claim that reported nothing after two timeouts, and a sandbox without RDKit.
Their fixes are **not yet seen live**; the 2026-09-24 entry below has the details.

Automated suite: **318 passed, 2 skipped, 1 failing on this machine only**. The failing
`test_runlog.py` preflight test fails the same way on the untouched `2d9f8af` tree: its
stale-directory sweep finds this machine's leftover `sci-verifier-*` directories in `%TEMP%`
and logs an event the test does not expect.
Fixtures remain synthetic, reviewed registries remain empty, and nothing in the automated
suite establishes scientific acceptance.

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

## Claude: 2026-09-24 (runs 3dc02567 and 84e90683; one model per trial, a re-run, a fallback D, an RDKit image)

### Current stage and status

Version 0.7.0, local workflow. Two sar-analysis runs today.

Run `3dc02567`, on `18ef2b9`, completed six claims: A, A, A, B and A, and one voided by a
refusal fallback; 95 of 95 scored trials passed. It led to commit `2d9f8af`: one model per
trial, one disclosed re-run at the end, a narrower prior-review trigger, the leak shapes in
the rubric, the 40 KiB limit on section and resource-preview replies, and a startup model
probe.

Run `84e90683`, on `2d9f8af`, completed four claims:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | B | 12 of 12 | four counting cases |
| `completeRingsOnly` / `ringMatchesRingOnly` | withheld | none | not obtained | `claude_timeout`, and again on the re-run |
| pIC50 | pass | A | 15 of 15 | one `duplicate` case not counted |
| dummy atoms / `makeDummiesQueries` | inconclusive | D | n/a | documentary, no trials |

It used 2,762 s of the 5,400 s limit, cost about $16, and had no `invalid` and no model
change. Of `2d9f8af`'s fixes, the probe worked (4.6 s), the re-run fired with time to spare
and repeated the timeout, and the section limit cut the planner's end-of-run report re-read.
No refusal occurred, so the one-model rule and the fallback switches are still unobserved;
the prior-review trigger never fired; `leaked` was two of the three rejections.

It exposed three problems:

1. **A critique counted cases its own objection placed outside the claim.** It wrote that "a
   subject applying the claim as worded answers 2 to both and fails", counted both cases, and
   all six trials of one of them failed. Had the claim finished it would have read A with
   status fail. Two of `3dc02567`'s critiques made the same contradiction.
2. **The ring-option claim reported nothing.** Both attempts stopped at the 120 s subject
   limit, and the report never named the limit.
3. **The sandbox had no RDKit.** Every ring-option trial first tried to import and install
   it. Two ran out of time working an MCS out by hand, and six worked one out wrongly. In the
   new image RDKit returns every expected answer.

This session's fixes, contracts first, are tested and pushed to `main` in the commit that
carries this entry, but **have not met a live run**:

1. **Fallback D.** A claim that a subject-trial fault still stops after the re-run gets a
   documentary assessment Python assembles from its cases' reference quotes, and the fault
   stays on the record. "Independent documentary path" in `local-contract.md` owns the rule.
2. **An honest timeout.** A `claude_timeout` names the case, the trial and the
   `subject_timeout_seconds` it reached, and says the limit is the verifier's.
3. **Critique rubric v6.** `beyond_scope` covers a key that a subject correctly applying the
   claim could miss, and `verdict_consistency` says objections and verdicts must agree.
4. **A fifth leak shape**: the correct option in the source's wording among options written
   fresh.
5. **The subject's command tool says nothing can be installed.**
6. **An RDKit image**, [images/rdkit/](images/rdkit/Dockerfile), pinned in
   `.verifier/local-settings.json`.

Operator decisions today: D stays pure AI judgment and needs no trials, so every claim gives
the reader something to refer to; a re-run claim's first attempt stays out of the report,
being the product of a runner fault; `subject_timeout_seconds` stays at 120 s until a large
skill needs more; RDKit belongs in the image.

Superseded today: "a safety refusal is never retried", replaced by the one disclosed re-run;
the reading of `subject_model_changed` as random fallback, which was a refusal fallback; my
recommendation that D follow an execution, declined; a stopped ungraded plan ending with
nothing, since it is still not re-run but now gets the fallback; the pinned image
`78387bc3…`, now `12771144…`; and checking the server's start time, replaced by the run's own
code digest below.

### What has been done

This session:

- Cleaned `3dc02567` into the session scratchpad and ran `84e90683`. Report
  `.verifier/runs/84e90683-1e8f-4712-bf32-a8754c0322e7/report-card.md`, workflow log
  `.verifier/attempts/74972df6-1d0d-46d6-b341-05fd8f918e70/workflow.md`. Cost: planner
  $10.74, 36 subject sessions $4.21, four critiques $0.96, assessor $0.14; the two timed-out
  sessions are unpriced.
- Checked the failure against its source. RDKit's own `test4RingMatches` asserts 3 atoms for
  `completeRingsOnly=True` on `CCCCC` and `CCC1CCCCC1`, so the key was right and the
  subject's `2` wrong. The timed-out trials ran `import rdkit` and `pip install rdkit`, then
  thought until they were killed.
- Implemented the six fixes in `local-contract.md`, `tool-contracts.md`,
  `artifact-contracts.md`, `evidence-rubric.md`, `LOCAL-CONFIG.md`, `local.py`,
  `documentary.py`, `subject_server.py` and `images/rdkit/`.
- Verification: suite 315 → 319 tests, with 318 passing, 2 skipped and the one machine-only
  failure under "Current state". Twelve one-line mutations of the fixes were each caught.
  `test_recorded_replies.py` rebuilds v5 from v6 and pins its digest, `bf944269…`. The image
  was checked through the verifier's own `DockerSandbox` and subject tool, as user 65534
  with no network. RDKit 2026.03.6 and pandas 3.0.6 import, the six ring-option questions
  return 3, 2, 3, 2, 3 and 5 as RDKit's tests assert, and an ACS1996 SVG draws.
- Not verified: any of the six fixes live, and still the effect of
  `CLAUDE_CODE_NO_MODEL_FALLBACK` and `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK`.
- Considered and not done: requiring execution before D (declined); a Python check that
  objections agree with verdicts, since 26 of the two runs' 92 objections and revisions name
  a counted case legitimately; reporting the first attempt's answers (declined); a longer
  subject limit (deferred by the operator).

Earlier today, in the `3dc02567` session: `2d9f8af`'s six fixes, with the suite 301 → 315,
seventeen mutations caught and two new recordings replayed through the real subject adapter.
That run took 90 minutes, 8 s inside the limit.

### Before the next run

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:127711447fe5260556ae724850ef4186a79ea774ec119ebb01c3775240f5264e`
   (`sci-verifier-rdkit:2026.3.6`, built from `images/rdkit/` as `LOCAL-CONFIG.md` says).
2. **A new Code-tab session after the commit that carries these fixes.** Every session, new
   or resumed, starts its own `serve-local`, and a resumed one keeps the code it started
   with; restarting the app is not needed. After the run, the run itself settles it:
   `run.json`'s `local_method_ref` must equal the tree's digest, printed by
   `python -c "import sys; sys.path.insert(0, 'src'); from sci_ai_verifier.storage import implementation_bytes; from sci_ai_verifier.common import digest; print(digest(implementation_bytes()))"`.
3. **The model is `claude-opus-5`.** The probe stops a run the CLI cannot serve.
4. **The working tree is clean** at that commit, or at a later one that did not touch `src/`.
5. **The plan's 5-hour window has room**; `84e90683` cost about $16 and `3dc02567` about $35.
6. **The timeout.** The app passes 5,400 s; four claims took 46 minutes and six took 90. A
   fallback needs up to nine minutes of the time left.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `84e90683`:

- `.verifier/runs/84e90683-1e8f-4712-bf32-a8754c0322e7`
- `.verifier/attempts/74972df6-1d0d-46d6-b341-05fd8f918e70`
- `.verifier/subject-runs/84e90683-1e8f-4712-bf32-a8754c0322e7`
- the **seven** candidates in `.verifier/candidates/` at `local-reference-comparison-5`

**Keep** the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs, and
the five candidates at `local-reference-comparison-1`. Leave `.verifier/store/` alone. Do not
leave a shell inside a directory you are moving.

### What to check in the run

`verify_skill` returns 150–350 KB, which overflows the tool result; read
`.verifier/runs/<run>/report-card.json` on disk.

1. **The new code ran.** `run.json`'s `local_method_ref` matches the tree, and every
   critique's `rubric_ref` is v6,
   `9dc8fd5d3510504e4bf49ee3b06600eb2e2cf0315df8c474f695a4dbca2864f9`.
2. **RDKit.** Do the subjects' commands import it? Do cases like the ring-option ones pass
   now? Any `claude_timeout`, and what was the subject doing? Quote the events.
3. **The fallback.** Did any claim carry `fallback`? Its status and reason, and the record's
   first limitation line.
4. **Critique v6.** Did any critique still count a case its own objection placed outside the
   claim? Quote every `beyond_scope` verdict.
5. **Leaks.** Are each case's options written in one style? The `leaked` count.
6. **The rest.** Any refusal (quote the `model_refusal_*` events), `invalid` still zero, the
   claim count and the run time.

### Reading the results without fooling yourself

- **Before calling any `fail` a finding about the skill, read the observed reply, the expected
  answer and the reference quote verbatim.**
- **A unanimous `none of these`** means a broken case far more often than a wrong subject.
- **`claim-00N` directories under `subject-runs/` do not follow the report's order**, and a
  re-run's trials sit in `claim-NNN-retry`. Map them by `case_id`.
- **`subject_refused` or `subject_model_changed`: read the trial's `system` events** in the
  workflow log (`model_refusal_*`) before advising anything. A refusal may or may not recur.
- **A `claude_timeout` can come from the case itself.** Trace the subject's commands and
  thinking before promising that a re-run or a longer limit fixes it.
- **A run the runner closed should say `agent_unavailable`** with the planner's own reason; one
  that still says "The operator cancelled this run." for a stop nobody made means old code.
- **`workflow.jsonl` truncates long tool results** at about 16 KB; every tool call's whole
  request and result, including every critique round, is in `.verifier/runs/<run>/events/`.
- **With RDKit in the image, a subject can compute an answer instead of recalling it.** A pass
  then says the skill-guided subject ran RDKit correctly, a different statement from knowing it.
- **A fallback D rests on its cases' quotes alone.** Read it as documentary, never as behaviour.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct.
2. **Claim coverage.** `3dc02567` extracted six claims, `84e90683` four and `74eadedd` three.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. Their case is semantic, but a subject could still
   lowercase one.
4. **Recognition.** The fifth leak shape covers one tell; a subject can still pick the
   conventional-looking option.
5. **Reviewers disagree on unchanged cases.** Spare cases absorbed two rejections in `3dc02567`;
   keep watching whether that is enough.
6. **A claim Opus 5 refuses cannot be verified on Opus 5.** If the re-run is refused too, the
   report says so, and that is the finding: a provider limitation, not the skill's.
7. **Other operational endings.** Only subject-trial faults get a fallback D; a claim ended by
   `critic_unavailable` or by the planner still reports nothing. Should they get one?
8. **Knowledge or execution.** With RDKit available, should some cases stay questions a
   subject must answer without running code?

### Deferred, and why

- **Parallel trials** — the operator agreed it is a good design. It is not built: the sandbox is
  configured with one CPU, and parallel sessions spend the usage window faster, so both need a
  decision first. Running a case's three trials at once would cut about 29 minutes of trials to
  about 10.
- **Opus 5.5** — until WinGet offers Claude Code 2.1.280; the startup probe now catches a
  premature switch.
- **A longer subject limit** — the operator will raise `subject_timeout_seconds` when a large
  skill needs it; the report now names the limit whenever it stops a trial.
- **The case-level contract** — flagged do-not-implement until four or five case-type rules
  accumulate; `a202146`'s answer forms and case verdicts overlap it, unreviewed. Design in the
  archive, 2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18. `images/rdkit/` is the manual path it would automate.

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

None now. Before the next live run, start a new session so `serve-local` loads the commit that
carries these fixes.

### Suggested next move

Run `sar-analysis` once on the new code and image, and read the RDKit path, any fallback and
the critique's verdicts rather than the grades.

### Recommended next action

Start a new session, clean `84e90683` as above, and run once. It is finished when every item
under "What to check in the run" has a recorded answer.
