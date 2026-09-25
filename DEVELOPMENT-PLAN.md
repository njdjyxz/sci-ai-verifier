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
| `31b67427` (2026-09-24) | sar-analysis | 1 at A, 2 at B; 42 of 42 trials passed, 0 invalid, 0 faults |
| `3b3f3c94` (2026-09-24) | sar-analysis | 1 at A, 2 at B, 1 at C with status fail; 44 of 45 counted trials passed, 0 invalid, 0 faults |
| `d416f79d` (2026-09-24) | sar-analysis | 4 at B; 39 of 39 counted trials passed, 0 invalid, 0 faults |

Four more sar-analysis runs on 2026-09-23 (`28d19f8a`, `d87a6d5c`, `0a243b7e`, `74eadedd`) are
described only in the messages of commits `a202146` and `041552c`. Run `7f88fbef` stopped on
the subscription session limit.

Every run above used Opus 5, and the verifier is still pinned to it. A move to
`claude-opus-5-5` was made and reverted the same day: the installed Claude Code, 2.1.268,
cannot serve that model, which needs 2.1.280, and WinGet does not yet offer 2.1.280.

What that does and does not establish: the **A and B branches** both carry settled grades
from live runs, and the planner has now used all three comparison methods, including an
open `exact` case written specifically to make the subject generate an answer rather than
recognise one. **Grade C has settled once**, in `3b3f3c94`, on the case profile alone (three
counting cases, none open) rather than on indirect evidence, **and `qualify_local_evaluator`
has never been exercised.** The documentary path has now run five times: once to completion, once rejected,
once in `b43780be` for a claim that should have executed first and could not, once in `b0955d2f`
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
Run `31b67427` then saw the RDKit image work and critique v6 in force, but nothing stopped a
trial, so the fallback D and the timeout message are **still unobserved**, and a case with
the fifth leak shape was counted. Run `3b3f3c94`, on the same code, saw `beyond_scope` catch a
mis-keyed case before any trial ran, but a counted case whose key was finer than its claim
produced the ring claim's `fail`. Seven fixes for what those two runs showed, among them
critique rubric v7 and claim-only answers that Python measures, then met run `d416f79d`,
which settled all four claims at B. The claim-only answers kept a case finer than its claim
out of a design before any trial ran; neither new qualification check fired, and the fallback
D and the timeout message are **still unobserved**. That run exposed two defects in the
verifier's own plumbing: a workflow log slow enough to lose two finished claim-only answers,
and reused answers filed under a case's old ID. Both are fixed and **not yet seen live**. The
2026-09-24 entry is in the archive; the 2026-09-25 entry below has the details.

Automated suite: **338 passed, 2 skipped, 1 failing on this machine only**. The failing
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
- **Claude 2026-09-24** — Runs `3dc02567` (six claims, one voided by a refusal fallback),
  `84e90683`, `31b67427` and `3b3f3c94`, the last with the first settled C and a `fail` that
  measured its case rather than the skill. One model per trial, a disclosed end-of-run re-run,
  a startup model probe, a fallback D, an honest timeout message, an RDKit sandbox image,
  critique rubric v7 with the leak shapes, two leak checks at qualification, the case gap in
  revision replies, and claim-only answers measured by Python.

## Claude: 2026-09-25 (run d416f79d; a log that keeps up with its readers, reused answers under their case's ID)

### Current stage and status

Version 0.7.0, local workflow. Run `d416f79d`, on `da7605b`, ran from 22:58 to 23:50 PDT on
2026-09-24 and completed four claims, all passing at B:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | B | 12 of 12 | four counting cases, two open |
| `completeRingsOnly` / `ringMatchesRingOnly` | pass | B | 9 of 9 | round 1 lost `ring-atom-count` to the claim-only answers; one `duplicate` |
| pIC50 | pass | B | 9 of 9 | three counting cases, one open |
| dummy atoms / `makeDummiesQueries` | pass | B | 9 of 9 | one `leaked`; one case `unmeasured` |

It used 3,096 s of the 5,400 s limit and cost about $18.90: planner $12.21, 45 subject
sessions $4.69, six critiques $1.56 and 40 claim-only sessions $0.42. All 39 counted trials
passed, with no `invalid`, fault, refusal, timeout, fallback, re-run or model change. It is the
first full run of the 2026-09-24 fixes, and the claim-only answers did what they were built
for: both answers to the ring claim's `ring-atom-count` gave `2` against RDKit's `3`, the split
behind `84e90683`'s failure, and the case left the design before any trial ran.

It exposed two defects in the verifier, fixed in this session with contracts first. Neither
changed a counted case or a grade. **The fixes are tested and pushed to `main` in the commit
that carries this entry, but have not met a live run.**

1. **The workflow log starved its pipe readers.** Every write re-read and re-verified every
   earlier event file, and the path check behind each read lstat'ed every parent directory. A
   write took about 0.09 s around the 350th event and 0.94 s by the 2,100th. The readers logged
   as they read, so with four claim-only sessions sharing the lock a reader fell more than the
   5 s drain grace behind its exited process. Two finished claim-only sessions were read as
   `claude_incomplete`, leaving two cases `unmeasured`. Four more kept their answers but lost
   their last lines from `workflow.jsonl`: `StreamLog.close()`, called on another thread,
   flushed the unread remainder as one unparseable line. The gap between a trial's wall time and
   the CLI's own time grew from 2.0 s in claim 1 to 6.1 s in claim 4. Now the readers only read,
   the thread waiting for the process logs its stream and returns exactly what it logged, and a
   write reads back only event files it has not verified or whose size or modification time
   changed. `local-contract.md` "Acceptance" owns the rule.
2. **Reused claim-only answers kept an earlier round's case ID.** The planner renamed
   `ring-which-argument` to `ring-prevent-argument` without changing it, and its reused answers
   were reported under the old name. Counting matches misses by ID, so a renamed miss would still
   have counted. The answers now carry the current ID. `select_local_candidate` in
   `tool-contracts.md` owns the rule.

Why neither touched the result: a slow reader loses only the end of a session's output, and an
answer is recorded only once the final `result` line has arrived, so nothing partial was scored.
All 45 subject sessions, the six critiques and the planner have complete logs. The two lost
answers belonged to cases the critique had ruled `leaked`, and a claim-only answer can only drop
a case from the count. The renamed case asks the same question, with the same input, key and
method, and its answers were `reached`; only a `missed` answer affects counting.

### What has been done

In the session of run `d416f79d`, started at 22:55 PDT on 2026-09-24 after `da7605b`:

- Preflight as the 2026-09-24 entry lists it: Docker 29.8.0 with the pinned image; this
  session's own `serve-local` started six minutes after `da7605b`; `claude-opus-5`; a clean
  tree; 27 % of the five-hour window used.
- Cleaned `3b3f3c94` into the session scratchpad: 2,458 files, counts and bytes matched.
- Ran `d416f79d`. Report `.verifier/runs/d416f79d-dbf4-4c0b-a5e1-69f53c5772c8/report-card.md`,
  workflow log `.verifier/attempts/2275addb-174d-4ac5-9db8-325bf15593bb/workflow.md`.
- Checked it against "What to check in the run"; the answers are below.
- Traced both defects to the code and measured the log on a copy of the run's 2,430 events: a
  write took 2.34 s there, of which 2.00 s path checks, 0.23 s reads, 0.06 s rewriting the two
  timelines and 0.04 s parsing and digests.
- Fixed both in `local-contract.md`, `tool-contracts.md`, `claude_runner.py`, `runlog.py` and
  `documentary.py`. Verification: suite 337 → 341 tests, with 338 passing, 2 skipped and the
  machine-only failure under "Current state". Three of the four new tests fail on `da7605b`'s
  code: a slow observer loses a finished process's output and runs on the reader thread; a write
  re-reads every file; a reused answer keeps the old ID and its miss counts. The fourth, a
  changed event still detected, guards the new cache; the old code passed it by reading
  everything. Six one-line mutations of
  the fixes were each caught. Each test run compiled into its own bytecode cache: a same-size
  mutation restored within the same second had left a `.pyc` that still looked current.
- On the same copy the fixed log writes in 0.034 s. A process opening a 2,430-event log for the
  first time verifies it once, in 2.5 s.
- Not verified: either fix live. The two timelines are still rewritten whole on every write,
  0.06 s at 2,430 events.

Against "What to check in the run" of the 2026-09-24 entry:

1. **The new code ran.** `local_method_ref` matched the tree's `98882e6b…`, all six critiques
   carried v7's `58b2509c…`, and all six candidates were at `local-reference-comparison-6`.
2. **RDKit.** No subject ran it, or any command: all 45 trials used only the Skill tool, in
   three turns each. No `claude_timeout`.
3. **The fallback.** Not exercised; nothing stopped a claim.
4. **Critique v7.** One `beyond_scope`, the ring claim's first-round `ring-atom-count`, which
   the claim-only answers also missed. No critique counted a case its own objection placed
   outside the claim: every objection to a counted case questioned its strength. No counted
   case failed a trial.
5. **Leaks.** No qualification was refused, so the leading-word and repeated-word checks cost
   no rewrite and did not fire. Two `leaked` verdicts, both claim 4's. One counted key stands
   alone among its options: `thr-proportion-of-what`'s "the dataset" is the only option naming
   the molecule set. Its critique objected to exactly that and counted it; claim 4's critique
   ruled the same shape `leaked`.
6. **Grades.** Two `case_gap` replies. The ring claim's first round: "This design has 1 counted
   case, 1 generated: add at least 2 more counting cases of either form. The critique's own
   grade is none, so its objections need answering as well." The dummy claim's: "This design
   has 2 counted cases, 1 generated: add at least 1 more counting case of either form." Both
   times the planner replaced the rejected cases and the next critique supported B. It never
   accepted a grade below its proposal. It proposed B for all four claims, and each
   `stronger_grade_considered` names why no further independent case with a quotable key
   existed. The dummy claim's critique did not accept that reason: "rdkit.Chem.rdmolops
   documents AdjustQueryProperties as a module function on the same page", so a second
   generated case "appears to have been available"; with four counting cases it would still
   have been B.
7. **Effect-to-setting cases.** Three designed, all counted: `thr-which-property`,
   `ring-prevent-argument` and `dummy-which-field`.
8. **Claim-only answers.** One miss, `ring-atom-count`, answered `2` twice against the key `3`
   that RDKit's test asserts: a scope problem, not a slip. One reply: "The claim, applied
   literally, bars any partial-ring fragment from the MCS. … any single ring carbon would be a
   partial-ring fragment". Two `unmeasured`, both from the log defect. 40 sessions, $0.42 for
   the 38 that returned, about 2.3 minutes over six rounds; six answers reused.
9. **The rest.** No `model_refusal_*` event, `invalid` zero, four claims, 3,096 s.

### Before the next run

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:127711447fe5260556ae724850ef4186a79ea774ec119ebb01c3775240f5264e`
   (`sci-verifier-rdkit:2026.3.6`, built from `images/rdkit/` as `LOCAL-CONFIG.md` says).
2. **A new Code-tab session after the commit that carries these fixes.** Every session, new or
   resumed, starts its own `serve-local`, and a resumed one keeps the code it started with.
   After the run, `run.json`'s `local_method_ref` must equal the tree's digest, printed by
   `python -c "import sys; sys.path.insert(0, 'src'); from sci_ai_verifier.storage import implementation_bytes; from sci_ai_verifier.common import digest; print(digest(implementation_bytes()))"`.
3. **The model is `claude-opus-5`.** The probe stops a run the CLI cannot serve.
4. **The working tree is clean** at that commit, or at a later one that did not touch `src/`.
5. **The plan's 5-hour window has room**; `d416f79d` cost about $19, `3dc02567` $35.
6. **The timeout.** The app passes 5,400 s; three claims took 40 minutes, four took 43 to 52 and
   six took 90. The log fix removes most of the late-run overhead; by how much is unmeasured.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `d416f79d`:

- `.verifier/runs/d416f79d-dbf4-4c0b-a5e1-69f53c5772c8`
- `.verifier/attempts/2275addb-174d-4ac5-9db8-325bf15593bb`
- `.verifier/subject-runs/d416f79d-dbf4-4c0b-a5e1-69f53c5772c8`
- the **six** candidates in `.verifier/candidates/` at `local-reference-comparison-6`, all
  qualified

**Keep** the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs, and
the five candidates at `local-reference-comparison-1`. Leave `.verifier/store/` alone. Do not
leave a shell inside a directory you are moving.

### What to check in the run

`verify_skill` returns 150–350 KB, which overflows the tool result; read
`.verifier/runs/<run>/report-card.json` on disk.

1. **The new code ran.** `run.json`'s `local_method_ref` matches the tree, every critique's
   `rubric_ref` is v7, `58b2509c3e8799cf55cf60033edcb7e2d550d4ce8821295cb4daeddbeaba7aa9`, and
   every candidate is at `local-reference-comparison-6`.
2. **The log keeps up.** Every subject, critique and claim-only session has its `result` event
   in `workflow.jsonl`; no `process_unparsed_output`; no claim-only sample `claude_incomplete`.
   Late in the run, the gap between a trial's wall time and the CLI's `duration_ms` should stay
   near claim 1's 2 s, not reach `d416f79d`'s 6 s.
3. **Reused answers.** A claim-only case reused under a new name shows its current ID.
4. **Claim-only answers.** Quote every `missed` case with its answers and key, and say whether it
   was a scope problem or a slip, from the full reply in `workflow.jsonl` (role `claim_probe`).
   Any `unmeasured` case, and why. Cost, minutes and reused answers.
5. **Critique v7 and leaks.** Quote every `beyond_scope` verdict. Did any critique count a case
   its own objection placed outside the claim? Quote every qualification refused for a leak
   and count the rewrites; both checks have yet to fire live. The `leaked` count.
6. **Grades.** Quote every `case_gap` summary and what the planner did next. Did it accept a
   settled grade below its proposal while a replacement round remained? For each grade below
   A, did the critique accept the planner's `stronger_grade_considered`?
7. **RDKit and timeouts.** Which subjects ran commands, and did they compute or look up? Any
   `claude_timeout`, with the subject's events quoted.
8. **The fallback.** Did any claim carry `fallback`? Its status and reason.
9. **The rest.** Any refusal (quote the `model_refusal_*` events), `invalid` still zero, the
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
- **A `claude_incomplete` from a session that exited 0** was the log starving its reader until
  this fix. On the fixed code, it means this diagnosis was incomplete.
- **Trial wall times before this fix include log overhead** that grew through a run. Compare
  runs with the CLI's own `duration_ms`.
- **A run the runner closed should say `agent_unavailable`** with the planner's own reason; one
  that still says "The operator cancelled this run." for a stop nobody made means old code.
- **`workflow.jsonl` truncates long tool results** at about 16 KB; every tool call's whole
  request and result, including every critique round, is in `.verifier/runs/<run>/events/`.
- **With RDKit in the image, a subject can compute an answer instead of recalling it, or look it
  up.** In `31b67427` two trials printed a docstring that was their case's key word for word.
- **A counted case can still turn on a finer fact than its claim.** Compare a failing reply with
  the claim's wording before calling it a finding.
- **A fallback D rests on its cases' quotes alone.** Read it as documentary, never as behaviour.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct.
2. **Claim coverage.** `3dc02567` extracted six claims, `84e90683`, `3b3f3c94` and `d416f79d`
   four, and `74eadedd` and `31b67427` three.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. It now costs evidence: `d416f79d`'s threshold planner
   named it as the reason `Threshold` could not be a fifth, open case.
4. **Recognition.** The fifth leak shape covers one tell; a subject can still pick the
   conventional-looking option. `thr-proportion-of-what` counted although its critique wrote
   that the key could be reached "on general plausibility".
5. **Reviewers and planners disagree across runs.** In `d416f79d` one critique counted a key that
   alone names what the stem is about and another ruled that shape `leaked`. The threshold and
   pIC50 claims settled at B after reaching A in earlier runs.
6. **A claim Opus 5 refuses cannot be verified on Opus 5.** If the re-run is refused too, the
   report says so, and that is the finding: a provider limitation, not the skill's.
7. **Other operational endings.** Only subject-trial faults get a fallback D; a claim ended by
   `critic_unavailable` or by the planner still reports nothing. Should they get one?
8. **Knowledge or execution.** With RDKit available, should some cases stay questions a subject
   must answer without running code? In `d416f79d` every B rested on sources that quote only
   three or four independent facts, and the ring planner wrote that "Executing RDKit to measure
   a fresh consequence is not available to this verifier for this claim".
   `qualify_local_evaluator` has never run. Is an executed key the route to A for narrow API
   claims?
9. **Accepting a lower grade.** In `31b67427` the planner accepted B one counting case short of
   A with a replacement round unused. Neither later run repeated it. Not changed; the revision
   reply states the case gap instead.
10. **How strict qualification should be.** Its two leak checks would have refused 11 of the 30
    choice cases before them, yet refused none of `d416f79d`'s designs. If rewrites start to
    cost more than the leaks did, should the repeated-word check drop to a warning?
11. **The prior-review trigger.** It refused a first proposal in `3b3f3c94` for a sentence about
    the coming review, and did not fire in `d416f79d`. Should it match only references to an
    earlier review?
12. **How many claim-only answers per case.** Two answers caught `d416f79d`'s one miss, which both
    answers made. A case missed in one answer of four, as `3b3f3c94`'s lone-ring case was, slips
    past two answers about half the time; a third answer cost about $0.01 a case in `d416f79d`.
    Should it be three?

### Deferred, and why

- **Parallel trials** — the operator agreed it is a good design. It is not built: the sandbox is
  configured with one CPU, and parallel sessions spend the usage window faster, so both need a
  decision first.
- **Appending to the timelines** instead of rewriting them on every write — 0.06 s per write at
  2,430 events. Rewriting keeps each projection rebuilt from verified events.
- **Opus 5.5** — until WinGet offers Claude Code 2.1.280; the startup probe catches a premature
  switch.
- **A longer subject limit** — the operator will raise `subject_timeout_seconds` when a large
  skill needs it; the report names the limit whenever it stops a trial.
- **The case-level contract** — flagged do-not-implement until four or five case-type rules
  accumulate. Design in the archive, 2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18. `images/rdkit/` is the manual path it would automate.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-25"). Follow its preflight, clean the previous run as it
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

None for the code, which is committed and pushed with this entry. Before the next live run,
start a new session: a session started before this commit runs a `serve-local` with older code.

### Suggested next move

Run `sar-analysis` once on the fixed code and read the log's completeness and timing, and any
claim-only answers reused under a new name, before the grades. Separately, decide open question
8: whether an executed key is the route to A for narrow API claims.

### Recommended next action

In a new session after the commit, clean `d416f79d` as above and run once. It is finished when
every item under "What to check in the run" has a recorded answer.
