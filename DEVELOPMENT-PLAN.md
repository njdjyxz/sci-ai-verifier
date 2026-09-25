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
produced the ring claim's `fail`. Six fixes for what those two runs showed, among them
critique rubric v7, are tested but **not yet seen live**. Replaying saved critique packets on
the pinned model showed that the rubric text alone did not make it catch the article tell;
the new qualification checks catch that tell and the repeated word behind the ring `fail`. The 2026-09-24 entry below has the details.

Automated suite: **324 passed, 2 skipped, 1 failing on this machine only**. The failing
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

## Claude: 2026-09-24 (runs 3dc02567, 84e90683, 31b67427 and 3b3f3c94; one model per trial, a re-run, a fallback D, an RDKit image, critique rubric v7)

### Current stage and status

Version 0.7.0, local workflow. Four sar-analysis runs today.

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

The `84e90683` session's fixes, contracts first, are tested and pushed to `main` in
`d8a71f6`. Their first live run is `31b67427`, below:

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

Run `31b67427`, on `d8a71f6` with the RDKit image, completed three claims:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | A | 15 of 15 | five counting cases, two open |
| `completeRingsOnly` / `ringMatchesRingOnly` | pass | B | 12 of 12 | one `leaked`; B accepted with a replacement round unused |
| dummy atoms / `makeDummiesQueries` | pass | B | 9 of 9 | one `duplicate`; three counting cases, one open |

It used 2,383 s of the 5,400 s limit, cost about $17, and passed 42 of 42 trials with no
`invalid`, fault, refusal or model change. Against the six fixes:

- **The RDKit image works.** `import rdkit` printed `2026.03.6`. Five trials ran seven
  commands; all succeeded in under a second and none tried to install anything. The longest
  subject session took 33 s. No ring trial ran a command, so `84e90683`'s failing ring cases
  were not retried.
- **Critique v6 was in force but not tested.** All four critiques carry its digest. None gave
  `beyond_scope`, every objection to a counted case questioned only its strength, and no
  counted case failed.
- **The fallback D and the timeout message were not exercised**: nothing stopped a trial.
- **The fifth leak shape was missed once.** In `which-object-is-the-query` the key, quoted from
  MolOps.h, was "a copy of a molecule with query properties adjusted", and the three other
  options began with "the", the tell of `84e90683`. The critique counted it, and the claim's B
  rests on it: without it two cases count, which allows no execution grade.
- **The no-install wording was not tested**, since nothing needed installing.

Two more findings. With RDKit present a subject can look an answer up: two of three trials of
a documented-phrase case printed `rdFMCS.MCSParameters.Threshold.__doc__`, which is the key
word for word. And the planner accepted B for the ring claim because "no second independent
open case is available from documentation alone", though that design already had two open
cases and A needed only one more counting case of either form.

Run `3b3f3c94` repeated the skill on the same code and completed four claims:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | B | 9 of 9 | one open case; one `duplicate` |
| `completeRingsOnly` / `ringMatchesRingOnly` | fail | C | 8 of 9, split | no open case; one `duplicate`, one `beyond_scope` |
| dummy atoms / `makeDummiesQueries` | pass | B | 12 of 12 | one open case; one `duplicate` |
| pIC50 | pass | A | 15 of 15 | redesigned after its first critique found a mis-keyed case |

It used 2,606 s and cost about $19, with no `invalid`, fault, refusal, timeout or model change.
Against `31b67427`:

- **`beyond_scope` worked twice.** Before any trial, the first pIC50 critique found that "30 nM
  is 3e-8 M and -log10(3e-8) = 7.522879, not 7.5", a key a correct subject would miss at the
  1e-6 tolerance; the planner rebuilt the design and the second critique supported A. A
  tutorial's "more intuitive representation of the scaffold" was ruled outside the ring claim.
- **A counted case finer than its claim gave the run's only `fail`.** `ring-no-lone-ring-atoms`
  keyed on RDKit's atom-level docstring "results cannot include lone ring atoms", which the
  planner itself called "a different exclusion from the bond-level partial-ring restriction".
  The failing trial answered `5`, "none of these": "`completeRingsOnly` excludes **partial
  rings** from the MCS … option 4's "lone ring atoms" describes only one narrow case". One
  passing trial had printed that docstring. The `fail` measures the case, not the skill.
- **No `leaked` verdict and no article tell.** The critiques rejected five `duplicate`s and two
  `beyond_scope`s. Three counted keys still carry a trace of their source, unflagged: the only
  option repeating the stem's "threshold", the only "log" among "logarithm"s, and an
  "actually".
- **Weaker designs for two claims.** For the ring claim the planner judged a
  symptom-to-option-name `exact` case recitation, the kind `31b67427` counted, so no open case
  was left and C was the ceiling; the threshold design had one open case, not two. On the same
  code the same claims settled A then B, and B then C.
- **The prior-review refusal fired falsely once**, on "a reviewer may judge one of each pair to
  add little independent evidence", a sentence about the coming review. No session was spent.
- **Subjects ran 14 commands**: ten pIC50 logarithms, three `AdjustQueryProperties`
  experiments and that one docstring lookup. The fallback D and the timeout message are still
  unexercised.

The same session then made six fixes for those findings, contracts first. They are tested
but **have not met a live run**:

1. **The critique gets the leak shapes.** Its rubric, now v7, lists the five shapes of "Common
   leaks" in `evidence-rubric.md`. Until now only the planner received them, which is how
   `31b67427`'s critique counted the article tell.
2. **Qualification refuses the article tell.** A correct option whose first word or
   capitalisation alone differs from every other option's is rejected, as
   `local-reference-comparison-6`. Over the saved choice cases of `84e90683`, `31b67427` and
   `3b3f3c94` it flags the three known tells and none of the other 27.
3. **A claim-only answer tests `beyond_scope`.** Before counting a case the critique answers
   it from the claim alone; if another option, `none of these` included, is as defensible as
   the key, the case does not count. `ring-no-lone-ring-atoms` is the worked example.
4. **An effect-to-setting case is not naming.** Asking which setting produces a described
   effect tests what the setting does; a name that hints at the effect bears on strength only.
5. **The revision reply states the case gap.** `case_gap` gives the counting and generated
   cases the proposal needs, has and lacks, and names the critique's own grade when that
   limits the settled grade too.
6. **Qualification refuses a lone repeated word**, added after the replay below at the
   operator's request. A correct option that alone repeats a content word of the question is
   rejected, in the same `-6`. Over the same 30 saved choice cases it flags nine keys, six of
   which critiques had counted, `ring-no-lone-ring-atoms` among them. With the leading-word
   check, 11 of the 30 would have been refused at qualification, so expect more rewrites; a
   refusal costs a planner turn, never a session.

Not done, and why: making acceptance wait until the replacement rounds are spent (open
question 9), because acceptance is right when an objection concerns the oracle rather than
the count; and narrowing the prior-review trigger (open question 11), because its false
positive costs one planner turn while a false negative would carry a grade to the critique.

Operator decisions today: D stays pure AI judgment and needs no trials, so every claim gives
the reader something to refer to; a re-run claim's first attempt stays out of the report,
being the product of a runner fault; `subject_timeout_seconds` stays at 120 s until a large
skill needs more; RDKit belongs in the image; an effect-to-setting case counts, as this
session recommended.

Superseded today: "a safety refusal is never retried", replaced by the one disclosed re-run;
the reading of `subject_model_changed` as random fallback, which was a refusal fallback; my
recommendation that D follow an execution, declined; a stopped ungraded plan ending with
nothing, since it is still not re-run but now gets the fallback; the pinned image
`78387bc3…`, now `12771144…`; checking the server's start time, replaced by the run's own
code digest below; critique rubric v6, now v7; and the fifth leak shape as planner guidance
only, now also in the critique's rubric and, in part, a qualification check.

### What has been done

In the session of runs `31b67427` and `3b3f3c94`, started after `d8a71f6`:

- Cleaned `84e90683` into the session scratchpad and ran `31b67427`. Report
  `.verifier/runs/31b67427-6db9-4e0e-ac8b-ae15aba4b21c/report-card.md`, workflow log
  `.verifier/attempts/6f0bb1b2-cfa7-4ac1-8d81-80853d68baa0/workflow.md`. Cost: planner
  $11.08, 42 subject sessions $4.80, four critiques $0.91.
- Cleaned `31b67427` the same way and ran `3b3f3c94` on unchanged code. Report
  `.verifier/runs/3b3f3c94-6892-4de7-a09e-a37f2092ef00/report-card.md`, workflow log
  `.verifier/attempts/7deed1ed-05b8-46d3-b919-0b22c1035c31/workflow.md`. Cost: planner
  $11.00, 60 subject sessions $6.60, five critiques $1.10.
- Checked both item by item against "What to check in the run"; the results are above.
- Implemented the six fixes in `evidence-rubric.md`, `tool-contracts.md`, `documentary.py`,
  `local_candidates.py`, `local_science.py` and `local.py`. Verification: suite 321 → 327 tests,
  with 324 passing, 2 skipped and the machine-only failure under "Current state". Seventeen
  one-line mutations of the fixes were each caught, with the tests run from `tests/` as
  discovery runs them. A first count of twelve had named the integration tests in a way that
  cannot import them, so it proved nothing and was redone. `test_recorded_replies.py` rebuilds
  v6 from v7 and pins its digest, `9dc8fd5d…`.
- Replayed saved critique packets through `critique()` on `claude-opus-5`: nine sessions, $2.39,
  the token passed as the MCP registration passes it, `CLAUDE_CODE_OAUTH_TOKEN` from
  `SCI_VERIFIER_OAUTH_TOKEN`. The replay script is in the session scratchpad.
  - `which-object-is-the-query` still counted under v7, in two samples of two, and neither
    reply mentioned the article tell. The rubric text did not carry the fifth shape to this
    model; qualification's check (fix 2) is what now stops that case.
  - `ring-no-lone-ring-atoms` counted in no fresh sample, v7 or v6: all three called it
    `leaked`, as the only option mentioning rings. The original count was one reviewer's miss,
    and none gave the claim-only test as the reason.
  - v7 newly called `application-reason-retain-rings` leaked, its key the only option echoing
    the stem's "application-side"; the original v6 critique counted it.
  - The effect-to-setting cases still counted, "so it is not mere naming". The pIC50 control
    kept A with every verdict unchanged. The threshold control fell from A to B:
    `molecules-left-out-below-one` became a duplicate, the objection its v6 critique had
    already raised while counting it.
- Earlier, a blind subagent proxy on a different model had caught the article tell that the
  pinned model then missed. A proxy on another model does not predict the pinned one.

In the `84e90683` session:

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
5. **The plan's 5-hour window has room**; `3b3f3c94` cost about $19, `31b67427` $17,
   `84e90683` $16 and `3dc02567` $35.
6. **The timeout.** The app passes 5,400 s; three claims took 40 minutes, four took 43 to 46 and
   six took 90. A fallback needs up to nine minutes of the time left.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `3b3f3c94`:

- `.verifier/runs/3b3f3c94-6892-4de7-a09e-a37f2092ef00`
- `.verifier/attempts/7deed1ed-05b8-46d3-b919-0b22c1035c31`
- `.verifier/subject-runs/3b3f3c94-6892-4de7-a09e-a37f2092ef00`
- the **seven** candidates in `.verifier/candidates/` at `local-reference-comparison-5`, one of
  them a rejected qualification

**Keep** the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs, and
the five candidates at `local-reference-comparison-1`. Leave `.verifier/store/` alone. Do not
leave a shell inside a directory you are moving.

### What to check in the run

`verify_skill` returns 150–350 KB, which overflows the tool result; read
`.verifier/runs/<run>/report-card.json` on disk.

1. **The new code ran.** `run.json`'s `local_method_ref` matches the tree, every critique's
   `rubric_ref` is v7,
   `58b2509c3e8799cf55cf60033edcb7e2d550d4ce8821295cb4daeddbeaba7aa9`, and every candidate is
   at `local-reference-comparison-6`.
2. **RDKit.** Which subjects ran it, and did they compute an answer or print documentation?
   Any `claude_timeout`, and what was the subject doing? Quote the events.
3. **The fallback.** Did any claim carry `fallback`? Its status and reason, and the record's
   first limitation line.
4. **Critique v7.** Did any critique still count a case its own objection placed outside the
   claim? Quote every `beyond_scope` verdict, and say which rest on the claim-only answer.
   Did any counted case fail a trial whose reply applied the claim? Quote the reply.
5. **Leaks.** Quote every qualification refused for a correct option that starts alone or
   alone repeats a word of the question, and count the rewrites they cost. In every counted
   `choice` case, is the key written like its options? The `leaked` count.
6. **Grades.** Quote every `case_gap` summary and say what the planner did next. Did it accept
   a settled grade below its proposal while a replacement round remained? Quote its reason.
7. **Effect-to-setting cases.** Did the planner design any, and did the critique count them?
8. **The rest.** Any refusal (quote the `model_refusal_*` events), `invalid` still zero, the
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
- **With RDKit in the image, a subject can compute an answer instead of recalling it, or look
  it up.** A pass then says the skill-guided subject ran RDKit correctly, a different statement
  from knowing it. In `31b67427` two trials printed `rdFMCS.MCSParameters.Threshold.__doc__`,
  their case's key word for word.
- **A counted case can still turn on a finer fact than its claim.** In `3b3f3c94` the only
  failing trial applied the skill's "partial rings" and rejected the atom-level docstring
  "lone ring atoms". Compare such a reply with the claim's wording before calling it a finding.
- **A fallback D rests on its cases' quotes alone.** Read it as documentary, never as behaviour.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct.
2. **Claim coverage.** `3dc02567` extracted six claims, `84e90683` four, and `74eadedd` and
   `31b67427` three.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. Their case is semantic, but a subject could still
   lowercase one.
4. **Recognition.** The fifth leak shape covers one tell; a subject can still pick the
   conventional-looking option.
5. **Reviewers and planners disagree across runs.** Spare cases absorbed two rejections in
   `3dc02567` and five `duplicate`s in `3b3f3c94`. Whether an effect-to-setting case counts is
   now decided: it does. Planners still differ elsewhere, as on whether "8 of 10 → 0.8" is the
   reference's value or the planner's arithmetic.
6. **A claim Opus 5 refuses cannot be verified on Opus 5.** If the re-run is refused too, the
   report says so, and that is the finding: a provider limitation, not the skill's.
7. **Other operational endings.** Only subject-trial faults get a fallback D; a claim ended by
   `critic_unavailable` or by the planner still reports nothing. Should they get one?
8. **Knowledge or execution.** With RDKit available, should some cases stay questions a
   subject must answer without running code? In `31b67427` a documented-phrase case was
   answered by printing the docstring that is its key.
9. **Accepting a lower grade.** The rubric lets the planner accept a settled grade. In
   `31b67427` it accepted B one counting case short of A, with a replacement round unused, on a
   misreading of what A needs. Should acceptance wait until the replacement rounds are spent?
   `3b3f3c94` did not repeat it: its pIC50 claim was redesigned to A rather than accepted at B.
   Not changed; the revision reply now states the case gap instead.
10. **How strict qualification should be.** It now refuses a correct option that alone starts
    differently or alone repeats a word of the question, which would have refused 11 of the
    last three runs' 30 choice cases. If rewrites start to cost more than the leaks did,
    should the repeated-word check drop to a warning the critique sees? The "log" among
    "logarithm"s trace stays with the critique.
11. **The prior-review trigger.** It refused a first proposal for "a reviewer may judge one of
    each pair to add little independent evidence", a sentence about the coming review. It cost
    no session; should it match only references to an earlier review?

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

Before the next live run, commit the five fixes and start a new session. The session that
made them still runs a `serve-local` started on `d8a71f6`.

### Suggested next move

Run `sar-analysis` once on the v7 code, and read the critiques' `beyond_scope` verdicts, any
qualification refused for a lone start, and any `case_gap` reply rather than the grades.

### Recommended next action

In a new session after the commit, clean `3b3f3c94` as above and run once. It is finished when
every item under "What to check in the run" has a recorded answer.
