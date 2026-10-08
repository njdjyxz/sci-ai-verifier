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

Version 0.8.0 implements the local workflow, testing each claim by tasks. `verify` and
`serve-local` provide one public action; Claude Code owns the planner loop and fresh subject
sessions; Python owns deterministic tools, bounded processes and saved evidence. Every run in
the table below before `f84c131c` used 0.7.0 or earlier, and tested claims with questions.

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
| `0aeca4c6` (2026-09-28) | scikit-survival | 1 at A, 3 at B, 1 at D by fallback after a safety refusal; 62 of 64 obtained trials passed, 0 invalid |
| `d3892f6c` (2026-09-29) | scikit-survival | 4 at A, 1 at B; 81 of 81 counted trials passed, 9 of them by the AI reader; 0 invalid, 0 faults |
| `fbd49132` (2026-09-29) | tooluniverse-dose-response | 1 at A, 3 at B; 51 of 51 counted trials passed, 0 invalid, 0 faults; every claim left facts it states untested |
| `26312681` (2026-09-30) | tooluniverse-dose-response | 2 at A, 2 at B; 57 of 57 counted trials passed, 2 of them by the AI reader; 0 invalid, 0 faults |
| `3303fd93` (2026-10-01) | tooluniverse-dose-response | 1 at A, 3 at B; 48 of 48 counted trials passed, 8 of them by the AI reader; 0 invalid, 0 faults |
| `1d1c3b6e` (2026-10-01) | tooluniverse-dose-response | 1 at A, 2 at B, 1 at D with no trials; 51 of 51 counted trials passed, none by the AI reader; 0 invalid, 0 faults |
| `90c60cbe` (2026-10-02) | tooluniverse-dose-response | 4 at A, one of them `fail` on a single case; 57 of 60 counted trials passed, 1 by the AI reader; 0 invalid, 0 faults |
| `f84c131c` (2026-10-06) | tooluniverse-dose-response | Task tests, 0.8.0: 4 at A, all `pass`; 48 of 48 trials passed, 0 invalid, 0 faults |
| `cfe9e57a` (2026-10-07) | western-blot-quantification | Question-based verdicts, critique at `xhigh`: 3 at A (`pass`, 27 of 27 trials), 2 at D by the fallback after their critiques passed the output limit; the two-step flaw passed again |
| `2bef9e0d` (2026-10-06) | western-blot-quantification | Task tests with the coverage return: 4 at A, all `pass`; 57 of 57 trials passed, 0 invalid, 0 faults; 4 tasks passed only on tolerance, hiding a flaw in the skill |

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
and reused answers filed under a case's old ID. Both are fixed. Run `d3892f6c` saw the log keep
up; the case-ID fix is **not yet seen live**, since no case there was renamed. The 2026-09-24 and
2026-09-25 entries are in the archive. Run `0aeca4c6`, the first on a
non-chemistry skill since glycoengineering, saw the reply schemas work live, and the **fallback D
ran for the first time**. That run also exposed three problems:
- a content-triggered safety refusal voided one claim;
- a code-fenced reply was misread;
- the sandbox could not run scikit-survival at all.

The last is now answered by **skill environments** (the 2026-09-28 entry). The code fence, and
reply format in general, is answered by **typed answers and an AI reader** (the 2026-09-29 entry):
seven answer types read by one reader, and a fresh session that reads again what that reader does
not pass. Run `d3892f6c` used all three, with claims sized to their tests:
- the environment was built, pinned for the planner and removed, but no subject ran scikit-survival;
  every sandbox command read the skill's own reference files;
- `choice` fell to 1 case in 28;
- the AI reader decided 9 of 81 counted trials, each a right answer with extra words on its answer
  line.

Calculated answers met their first run in `fbd49132`: two designs were keyed by programs that
first reproduced worked examples quoted from their references. That run also showed planners
testing only part of what a claim states, which the 2026-09-30 entry addresses. In `1d1c3b6e`
the planner, never told its deadline, gave its last claim no test with an hour left; the
2026-10-01 entry addresses that. In `90c60cbe`, told, it tested all four. The 2026-10-02 entry
sets a bar for changes, so that rules drawn from one run do not overfit.

**Task tests have run live once** (built in the 2026-10-05 entry, sections 5 and 6, on branch
`whole-skill-tests`): run `f84c131c` (the 2026-10-06 entry) settled the dose-response skill's four
claims at A with every trial passing, while its reviewers named parts no task tested. A skill is split into claims that are groups of its whole sections, and each
claim is tested by tasks that run the skill on input Python built. Questions, calculated answers,
generated evaluators, the claim-only check and the AI reader were removed on 2026-10-05, as version
0.8.0; what they did is recorded above and in the archive. One live test session and two live task
critiques worked, and the second critique's stream is recorded as a test.

Automated suite: **383 tests, 381 passing and 2 skipped, none failing**. The one that used to
fail only on this machine traced to 25 leftover temporary folders holding files past Windows'
260-character path limit. The folders are gone and removal now uses the long-path form.
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
- **Claude 2026-09-25** — Run `d416f79d`: four claims at B, 39 of 39 counted trials passed. A
  workflow log slow enough to starve its pipe readers and claim-only answers reused under an old
  case ID were fixed (`7b6c5c9`), and `local-contract.md`'s stale grade rule, given to every
  local planner since 2026-09-21, was corrected (`a7f023b`). The pIC50 claim's B traced to its
  planner's pages rather than its duplicates, and calculated answers were drafted.

## Claude: 2026-09-28 (reply schemas; calculated answers; run 0aeca4c6; skill environments)

### Current stage and status

Version 0.7.0, local workflow. Earlier this day two operator-requested changes were built,
committed and pushed as `265a095`:
- the verifier's own sessions (critique, documentary assessment, claim-only answers) now answer
  through a reply schema that Claude Code enforces;
- a maths claim's expected answers may be calculated by Python from a quoted formula.

Later, a new session ran **`0aeca4c6` on scikit-survival**, the first non-chemistry run since
glycoengineering:
- the reply schemas worked live;
- no planner wrote a calculation;
- the fallback D ran for the first time.

The run could execute nothing, because the pinned image lacks scikit-survival. So the operator
asked, by name, for the 2026-09-18 automatic dependency resolution design. It is now built, contracts
first, as **skill environments**: the packages a skill declares are downloaded in one step before
the run exists, and installed offline into an image that only its subject trials use.
**Skill environments build live on a blank base and are removed after each run, but have not yet
been used in a verifier run.** A Windows
long-path fix to temp cleanup was also made. The long-path fix is on `main` (`f61a97b`). At the
operator's request, skill environments live on this branch, `skill-environments`, until they have
been tested; this copy of the entry describes them.

### What has been done

In the session of run `d416f79d`, continued on 2026-09-28:

- `a7f023b`, pushed on 2026-09-25: the grade-rule correction in `local-contract.md` that the
  2026-09-25 entry records.
- The pIC50 claim's B traced to its planner's pages (the archived 2026-09-25 entry, "Drafted,
  not built"). The operator asked for that fix built, and asked why the verifier's replies were
  never held to a schema.

**1. Reply schemas.** Python parsed the three sessions' free text and learned each tolerance
after a lost reply: a code fence and a list-shaped field in `a392ea65`, a sixth finding in
`e035eef6`, an empty extra key in `0a243b7e`. Claude Code 2.1.268 has `--json-schema`; the
runner never passed it.

- Probed first, on the pinned model with the runner's own flags: five sessions, $0.13. Claude
  Code adds one `StructuredOutput` tool even under `--tools ""`, checks the reply against the
  whole schema (a `minLength` was enforced, so it validates rather than only constraining
  generation), hands a refused reply back to the session with the validator's message, and puts
  the reply in `structured_output` on the `result` event. A session whose replies could not meet
  the schema stopped as `error_max_turns`, exit 1.
- Built in `documentary.py`: `critique_schema`, `assessment_schema` and `CLAIM_PROBE_SCHEMA`; only
  the `StructuredOutput` tool is allowed; the reply is read from `structured_output`; a session
  that ends without a reply in shape is `<role>_response_invalid`. Case verdicts are keyed by case
  ID, so the schema itself demands one per packet case, and findings are exactly one per
  criterion. Python checks the reply again against the same schema with `common.validate`, which
  gained `anyOf` and `pattern`; the citation check stays Python's alone. Turn limit 2 → 4.
- Removed, because the schema prevents what they handled: the code-fence stripper, the
  lone-string, `null`-replacement, extra-finding and extra-key tolerances, the second fresh
  session for an unusable shape, judging a reply against an earlier rubric, the format paragraphs
  of the three system prompts (field meanings moved into the schemas' descriptions), the
  `attempts` record, and eight text-reply recordings with their tests.
- Recorded instead, live through the new code, $0.42: `d416f79d`'s pIC50 critique packet under
  rubric v8 (B, all three cases counted, as that run's critique judged them), `a392ea65`'s
  documentary packet, and one `d416f79d` claim-only case. **Two of the three first replies broke
  the schema**: the critique wrapped its reply in a stray `$PARAMETER_NAME` key and the
  claim-only answer added a stray `a`. Each session corrected it on the next call. Either would
  have been a lost reply before.
- Minimum Claude Code 2.1.248 → 2.1.268, the version the schemas were tested on
  (`LOCAL-INSTALL.md`). Contracts: the reply-shape paragraph under `select_local_candidate` in
  `tool-contracts.md`, which owns it, and the critique, assessor and fallback-budget paragraphs of
  `local-contract.md` (the fallback now needs one assessor session plus five minutes).

**2. Calculated answers**, built as the draft proposed. `qualify_local_candidate` in
`tool-contracts.md` owns the rule; `local-contract.md` (grade list, "Scope and evidence"),
`evidence-rubric.md` (the eligibility predicate) and `artifact-contracts.md` point to it.

- A design's `calculation` holds the program, the formula's reference and exact quote, and one to
  eight `anchors`, each a worked example quoted from a fetched page. A calculated case gives
  `arguments` and `decimals` (0 to 6); Python supplies its `expected`, rounded half away from
  zero, and its `reference_ref` and `source_quote`, the formula's. `local_evaluators.calculate`
  runs the program once per distinct argument in one container of the pinned image. Every anchor
  must reproduce at the precision its page prints, so run `3b3f3c94`'s rounded "which is pIC50 =
  7.5" for 30 nM passes as 7.522879.
- The receipts (program digest, image, outputs, anchors) let selection re-check a saved candidate
  without running it again; a catalog import runs it again. `traceable()` accepts a calculated
  answer whose anchors all reproduced, and the origin check covers the anchors' pages. Policy
  `evidence-strength-v5` → `v6`; critique rubric v7 → v8, adding `calculated_answers`. The critique
  sees the program whole, the formula, each anchor with its output and each case's arguments.
  `ai_involvement` says the planner wrote the program; the report card gains a `calculation`
  record, a "Calculated answers" line and each test's `calculated` arguments.
- With it, `d416f79d`'s two ChEMBL pages alone would support A for pIC50: the quote
  "-Log(molar IC50, XC50, EC50, AC50, Ki, Kd or Potency)" and the anchor "an IC50 measurement of
  1nM would have a pChEMBL value of 9" are both on its FAQ page.

Verification:

- Suite 341 → 349 tests: 346 passing, 2 skipped, the machine-only failure under "Current state".
- Seventeen one-line mutations of the two changes were each caught. The first pass missed one:
  selection not loading a worked example's own page went unnoticed, because the end-to-end test's
  example shared the formula's page. That test now fetches a second page.
- **Live sandbox check**, after the operator saw to Docker Desktop: the pinned image ran the
  program on six inputs in 1.3 s against the real ChEMBL page bytes. The anchor 1 nM → 9
  reproduced (the program printed 9.0); the keys were 3.60, 8.49, 9.02, 11.22 and 7.52 for 250 µM,
  3.2 nM, 950 pM, 6.0 × 10⁻¹² M and 30 nM; the ceiling at three trials was A with no limits. A
  natural-log program was refused: "The calculation gives '20.72326583694641' for the anchor with
  arguments '1e-9', where its reference prints '9'." The re-check from receipts ran nothing.
- Not verified: a critique of a calculated design, and either change in a verifier run.

Later on 2026-09-28, in a new session:

**3. Run `0aeca4c6`** (scikit-survival, 3,827 s, about $27 at API rates, 5-hour window 26% → 77%).

Results:
- Five claims: Coxnet at A; the CIF array, FastSurvivalSVM `rank_ratio` and GBSA `criterion`
  claims at B; Brier-score input at D by fallback.
- 62 of 64 obtained trials passed and none was invalid.
- The new code ran: `local_method_ref` matched the tree, and every critique ran rubric v8 under
  policy v6.
- The reply schemas held. All 59 of the verifier's own sessions ended with a valid structured
  reply, and 11 first replies refused for a stray key were corrected on the next turn.
- No planner wrote a `calculation`: no claim had a formula with a worked example.
- The log kept up: all 134 sessions have a `result` event and there was no unparsed output.

Problems it showed:
- **A content-triggered refusal voided the Brier claim.** Opus 5 flagged `brier-column-alignment`
  as `model_refusal_no_fallback`, category `reasoning_extraction`, in 4 of 4 sessions (2 per
  attempt) and in no other session. Trial 1 recovered and answered correctly; trial 2 ended with
  the error text, which stopped the claim. The end-of-run re-run repeated the pattern exactly.
- **Two correct answers were scored `fail`** because the reply opened with a code fence
  (```` ```python ````) and `exact` reads the first line. The case was uncounted, so the grade was
  unaffected.
- **Nothing could run.** No subject tried to import scikit-survival; all 113 commands read the
  skill's own files. All five planners said the library was not in the image, so every grade rests
  on scikit-survival's own documentation.
- Three B grades came from claims too narrow to supply five independent cases.

**4. Long-path fix.** The test that failed only on this machine, and the `%TEMP%` leftovers behind
it, had one cause:
- Claude Code saves large tool results 273–277 characters deep in the controller's temp folder.
- `LongPathsEnabled` is 0 on this machine, so Python could not see those files.
- `shutil.rmtree` therefore skipped them silently.

The fix:
- `extended_path()` in `claude_runner.py` gives both the per-session cleanup and the startup sweep
  the `\\?\` form.
- Two regression tests failed before the fix and pass after it.
- The 25 leftover folders were sent to the Recycle Bin at the operator's request.
- `local-contract.md` states the rule.

**5. Skill environments**, the operator's request with the constraint that package downloads
happen only in this step. `local-contract.md` "Skill environment" owns the mechanism;
`resource-policy.md` "Packages a skill declares" owns the trust decision.
- **Declarations** are read only from the skill's own snapshot, taken in setup exactly as
  `load_submitted_skill` will take it. They come from install commands in fenced Markdown blocks,
  `requirements*.txt` and `pyproject.toml` dependencies. Prose, URLs, paths, VCS references,
  markers, index options and installer packages are rejected. Import-only names are never installed.
  On the real skills: scikit-survival gives its 10 pins, sar-analysis nothing, and
  glycoengineering's `uv pip install -e .` is rejected.
- **The build** runs in setup, after the model probe and before the run or planner exists. It
  starts from `environment_base_image`, a plain Python image the operator pins, never from
  `sandbox_image`:
  1. a resolver container, the only container with a network, runs `pip download` for wheels only;
  2. Python checks and hash-locks the wheels;
  3. an offline installer applies the lock with `--require-hashes`, then `pip check`, under the
     base's own empty entrypoint;
  4. `docker commit` makes an image tagged for this build alone.

  Any failure stops the run before a planner is spent.
- **Removal.** The image is removed when the verification ends, however it ends. Setup also
  removes environment images more than a day old that a killed verification left behind. Nothing
  is cached, so each verification rebuilds, which took about 30 s.
- **Only subject trials use the built image.** Calculations, evaluators, scoring and catalog
  requalification keep the operator's image, so no package the skill chose runs where keys are
  produced or trials scored. The image is folded into the subject identity (`--subject-image` to
  the internal server) and `environment_digest` includes the record.
- **The planner** gets a pinned block rendered only from checked values, and the full record as the
  `environment` context section. A skill changed between setup and `load_submitted_skill` ends the
  run as `source_changed`.
- **Settings:** `package_index` (null by default), `environment_base_image` (required with it),
  `max_package_bytes` and `max_packages`.

Verification of items 4 and 5:
- Suite 349 → 385 tests: 383 passing, 2 skipped, none failing.
- 34 tests in `test_environment.py` run on fake Docker. Among them, a guard checks that only
  `environment.py` gives a container a network.
- Twelve one-line mutations of the first design's safeguards were each caught.
- `resource-policy.md`'s new section was kept short so that the historical verification profile's
  bootstrap stays under its 200,000-byte test bound (199,805).
- **First live build**, of scikit-survival on the RDKit image, which was the base then:
  - 10 pins resolved to 16 wheels (79 MB) in 30 s, and `pip check` passed;
  - an offline container imported `sksurv` and computed a competing-risk CIF of shape `(3, 6)`;
  - a second call reused the image with no download.

  It showed two faults, both fixed:
  - the environment carried RDKit's 670 MB and had numpy and pandas swapped under it;
  - Docker ignored the `ENTRYPOINT []` reset, so the image kept `python3` as its entrypoint.
- **Live re-check on `python:3.12-slim`:**
  - the same lock, digest `9679b819…`, came out again in 30 s;
  - entrypoint empty, 695 MB, and scikit-survival works;
  - RDKit is absent;
  - the image was gone after `remove_environment`;
  - the sweep ran;
  - `package_index` null gave `disabled`.

  No container or volume was left behind. The operator's settings file was not edited.
- **Not verified:** a verifier run in a built environment.

### Decisions taken 2026-09-28

- **Build both, and delete what the schema makes unnecessary** (operator).
- **Schemas for the verifier's own sessions only.** Subject replies keep the first-line reader:
  the subject is the skill under test, and a schema would change its session and could clash with
  the skill's own output format. Open question 3.
- **A planner-written program may key a grade-A answer** (operator, confirmed after the build).
  The planner writes a fresh program for each claim rather than the verifier holding a reviewed
  calculator; the quoted formula, the reproduced worked examples and the disclosure in the report
  are what make it acceptable. The rubric's A is "traceable or mathematically exact", and the
  local profile had implemented only the first.
- **Build automatic dependency resolution** (operator, by name, lifting the 2026-09-18
  do-not-implement flag), **with package downloads only in that one step**. This supersedes the
  "Deferred" entry and "Dependencies must already exist in the pinned image".
- **A failed build stops the run in setup** (operator), before any planner cost; `package_index`
  null runs on the operator's image instead.
- **Only declared installs** (operator): names inferred from imports are never installed.
- **Subject trials only** (approved in the plan). The verifier's own calculations, evaluators and
  scoring keep the operator's image, which also leaves open question 2 open.
- **Keep skill environments on their own branch** (operator): `skill-environments`, until they have
  been tested. The operator may still change them before any merge.
- **Build on a blank base** (operator, after the first live build). Environments start from a plain
  Python image (`environment_base_image`), never from the RDKit image. This corrects the plan's
  choice of `sandbox_image` as the base, which contradicted what had been proposed to the operator.
- **Delete each built image after its run** (operator), rather than caching it: nothing
  accumulates, at the cost of about 30 s and an 80 MB download per run.
- **Delete the 25 leftover temp folders** (operator). They went to the Recycle Bin, not
  permanently.

### Before the next run

1. **Docker Desktop's engine is running** (`docker info` prints a server version) and the pinned
   image is present:
   `sha256:127711447fe5260556ae724850ef4186a79ea774ec119ebb01c3775240f5264e`
   (`sci-verifier-rdkit:2026.3.6`). On 2026-09-28 launching Docker Desktop alone left the
   `docker-desktop` WSL distro stopped; the engine came up once the operator saw to the app.
2. **A new Code-tab session after the commit that carries these changes.** A resumed session
   keeps the `serve-local` it started with. After the run, `run.json`'s `local_method_ref` must
   equal the tree's digest, printed by
   `python -c "import sys; sys.path.insert(0, 'src'); from sci_ai_verifier.storage import implementation_bytes; from sci_ai_verifier.common import digest; print(digest(implementation_bytes()))"`.
3. **Claude Code is 2.1.268 or later** and the model is `claude-opus-5`.
4. **The working tree is clean** at that commit.
5. **The plan's 5-hour window has room.** `0aeca4c6` cost about $27 and took the window from 26%
   to 77%, so plan one run per window.
6. **The timeout.** The app passes 7,200 s, the most `serve-local` accepts; the operator raised it
   from 5,400 s on 2026-09-29, and a session started before that still serves 5,400 s. `0aeca4c6`
   used 3,827 s for five claims, and each environment build adds about 30 s of setup.
7. **For a skill environment**, the operator adds two settings to `.verifier/local-settings.json`:
   - `package_index: "https://pypi.org/simple"`;
   - `environment_base_image:
     "sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea"`, the local
     `python:3.12-slim`.

   Each run downloads the scikit-survival stack, about 80 MB of wheels.

### Cleaning the previous run

Move, do not delete, into the session scratchpad:
- `.verifier/runs/0aeca4c6-5f2c-4d72-87a4-e8452340a5dc`
- `.verifier/attempts/f32cd389-5e51-4b87-adb9-b17de85e397d`
- `.verifier/subject-runs/0aeca4c6-5f2c-4d72-87a4-e8452340a5dc`
- the nine candidates it wrote at `local-reference-comparison-6`, dated 2026-09-28

Keep the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs and its five
candidates. Leave `.verifier/store/` alone: environment build records live there. `d416f79d`'s
files are already in an earlier session's scratchpad. Built environment images need no cleaning:
each run removes its own.

### What to check in the run

1. **The new code ran.** `local_method_ref` matches the tree, every critique's `rubric_ref` is v8,
   `499ff634d7fbd0e28780ecff9370a6bd587ab6354f1af57cd8dfe00073bbb1a7`, and the audits carry policy
   `evidence-strength-v6`.
2. **Reply schemas.** Every critique, assessor and claim-only session ends `success` with a
   `structured_output`. Count the sessions whose first reply Claude Code refused (a `tool_result`
   with `is_error` in the events) and quote the validator's messages. Any `*_response_invalid`,
   with its stream. How many turns sessions used.
3. **Calculated answers.** Did any planner write a `calculation`, the pIC50 claim above all?
   Quote its program, formula and anchors, any qualification it was refused, and what the
   critique said of the program under `calculated_answers`. The grade it settled at, and why.
4. **Claim-only answers on calculated cases.** Any `missed` at the case's rounding, with the
   answers and key: a reader working by hand, or a wrong key?
5. **Carried from 2026-09-25.** The log keeps up: every session has its `result` event, no
   `process_unparsed_output`, no claim-only `claude_incomplete`, late-run wall-time gap near 2 s.
   A reused claim-only answer shows its case's current ID.
6. **The rest.** Refusals (quote `model_refusal_*`), `invalid` still zero, claim count, run time.
7. **Skill environment.**
   - The setup log's `preflight.environment` status should be `built`, on `python:3.12-slim`.
   - The lock (digest `9679b819…` if nothing moved on PyPI).
   - That no `sci-verifier-env` image remains after the run.
   - The planner's pinned block.
   - Whether subjects now run scikit-survival or the skill's scripts.
   - Any docstring lookups of a key: trace `mcp__subject__run_command`, as with RDKit in `31b67427`.
   - Whether any planner designs an executed case.
   - That calculations and scoring still report the operator's image ID.

### Reading the results without fooling yourself

The 2026-09-25 list still holds (archived), with three additions:

- **A critique is one session now.** A reply Claude Code refused is visible only in the stream,
  as a `StructuredOutput` call answered by a `tool_result` with `is_error`.
- **A calculated case's `reference_quote` is its formula**, not its value; the value came from
  the program, whose anchors are in the report's `calculation` record.
- **A calculated key is exact at its rounding.** A subject that answers more decimals than the
  question asks for fails at the installed tolerance; read the question before the verdict.

### Open questions for the operator

1. **Is one anchor enough?** A worked example in nanomolar cannot catch a micromolar slip in a
   case's arguments; only the claim-only answers do.
2. **Answers produced by running RDKit** for RDKit claims: no formula to quote, since the library
   is the reference; an answer holds only for the pinned 2026.03.6; and subjects hold the same
   RDKit. Was open question 8's other half.
3. **Subject replies through a schema?** Not done, for the reason under "Decisions".
4. **From `0aeca4c6`**, proposed, not built:
   - **Refusals.** Replay the flagged question a few times on the pinned model first. If recovery
     is random, retry only the refused trial. If it is deterministic, let the planner reword the
     case instead of re-running the claim unchanged. Either way, show a stopped claim's obtained
     trials in its headline.
   - **Code fences.** Read the first line inside a fence for all three methods.
   - **Coverage.** A run sampled five narrow API facts and none of the skill's workflow advice.
   - **Narrow claims.** Say in the report when a B was limited by the claim's size rather than its
     source.
5. **From skill environments:**
   - Subjects can read installed docstrings, so doc-keyed cases can be looked up.
   - A fenced counter-example install line stops the run if it cannot resolve.
   - Should library output ever key an answer? That is open question 2.
6. **Carried from 2026-09-25**, detail in the archive: the aggregation rule as a plan field; claim
   coverage (three to six claims per run); the capitalisation residue; recognition cases passed on
   plausibility; planners and reviewers differing across runs (for pIC50 the cause was pages, now
   answered by calculated answers); claims Opus 5 refuses; a fallback for other operational
   endings; accepting a lower grade; how strict qualification should be; the prior-review
   trigger; two or three claim-only answers per case.

### Deferred, and why

Unchanged from 2026-09-25: parallel trials, appending to the timelines, Opus 5.5 (until WinGet
offers Claude Code 2.1.280), a longer subject limit and the case-level contract. Automatic
dependency resolution left this list on 2026-09-28, when the operator asked for it.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-28"). Follow its preflight, clean the previous run as it
describes, and use scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\scikit-survival"

Show me the report and workflow-log paths, a table with one row per claim
(grade, accuracy, consistency, status and the other measurements) and, for each
claim, a table with one row per test. Tell me whether it is a good run, and
whether our changes work: go through the entry's "What to check in the run" list
item by item. Before concluding anything from a `fail`, an `invalid`, a refusal
or a unanimous "none of these", quote the verbatim reply or event behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None blocking. Skill environments are committed on this branch with this entry and are not merged
into `main`. Testing them needs this branch checked out, and a new session started after that,
because a session started earlier runs a `serve-local` with the old code.

### Suggested next move

Run scikit-survival in a built environment. The build itself is proven live. The question now is
whether subjects execute the library once it is installed, and whether planners design executed
cases.

### Recommended next action

With the operator's go-ahead:
1. Add the two settings under "Before the next run", item 7.
2. Start a new session with this branch checked out.
3. Clean `0aeca4c6` as described above.
4. Run scikit-survival once.

It is finished when every item under "What to check in the run" has a recorded answer.

## Claude: 2026-09-29 (typed answers and the AI reader, on skill-environments; run d3892f6c)

### Current stage and status

Version 0.7.0, local workflow, on the `skill-environments` branch. The operator asked for one
general fix for replies that give the right answer in a form the scorer cannot read. The earlier
fixes had turned good open questions into multiple choice: `choice` went from no cases at method
versions 1 and 2 to 52–71% at versions 3 to 6, and 13 claim grades in 17 runs were capped for
want of generated cases. Two parts are built, contracts first, on top of the skill environments
of the 2026-09-28 entry:
- **Typed answers.** Seven installed answer types, one reader that finds the answer line past a
  code fence or an `Answer:` label, controls generated for each type, and one line Python adds to
  each case's input stating its answer form.
- **The AI reader.** A counted trial Python's reader does not pass is read again by a fresh no-tool
  session. Its reading decides that trial unless Python's checks refuse it. The grade stays, and
  the report shows every reading beside the status Python's reader alone gives.

Later the same day, at the operator's request, claims were sized to their tests (**Claim scope**
below). All of it is committed on `skill-environments` as `73496d6` and pushed; `51b3cd2` then gave
each verification two hours (`--timeout 7200`). **Run `d3892f6c` used all of it** (below): five
claims, four at A and one at B, every counted trial passing. This replaces the earlier "none of
this has been used in a verifier run, and nothing is committed yet".

### What has been done

This session, 2026-09-29, after the work of the 2026-09-28 entry:

**1. The format history.** A replay of 945 saved replies from 17 report cards found five forms
that had misread right answers: a plural (`e13f50ee`), `Molar` (`fb64115f`), `**1**`
(`7efbdd8c`), an explanation below the answer (`0a243b7e`) and a code fence (`0aeca4c6`). Only
the two fenced replies were still misread by the old reader.

**2. Contracts.**
- `tool-contracts.md`, under `qualify_local_candidate`, owns the types and "Reading a reply".
  The types are `numeric` (with an optional `unit`), `exact`, `term`, `expression`, `list`, `set`
  and `choice`. It also owns the answer-format line and the controls.
- `local-contract.md` gains "Reading replies", which owns the AI reader. The same file points to
  it where grades, verdicts and subject input are described.
- `evidence-rubric.md`:
  - A's row allows an AI reading of which answer a reply gives;
  - "generated" points to the open types;
  - AI-involvement says a reading does not lower A.
- `artifact-contracts.md`, `local-evaluator-spec.md` and `LOCAL-INSTALL.md` are updated to match.

**3. Code.**
- The new `answers.py` holds the reader, the types, the controls and the answer-format lines. The
  fence parser moved from `environment.py` to `common.py`, so both use it.
- `local_candidates.py` qualifies each case by its type; method version `-6` → `-7`.
- `local_science.py`:
  - counts every open type as generated;
  - traces a term to its quote by its words;
  - policy `evidence-strength-v6` → `v7`;
  - `decide` records `reading_summary`, with the status and accuracy Python's reader alone gives.
- `documentary.py`:
  - adds the reader session, and reads claim-only misses except `UNDETERMINED` and
    `none of these`;
  - critique rubric v8 → v9, adding `answer_types` and wording A as the rubric's row now does.
- `local.py`: the tool schema, the answer-format line, readings after each claim's trials,
  reading receipts, and a report with a "Read by" column and an AI-reader paragraph per claim.

**4. Verification.**
- Suite: 385 → 419 tests, 417 passing and 2 skipped, none failing (425 after claim scope below).
- `tests/recorded/subject-replies.json` keeps all 945 replies, labelled right, wrong or
  paraphrase; `test_answers.py` replays them:
  - every right answer passes, including the 19 trials misread when they ran;
  - the 10 wrong trials still fail, and the 3 paraphrases are left to the AI reader.
- 32 one-line mutations were each caught, and the baseline and restored trees passed:
  - 30 of the reader, the type rules, the AI reader, the Python-only status and the disclosure;
  - 2 of the follow-ups below.
- Follow-ups the new tests found or prompted:
  - a label's emphasis closing after the answer (`**Answer: 42**`) is now removed;
  - an option whose text reads as another option's number (`3` at position 1) is refused;
  - `term` refuses a number with the right message.
- **Live recordings**, about $0.23 on the operator's go-ahead, through the code that reads them:
  - `d416f79d`'s critique packet under rubric v9 settled at B with all three cases counted, as
    under v8.
  - The AI reader called `MolOps::adjustQueryProperties` `matches` for key
    `adjustQueryProperties`, "a formatting difference". It did so although the question asked for
    no namespace prefix.
  - It called a paraphrase of a sentence the question wanted verbatim `differs`.
  - All three first replies met their schemas.
- The verification bootstrap is 199,919 of its 200,000 bytes after claim scope, 81 to spare. Each
  document pinned for the local planner fits the 40 KiB section reply, now tested.
- Not verified then: any of this in a verifier run. Run `d3892f6c` below has since used it.

### Decisions taken 2026-09-29

- **Build the full typed-answer system and the AI reader together, on this branch** (operator),
  to be tested with skill environments in one run.
- **An AI reading counts, and the grade stays** (operator). The other options were capping the
  claim at B, or lowering it to C. A reading establishes what a reply says, never what the right
  answer is, so the rubric's A row now allows it. It is disclosed on every trial and claim.
- Proposed here and built:
  - the reader reads only counted trials Python did not pass;
  - Python refuses a reading whose copied answer is not in the reply, that another model gave,
    or that its own reader settles the other way;
  - no reading is ever retried;
  - Python, not the planner, writes the answer-format line;
  - the critique learns the answer types but not the reader.

### Claim scope

The operator asked why extracted claims are so narrow, and why they vary so much between runs.
A survey of the 17 report cards answered both:
- **Narrow claims cap grades.** Since per-case verdicts began (`28d19f8a`), 24 of 41 graded claims
  settled below their source's grade only because of their case count, most often one counting
  case short of A.
- **They also produce padding.** Critiques rejected 17 cases as `duplicate`, the same fact asked
  from the other direction. The critique of one `0a243b7e` claim wrote that it was "narrow enough
  (two documented constants plus one corollary) that five genuinely independent counting cases may
  not be constructible".
- **The variety is in the cutting, not the facts.** The 13 sar-analysis runs drew their claims from
  the same few passages: the FindMCS settings at `SKILL.md:37` in all 13, pIC50 in 12, dummy atoms
  in 12, RGroupDecompose in 10. That one passage became one, two or three claims, and runs had
  three to six claims. No claim ever tested the skill's workflow advice; `0aeca4c6`'s five were
  narrow scikit-survival facts too.
- **Cause.** The local planner's only guidance is the tool description "commit atomic claims".
  Nothing says how broad a claim is, how many to write, or what to cover.

Proposed changes, of which 1 to 3 are built:
1. Replace "atomic" with a scope rule, owned by `local-contract.md`. A claim is one behaviour the
   skill tells its user to rely on: a procedure step, a documented rule, or one function's
   behaviour. It includes every fact the skill states about that behaviour, and is broad enough
   for about six independent questions (A's five plus a spare). A behaviour that cannot support
   that merges with a neighbouring one; unrelated behaviours never merge.
2. A fixed procedure:
   - walk the skill's sections in order and take one claim per section that makes a testable
     promise;
   - prefer what the skill tells its user to do over library trivia;
   - write at most five claims, because broader claims mean more trials, and runs are near the
     90-minute limit.
3. Report lines: "limited by the claim's size, not its source" where only the case count held a
   grade down (open question 4 of the 2026-09-28 entry), and the skill's sections that received
   no claim.
4. Optional: start a re-run of an unchanged skill from the previous run's claims, keeping or
   replacing each with a reason. Runs become comparable, but earlier mistakes carry over.

**Decided** (operator): first "not before the next run"; then, superseding that, build items 1
to 3 before it and save item 4 for later.

Built:
- **Contract.** `local-contract.md` gains "Claims", which owns the scope rule, the
  section-by-section procedure and the limit of five. A section is the text under one heading
  of `SKILL.md`, and a reference file belongs to the first section that names it.
  `tool-contracts.md` lists a manifest over the limit as retryable, and `artifact-contracts.md`
  lists the new report fields.
- **The planner's tools.**
  - The shared `commit_claim_manifest` description still says "atomic" for the older profiles.
    The local planner's copy states the local rule instead: `local_definitions` in `tools.py`,
    used for both the served tools and the pinned block.
  - Step 1 of the planner prompt points to "Claims".
  - `MAX_CLAIMS = 5` is the local `max_claims` limit, with its own refusal message.
- **Coverage.** `claims.sections` reads `SKILL.md`'s sections, skipping frontmatter, a `#` inside
  a code fence, and headings with no text of their own. `claims.section_coverage` maps each
  claim to the section it covers.
- **Report.**
  - A "Skill sections" line near the top lists the sections no claim covers, and each claim has
    a "Skill section" line. The JSON gains `coverage` and each row gains `sections`.
  - `local_science.size_limit` gives a claim held below its source's grade only by its case
    count a "Limited by its number of independent cases, not its source" line, and its row a
    `size_limited` record.
  - `reference_grade` now holds the half of `evidence_ceiling` that the report reads back.
- **Replayed on real claims,** the coverage shows the problem:
  - `d416f79d`'s four claims covered two sections, two claims each;
  - three of `3dc02567`'s six came from the one MCS section;
  - three of `0aeca4c6`'s five came from "Model choice".
- **Verification.** Suite 419 → 425 tests. Ten one-line mutations were each caught, after one test
  was tightened: the first pass missed frontmatter handling, because the section test gave the
  frontmatter an intro line. It now also checks frontmatter directly before a heading.

**Across all 15 sar-analysis runs**, the claims covered 2 to 4 sections each, and 14 runs put a
second claim on a section already covered. Workflow was tested in 3 runs, Decision Framework and
Best Practices in 1 each, and Substructure Alignment and Activity Heatmap never. Two causes:
- **Splitting one passage.** The MCS section is one paragraph (`SKILL.md:37`), and 7 of the 17
  manifests split it into two or three claims (definition, threshold, ring options). Those split
  claims are the ones capped by their case count.
- **Chasing the easy oracles.** MCS parameters, pIC50 and dummy atoms have crisp API
  documentation; the workflow advice does not.

**Drafted, decide after the run: one claim per paragraph.** Python would refuse, as retryable, a
local manifest in which two claims quote the same paragraph, telling the planner to merge them.
Replayed over the 17 saved manifests, it refuses exactly the 7 that split the MCS paragraph and
nothing else. Claims on separate "Common Pitfalls" items, and on different scikit-survival
reference files, still pass. It enforces the "one behaviour" rule where planners broke it.
Python cannot tell which sections are testable, so it cannot force coverage of the hard ones.
The operator chose to run first on the instructions and the coverage line, and add this only if
the run still splits a passage.

### Run `d3892f6c`

Scikit-survival, 2026-09-29, on `51b3cd2`, after a Claude restart, from a session whose
`serve-local` started after both commits, with `--timeout 7200`:
- **Result.** Five claims, four at A and one at B, all `pass`. All 81 counted trials passed; none
  was invalid, missing or refused.
- **Time.** 3,641 s. Setup, including the environment build, took 34 s, and each claim 7 to 16
  minutes.
- **Cost.** About $24.69 at API rates: the planner $13.06 over 45 turns, 84 subjects $7.22, 7
  critiques $3.27, 64 claim-only sessions $0.97 and 17 readings $0.17. The 5-hour window went from
  3% to 52%.
- **Report.** `.verifier/runs/d3892f6c-4597-440b-a3fd-e008dbe2fc8e/report-card.md`, outside Git.

The checks this entry set for the run, answered:
- **The new code ran.** `local_method_ref` equals the tree's digest, `95f2ea51…`. All five critiques
  carry rubric v9, the audits carry policy `evidence-strength-v7`, and all nine trial readings carry
  `reader_ref` `738e3dbe…`.
- **Answer types.**
  - 1 of the 28 final cases is `choice` (3.6%, against 52–71% at versions 3 to 6). The rest are 16
    `term`, 4 `expression`, 3 `exact`, 3 `numeric` and 1 `set`; one replaced design had a `list`.
  - Every claim had at least two generated counting cases, so none was capped for want of them (13
    grades in 17 runs before).
  - One qualification was refused, by the new `exact` rule: a dtype keyed as `exact` although its
    case carries no meaning. The planner re-keyed it.
- **The AI reader** read 17 answers. It called all of them `matches`, and Python refused none.
  - Nine were counted trials, each a right answer that Python's reader failed for extra words on the
    answer line: "floating-point" for `float` (3), "Higher-is-riskier risk scores" and "Risk scores
    (…)" for `risk scores` (3), and "Estimated survival probabilities" and the like for `survival
    probabilities` (3). By Python's reader alone C1 would be `fail` at 15 of 18, and C2 at 12 of 18.
    Each copied answer is the reply's leading phrase, and each reason calls it the expected answer
    in other words, for example "'floating-point' is an equivalent wording of the expected answer
    'float'". The report quotes all nine.
  - Eight were claim-only answers. Six were the same kind, such as "boolean (bool)" for `boolean`.
    The other two read "the event time points" as matching `unique times`: a paraphrase, not
    presentation, and it hid the miss that claim-only answers exist to catch. The critique rejected
    that case as `beyond_scope` anyway, because its key is finer than the claim's wording, and the
    planner replaced it. See open question 1.
- **Claim scope, against the survey:**
  - five claims from five of the skill's 14 sections, one each; in `0aeca4c6` three of five came
    from "Model choice";
  - one claim settled below its source only for its case count: C4, at B with 4 of 5 counting cases
    (24 of 41 before). The report's "Limited by its number of independent cases" line names it;
  - one `duplicate` in seven critique sessions, replaced before any trial (17 in 17 runs before),
    with two `leaked` and one `beyond_scope`;
  - no claim summarises the skill, but four are broader than their cases. The critiques note that no
    case tests `concordance_index_ipcw` or `integrated_brier_score` (C2), the two competing-risk
    prohibitions (C3), C4's central GridSearchCV instruction, or seven of C5's nine estimator
    families. C2, C3 and C5 still settled at A (open question 5);
  - no two claims quote the same paragraph, so, as the operator decided, the drafted paragraph rule
    is not added;
  - the skill's workflow advice, "Non-negotiable workflow" and "Leakage-safe pipeline", got no
    claim, nor did Scope, installation, the CLIs, security triage, reference files, dated sources
    or citing.
- **C4 stayed at B by the planner's choice.** Its critique asked for four revisions, among them a
  case for the claim's central instruction. The planner re-proposed B on the same design instead.
- **Skill environment.**
  - Built on `python:3.12-slim` in 34 s, with lock `9679b819…`, the same as the live check.
  - The planner's 1,104-byte pinned block listed the 16 packages. No `sci-verifier-env` image,
    container or volume remained afterwards.
  - **No subject ran scikit-survival or the skill's scripts.** 30 of 84 trials used `run_command`,
    and all 79 commands read the skill's own reference files with `grep`, `sed`, `cat`, `find` or
    `ls`. So there was no docstring lookup to trace.
  - No planner designed an executed case or a calculation, and scoring used the operator's image.
- **Sessions and log.**
  - All 174 sessions ended `success`, each with its result event.
  - Every critique, claim-only and reader session returned a `structured_output`. Claude Code
    refused the first reply of 6 of 7 critiques and 4 of 64 claim-only sessions, each for an extra
    property such as `input`, `reason_for_call`, `_dummy` or `tool_use_id`, and every retry passed.
  - The two revised designs reused the claim-only answers of their unchanged cases, under the
    current IDs: 64 sessions for 32 distinct cases.
  - No refusal, `process_unparsed_output`, `claude_incomplete`, `*_response_invalid`, model change
    or timeout. No assessor ran.
  - The log kept up: at most 0.09 s between a session's result and its end, late in the run too.

### Open questions for the operator

1. **How lenient the AI reader should be.** It may judge `7.6e-9 M` to match 7.6 nM, a scientific
   equivalence rather than presentation, and in a recording it ignored a question's "without the
   namespace prefix". In `d3892f6c` every trial reading was presentation, but a claim-only reading
   called "the event time points" a match for `unique times`, and so hid a key finer than its
   claim. Claim-only misses could be read only for presentation, or not read at all, or the
   critique could see Python's reading beside the AI's.
2. **Uncounted trials are not read**, to save run time. Their report rows keep Python's verdict.
3. **List and set items are typed by their own form**, so a capitalised item such as `Core` is
   compared exactly.
4. The 2026-09-28 entry's open questions stand.
5. **Broad claims with partial cases.** Four of five claims settled with cases that test part of
   what they state, three of them at A. Should A need counting cases that reach each fact a claim
   states, or should a claim be cut down to what its cases test?
6. **The environment went unused.** Subjects answered documentation questions from the skill's own
   files, so the packages installed for them made no difference. Whether planners should write
   cases that need the library turns on open question 2 of the 2026-09-28 entry, a library's output
   as a key.

### Urgent next steps, if any

None. `skill-environments` is committed and pushed; merging it into `main` is the operator's call.

### Suggested next move

Settle open questions 1, 5 and 6, then run sar-analysis on this branch. The claim-scope survey's
baseline is 15 sar-analysis runs, so that run shows whether the instructions alone stop planners
splitting the MCS paragraph (`SKILL.md:37`) and returning to the same few passages. It also gives
typed answers and the AI reader a second skill.

### Recommended next action

This entry's earlier next action, to commit and run scikit-survival, is done; its checks are
answered under "Run `d3892f6c`". Next, with the operator's go-ahead:
1. Answer open questions 1, 5 and 6, or leave them open.
2. Follow "Before the next run" in the 2026-09-28 entry. Move, do not delete, into the session
   scratchpad:
   - `.verifier/runs/d3892f6c-4597-440b-a3fd-e008dbe2fc8e`
   - `.verifier/attempts/90e15c3d-e24d-4ee9-86e4-f5ae97d7deee`
   - `.verifier/subject-runs/d3892f6c-4597-440b-a3fd-e008dbe2fc8e`
   - the nine candidates it wrote at `local-reference-comparison-7`, dated 2026-09-29

   Keep the glycoengineering run, its attempt, subject-runs and five candidates, and
   `.verifier/store/`. `0aeca4c6`'s files are already in this session's scratchpad.
3. Start a new session and run sar-analysis.

Record, against the survey and this run: the claims and sections covered, claims held back only by
their case count, `duplicate` verdicts, any two claims on one paragraph, every AI reading, and what
subjects did with `run_command`. It is finished when each has a recorded answer.

## Claude: 2026-09-30 (runs fbd49132 and 26312681; planner told to test each fact a claim states; critique given Python's search record)

### Current stage and status

Version 0.7.0, local workflow, on `skill-environments`. On 2026-09-29 the operator ran a new skill,
`tooluniverse-dose-response`, as run `fbd49132`: one claim at A and three at B, every counted trial
passing, and every claim leaving facts it states untested (below). The operator judged the planner
lazy and asked for the planner's and the reviewer's instructions to be fixed. That is built (`fe47267`):
- **Planner.** Test a claim fact by fact, searching for each fact's source; keep a quote whole;
  revise, answering every required revision, before accepting a lowered grade.
- **Reviewer.** Critique rubric v10 lists the claim's facts against the counting cases, and turns a
  gap it can see a way to close into a required revision.

**Run `26312681`** then used it on the same skill (section 5): two claims at A and two at B. The
revise-before-accepting rule worked once, on C2, which went from B to A. The search rule did not:
C3 and C4 got no web search, were designed at B's minimum of four cases, and their critiques took the
planner's description of searches made for other claims as searches for theirs. The critiques also
read the planner's notes cut short. On the operator's go-ahead both are now fixed (section 6): the
critique reads the notes whole and judges searches by **Python's search record**, read from the
planner's own stream, under rubric v11. That fix is replayed live (below) and **not yet seen in a
run**. It cannot reach a plan that settles at its own proposal, as C3 and C4 did (open question 4).

### What has been done

This session, 2026-09-30:

**1. Run `fbd49132`**, tooluniverse-dose-response, 2026-09-29, on `4308111`, in a session started
after a Claude restart, with `--timeout 7200`:
- **Result.** Four claims: C1 (the 4PL equation) at A; C2 (data preparation), C3 (reading the four
  parameters) and C4 (quality gotchas) at B; all `pass`. 51 of 51 counted trials passed, and the 9
  uncounted ones too; none was invalid, missing or refused, and every case was unanimous.
- **Time and cost.** 3,061 s. About $19.79 at API rates: the planner $13.87 over 51 turns, 60
  subjects $2.60, 5 critiques $2.48 and 46 claim-only sessions $0.84; no readings. The 5-hour window
  went from 0% to 39%.
- **The new code ran.** `local_method_ref` equals the tree's digest, `95f2ea51…`. The critiques
  carry rubric v9 and the audits policy `evidence-strength-v7`.
- **Calculated answers, first seen live.** C1's keys came from a program implementing GraphPad's
  4PL formula, anchored on three Wikipedia Hill-equation statements; C2's from a percent-of-control
  program that reproduced four percentages printed in a CCK-8 protocol's table.
- **Against the claim-scope survey:**
  - four claims from four of the skill's eight sections, one each; none for the title section,
    "Step 2 — Fit / get the potency", "Honest limitations" or "Related skills";
  - three claims held back only by their case count, C2 and C3 at 4 of 5 counting cases and C4 at 3,
    each with `size_limited` showing that its source supports A;
  - three `duplicate` verdicts, two in C2 and one in C3, in designs that executed;
  - no two claims on one paragraph, and no AI reading;
  - `run_command` in 20 trials, each one line of `python3 -c` evaluating the formula, 18 in C1 and 2
    in C2. No subject ran the skill's script, which imports scipy: the skill declares no packages,
    so setup built no environment (`not_needed`) and the operator's image has no scipy.
- **Report.** `.verifier/runs/fbd49132-6165-44d5-93de-33025f8a5577/report-card.md`, outside Git.

**2. What went wrong: the planner took the cheapest legal path.**
- **Facts untested in every claim.** No case tested C1's statement about the helper's `hill_4pl`;
  C2's cases tested 3 of its 6 preparation rules; C3's left every threshold, the fold-shift rule and
  the Emin reading untested; C4's three cases reached 2 of its 5 gotchas. The coverage notes and
  critiques said so, but each claim's row gives one grade and `pass` for the whole statement.
- **No search for C4's missing gotchas.** The planner fetched two Wikipedia pages by URL, made no
  WebSearch for that claim, and designed exactly the three cases B needs, with no spare.
- **Accepting instead of revising.** C2's and C3's critiques settled B below a proposed A, with 4
  negotiation rounds and 1 replacement round left, and required cases for named untested rules; for
  C2's linear-vs-log10 rule the GraphPad page was already fetched. The planner accepted B both times,
  "rather than spend the remaining time on further revisions". Run `d3892f6c`'s C4 did the same.
- **Revisions answered in part.** C4's first critique required a case for the incomplete-curve
  remedy; the revised design met its other three requests and skipped that one.
- **A cut quote.** The first manifest was refused over a doubled space in C4's quote. The planner cut
  the quote to two of five gotchas and kept the statement of all five.
- **Where the rules allowed it.** The planner prompt offered accepting as one of "two moves";
  nothing asked cases to reach a claim's facts or asked for a search per fact; Python checks that a
  quote occurs, never what the statement adds; and a plan whose critique agrees with its proposal is
  fixed at once, so a design built at a low ceiling never returns to the planner.

**3. Changes**, contracts first:
- `local-contract.md`, "Claims", which owns both: **Quoted whole** (a quote carries every fact its
  statement states; correct a refused quote, and a shorter quote needs a shorter statement) and
  **Tested fact by fact** (a case for each fact a source can key before a second case on any; a
  search for each fact before leaving it untested; the spare case; within the subject-call budget,
  the facts the skill's user relies on most).
- `evidence-rubric.md`, step 4 of "Negotiating the grade": **Revise before accepting.** A revision
  answers every revision the critique requires; a lowered grade is accepted only when no search finds
  a source for what the critique asks, and saving run time is no reason.
- `tool-contracts.md`, `select_local_candidate`: `coverage` goes through the claim's facts, naming
  the cases for each and, for an untested fact, what was searched for and found.
- `SKILL.md` and the negotiation paragraph of `local-contract.md` restated step 4's old choice;
  both now point to it, and the operator's `LOCAL-CONFIG.md` describes the new rule.
- Code:
  - the planner prompt's steps 2 to 4 in `local_entry.py` follow these;
  - `local.py`'s `local_design_unchanged` message says to answer every required revision and to
    propose the settled grade only when step 4 allows it;
  - `claims.py`'s `quote_not_found` message, shared by every profile, says to correct the quote and
    to shorten the statement with it;
  - critique rubric v9 → v10 in `documentary.py`: criterion 2 is checked "as rubric.coverage says",
    and `coverage` asks for the facts with the counting case testing each. When the critique's grade
    is below the proposal, each untested fact a listed reference bears on, or no stated search
    covers, is a required revision; listing a gap does not by itself lower the grade.

**4. Verification.**
- Suite 425 → 426 tests, 424 passing and 2 skipped, none failing. New checks: the planner prompt
  and pinned blocks carry the new rules and no longer offer "two moves"; the quote refusal says how
  to repair; the v10 rubric carries its coverage rule.
- Sizes: the pinned `local-contract.md` is 38,580 of its 40,960 bytes, and the verification
  bootstrap 199,970 of its 200,000, so the next text added to `evidence-rubric.md` or `SKILL.md`
  must be offset there.
- **Live recording**, about $0.37: `d416f79d`'s pIC50 packet under v10 settled at B with all three
  cases counted, as under v8 and v9, and criterion 2's finding listed the claim's three facts with
  the cases testing each. Its first reply added a stray `evidence_ceiling` key, which Claude Code
  refused and the session resent.
- **Replays** of `fbd49132`'s four final critique packets on `claude-opus-5`, about $6.02: two
  samples of each under v10, and a second v9 sample of C2 to C4 beside the run's own critique.
  - **No grade moved.** C1 settled at A in all three samples, and C2, C3 and C4 at B in all four
    each. C2 counted four or five cases under either rubric; the other verdicts never changed.
  - **Criterion 2 now lists the facts.** Every v10 finding went through the statement fact by
    fact, eleven facts for C3, seven for C2 and six for C4, marking each untested one with whether
    a fetched reference bears on it and whether a search is stated. v9's findings summarised
    coverage in a sentence or two. Each list fit its 4,000-character field, and the report prints
    it under the claim.
  - **Required revisions** already named untested facts under v9 whenever the grade fell below
    the proposal (C2, C3). Under v10 they also tie each gap to the fetched page that bears on it,
    such as C2's linear-scale rule and the GraphPad page in hand; the number of gaps named did not
    rise.
  - **C4 is out of the reviewer's reach.** Its grade equals its proposal, so no revision is
    required, and v10 accepted the planner's mention of C2's blocked NCBI chapter as a search for
    C4's gotchas, though no search was made for that claim. Only the planner rules reach it.
  - One C3 sample offered narrowing the claim's scope as the alternative to a case, which the
    rubric's `verdict_consistency` rules out.
  - As in `d3892f6c`, Claude Code refused the first reply of 11 of the 12 sessions, v9 ones
    included, for a stray property such as `reason`, `cases` or `dd`; every retry passed.
- The 5-hour window was at 28% after this session's recordings and replays.
- A baseline in a scratchpad worktree failed on Windows' path limit (WinError 206), not on the
  code; in the repository the suite passed 425 of 425 before these changes.

Not verified then: any planner change in a run. Run `26312681` below has since used them.

**5. Run `26312681`**, tooluniverse-dose-response, 2026-09-30, on `fe47267`, from a session whose
`serve-local` started at 16:56 after that commit, with `--timeout 7200`. `fbd49132`'s files were moved
first, as this entry's recommended action said.
- **Result.** C1 (the 4PL equation) and C2 (data preparation) at A; C3 (reading the parameters) and
  C4 (quality gotchas) at B; all `pass`. 57 of 57 counted trials passed and the 3 uncounted ones too;
  none invalid, missing or refused; every case unanimous. Two C2 trials passed by the AI reader:
  "ic50" for an `exact` key "IC50". By Python's reader alone C2 is 13 of 15 and `fail`.
- **Time and cost.** 3,328 s of 7,200, and 60 of 128 subject calls. About $20.86 at API rates: the
  planner $15.12 over 51 turns, 60 subjects $2.68, 5 critiques $2.33, 42 claim-only sessions $0.69 and 2
  readings $0.03. The 5-hour window went from 29% to 70%.
- **The new code ran.** `local_method_ref` equals the tree's digest, `35bd30f0…`; the critiques carry
  rubric v10.
- **Against `fbd49132`, as this entry asked:**
  - facts tested, from each critique's v10 list: C1 6 of 7, C2 5 of 7, C3 4 of 12, C4 4 of 7, the
    three untested C4 facts being the incomplete-curve, too-few-points and biphasic gotchas;
  - WebSearch: 4 queries for C1 and 4 for C2 (one counted under C1, made before C2's first call), and
    **none for C3 or C4**. C3 fetched two Wikipedia pages by URL and C4 one, and the planner wrote
    "moving quickly" before C4;
  - critiques and their revisions: C2's first critique settled B below a proposed A, with 4 rounds and
    1 replacement round left, and required four revisions. **The next design answered all four** (a
    replacement for the leaked case, a direction case, and recorded searches for the point-count and
    unit rules) and settled at A. C3 and C4 were proposed at B, the ceiling of their four cases, and
    fixed at once, so neither critique could ask for more;
  - no accept below a proposal, so "revise before accepting" held where it applied;
  - no quote refusal: the manifest was accepted first time, and C4's quote now holds all five
    gotchas;
  - C1's first proposal was refused for `prior_review_in_packet` over the word "verdict" in its notes,
    spending no session;
  - grades 2 A + 2 B, against 1 A + 3 B; time 3,328 s against 3,061; subject calls 60 against 60;
  - sections covered: the same four of eight; no subject ran the skill's script, which needs scipy.
- **Two defects the run exposed:**
  - **The critique read the planner's notes cut short.** Every packet clipped the coverage note at
    2,000 characters and the design's limitations at 800, though the schemas allow 4,000 and 8,000. Two
    critiques said they could not confirm a search because the note was cut.
  - **The critique trusted described searches.** C3's critique wrote "every gap accompanied by a
    recorded search" and C4's credited GraphPad and NCBI searches; those were made for C1 and C2.
- Report: `.verifier/runs/26312681-3f7c-4573-8a4b-9da8b2c41c6b/report-card.md`, outside Git.

**6. Fixes after `26312681`**, on the operator's go-ahead, contracts first:
- `local-contract.md`: the critique receives the justification and the design's scope and
  limitations whole, and **Python's search record**: every WebSearch query the planner ran, marked
  with the claim it was working on (the one its last verifier tool call named), and every reference,
  resource or asset fetch with the claim it was for and its outcome. "Tested fact by fact" says the
  critique checks each described search against it. `tool-contracts.md`'s `coverage` points there.
- Code:
  - `local.py`: `NOTE_TEXT` (8,000) and `JUSTIFICATION_TEXT` (4,000) are shared by the tool schemas
    and the packet, so the packet carries what the schema accepted. `search_record` reads the
    attempt's event files, which are written once and never replaced, and `select` puts its result in
    `python_checked.search_record`; with no workflow log it says no search was recorded.
  - `documentary.py`: rubric v10 → v11, judging a search by `python_checked.search_record` ("the
    justification only describes searches, and one the record does not show was not made").
    `CRITIC_PACKET_LIMIT` goes from 160,000 bytes to 512 KiB: the largest packet the schemas allow is
    about 500 KB, so even the old limit never covered it.
- Verification:
  - Suite 426 → 429 tests, 427 passing and 2 skipped. New: the record read from a real
    `WorkflowLog` through `select`, attributing searches to this claim, another claim or none yet,
    reading a refused fetch, reporting results in no expected shape rather than failing the
    selection, and ignoring a subject's stream; the notes reaching the packet whole; and the
    schemas' largest packet, 500,611 bytes, under the limit.
  - Sizes: the pinned `local-contract.md` is 39,288 of its 40,960 bytes; the verification bootstrap
    is unchanged at 199,970.
  - **Packets rebuilt** from `26312681`'s journal, store and attempt log with today's code matched
    what was sent in everything but the rubric, the whole notes and the new record. The record showed
    8 searches when C3 and C4 were proposed, none of them while working on either.
  - **Live recording**, $0.43: `d416f79d`'s packet under v11, with its limitations whole and no log,
    settled at B with all three cases counted, as under v8 to v10. Its first reply added a stray
    `StructuredOutput` key, which Claude Code refused and the session resent.
  - **Replays** of `26312681`'s rebuilt packets under v11, $2.78: C1 once, C2's first round once, C3
    and C4 twice each, against the run's own v10 critiques. No grade moved: A, B, B, B. Every coverage
    finding used the record, for example C4's "search_record shows no query using any term for it
    (no 'plateau', 'incomplete curve', 'extrapolated IC50')". C2's first-round critique turned it into
    required revisions: "record an actual search for a source stating a minimum number of
    concentrations; the current search record contains none", and correct the justification's search
    narrative to match the record. C3's and C4's grades equal their proposals, so they required
    nothing (open question 4). Verdicts moved by one case in three samples: C2's first round judged a
    second case `leaked`, one C3 sample a case `duplicate` and one C4 sample a case `beyond_scope`;
    none changed a grade.
  - Not verified: any of this in a run.

### Decisions taken 2026-09-30

- **Fix the planner's and the reviewer's instructions** (operator), rather than cut claims down to
  their cases or add Python checks first.
- Proposed here and built: the two "Claims" rules, step 4, fact-by-fact `coverage`, the quote
  message and rubric v10.
- **Held back** at first: Python refusing an accept while replacement rounds remain, and returning a
  plan fixed at a low ceiling to the planner when its critique names a gap, until a run showed the
  text alone did not hold.
- **After run `26312681`** (operator: "yes, do both fixes and record the run"): the critique reads
  the planner's notes whole and judges searches by Python's search record, under rubric v11, with
  the packet limit raised to fit. This replaces the first half of what was held back with something
  narrower: the critique sees the searches, rather than Python refusing the planner anything.
- **Still held back:** refusing an early accept, which `26312681` never attempted, and returning a
  plan fixed at its own proposal to the planner (open question 4).

### Open questions for the operator

1. The 2026-09-29 entry's open questions stand. Question 5 is narrowed, not settled: the planner and
   reviewer now push coverage up, but whether A needs every fact a claim states tested stays open.
2. **The fitting step cannot run.** Step 2 needs the ToolUniverse `tu run` tools or the skill's
   scipy script, and the skill declares neither. A fenced `pip install numpy scipy` in the
   submission would let a claim on fitting execute; that is a change to the submission, not the
   verifier.
3. **More cases cost trials.** At three trials a case, the 128-call budget holds 42 cases a run.
   `fbd49132` and `26312681` each used 60 calls for 20 cases, and testing each fact could double that.
4. **A plan fixed at its own proposal never returns to the planner.** C3 and C4 of `26312681` were
   designed at B's minimum and settled at once. With the search record their critiques can name the
   facts no search sought, but only in the report. Returning such a plan to the planner, once and
   within its rounds, when its critique names such facts would make the search rule bite. It changes
   when `select_local_candidate` returns `local_grade_revision_required`.
5. **The planner hurries.** It wrote "moving quickly" before C4 of `26312681`, and accepted B in
   `fbd49132` "rather than spend the remaining time", though neither run used 56 of its 120 minutes.
   It is never told its deadline, and "Claims" still says a six-claim run used all but 8 seconds of
   its 90 minutes. Telling it the deadline and the time used might remove the pressure.
6. **C2's A rests on the AI reader.** Two of its 15 counted trials passed only because the reader
   judged "ic50" to match the `exact` key "IC50". This bears on the 2026-09-29 entry's question 1.

### Urgent next steps, if any

None. Committed and pushed on `skill-environments` with this entry.

### Suggested next move

Run tooluniverse-dose-response a third time once the 5-hour window allows, to see v11 and the whole
notes live against `26312681`; then decide open questions 4 and 5.

### Recommended next action

With the operator's go-ahead:
1. Move, do not delete, into the session scratchpad:
   - `.verifier/runs/26312681-3f7c-4573-8a4b-9da8b2c41c6b`
   - `.verifier/attempts/dc3fa47d-0ec7-4371-9c76-52dc9fa3576d`
   - `.verifier/subject-runs/26312681-3f7c-4573-8a4b-9da8b2c41c6b`
   - the ten candidates it wrote, dated 2026-09-30, 17:05 to 17:49

   Keep the glycoengineering run, its attempt, subject-runs and five candidates, and
   `.verifier/store/`. `fbd49132`'s files, 3,224 of them and its nine candidates, were moved on
   2026-09-30 to `cleaned-fbd49132` in scratchpad `c7991202…`; `d3892f6c`'s, 4,230 and nine, on
   2026-09-29 to `cleaned-d3892f6c` in scratchpad `8784dcda…`.
2. Start a new Code-tab session, so that `serve-local` starts after this commit, and check Docker and
   the 5-hour window as the 2026-09-28 entry says; `26312681` took 41 points of it.
3. Run tooluniverse-dose-response.

Record, against `26312681`: whether each critique's coverage finding uses the search record; for each
claim, the facts stated and tested and the WebSearch queries made while working on it; any claim
designed below A with no search, and whether its critique names the facts no search sought; each
critique's required revisions and whether the next design answered them; the grades; and run time
against 7,200 s and subject calls against 128. It is finished when each has a recorded answer.

## Claude: 2026-10-01 (runs 3303fd93 and 1d1c3b6e; a plan that settles at its own proposal comes back, and the planner is told its time)

### Current stage and status

Version 0.7.0, local workflow, on `skill-environments`. Run `3303fd93` used the 2026-09-30 fixes
(`66ff13e`): every critique judged the planner's searches by Python's record and named what was left
untested. The planner still built three claims to B's minimum, and their critiques agreed with B, so
those findings reached only the report. On the operator's go-ahead, two returns are now built
(`1ae07f8`, then section 3), both for a critique that agrees with a proposal below A:
- **the coverage-gap return**, once per claim, when the critique names coverage gaps;
- **the concern return**, while rounds remain, when the next critique, now shown every revision an
  earlier one required, judges one unanswered. That critique is the AI judge, as the operator asked;
  Python checks its `searched_no_source` verdicts against the search record.

After either return the grade is accepted only once Python's record shows a new search for the claim.
Both were replayed live (sections 2 and 3).

Run `1d1c3b6e` (section 4) used them, and **neither fired**: the planner proposed A in every round,
and both need a critique that agrees with a grade below A. It settled C1 at A and C2 and C3 at B.
C4 got a documentary D with no design, the planner saying its deadline was near with 62 of 120
minutes left. On the operator's go-ahead two fixes are built (section 5):
- every reply to the planner states the seconds it has left;
- the search record reads fetches from Python's own record of each call. This run's record had
  called five of ten successful fetches unreadable.

Neither fix is yet seen in a run, and neither return has yet fired in one.

### What has been done

This session, 2026-10-01:

**1. Run `3303fd93`**, tooluniverse-dose-response, on `66ff13e`, from a session whose `serve-local`
started at 13:41, after that commit, with `--timeout 7200`. `26312681`'s files were moved first.
- **Result.** C1 (the 4PL equation) at A; C2 (data preparation), C3 (reading the parameters) and C4
  (quality gotchas) at B; all `pass`. 48 of 48 counted trials passed and the 3 uncounted ones too;
  none invalid, missing or refused; every case unanimous.
- **The AI reader decided 8 trials.** In C2, "ic50" for the `exact` key "IC50" (2). In C4, "Cheng-Prusoff
  correction" for the term key "Cheng-Prusoff" (3), and "wider concentrations" for "concentration
  range" (3); the skill's own words are "recommend wider concentrations", so that key was the
  planner's paraphrase. By Python's reader alone C2 is 7 of 9 and C4 6 of 12, both `fail`.
- **Time and cost.** 2,791 s of 7,200, and 51 of 128 subject calls. About $18.04 at API rates: the
  planner $12.56 over 47 turns, 51 subjects $2.15, 5 critiques $2.67, 36 claim-only sessions $0.53 and
  10 readings $0.13. The 5-hour window went from 5% to 41%.
- **The new code ran.** `local_method_ref` equals the tree's digest, `578b3c4c…`; the critiques carry
  rubric v11 and a search record.
- **Against `26312681`, as the 2026-09-30 entry asked:**
  - every critique's coverage finding used the record. C3's, for example: "the record shows no search
    aimed at curve completeness for this claim", and of Emax and Emin, "the Prism variable-slope page
    (fetched twice, once for this claim) … bear[s] on Top/Emax, so a case here was available";
  - facts tested, from each critique's list: C1 3 of 6, C2 2 of 7, C3 3 of about 12, C4 2 of 5
    gotchas;
  - WebSearch: C1 7 queries, C2 2, **C3 and C4 none**; those two fetched two pages each by URL;
  - claims designed below A: C2 with 4 cases (6 in `26312681`), C3 with 3 (4), C4 with 3 then 4. C2
    and C3 were proposed at B, agreed and fixed at once, so their critiques could ask for nothing;
  - C4's first critique supported C below a proposed B and required five revisions. The next design
    replaced the leaked case and restored the case count, and **skipped the sparse-sampling and
    biphasic cases** it also required, with no search;
  - C2's first proposal was refused for `prior_review_in_packet` and spent no session;
  - grades 1 A + 3 B, against 2 A + 2 B; time 2,791 s against 3,328; subject calls 51 against 60.
- Report: `.verifier/runs/3303fd93-9621-42bc-8253-ea2115cc2709/report-card.md`, outside Git.

**2. The coverage-gap return**, on the operator's go-ahead ("yes, build it and record the run"),
contracts first:
- `tool-contracts.md`, `select_local_candidate`, owns it. Once per claim, a critique whose settled
  grade equals a proposal below A and that names `coverage_gaps` returns
  `local_grade_revision_required` with those gaps instead of fixing the plan. A revised design is
  critiqued as usual and never returned for gaps again. Accepting the returned design's grade is
  refused as `gaps_unsearched` until Python's search record shows a search or fetch for the claim
  since the return; with no workflow log there is nothing to check and acceptance stands. The
  critique's reply gains `coverage_gaps`.
- `workflow.md`'s local transition for `select_local_candidate` and `local-contract.md`'s negotiation
  paragraph point to it, in the same commit.
- Code:
  - `documentary.py`: rubric v11 → v12, asking for those gaps in `coverage_gaps` whatever the grade;
    the reply schema gains the field.
  - `local.py`: `select` makes the return and the acceptance check; the search record counts this
    claim's searches and fetches over the whole stream, not the listed 100; the gap return is a
    stored object, `gap_return_ref`, as every claim work field must be; the next critique is told the
    earlier gaps among the concerns it checks; the report prints each coverage gap and says when a
    claim came back.
  - `local_entry.py`: the planner prompt's step 4 names the return.
- Verification:
  - Suite 429 → 433 tests, 431 passing and 2 skipped. New, through `select` with a stand-in critique:
    an agreeing critique with gaps sends a B plan back once; accepting at once is refused as
    `gaps_unsearched` (renamed `return_unsearched` in section 3, which shares it); after one recorded
    search the same grade is accepted with no new session, and
    the report prints the gap and the return; a revised design with gaps left is fixed, with the
    earlier gaps among its critique's concerns; a plan at A, or with no gaps, is fixed at once; with
    no workflow log the returned grade is accepted.
  - Sizes: the pinned `local-contract.md` is 39,514 of 40,960 bytes and `tool-contracts.md` 26,494; the
    verification bootstrap is unchanged at 199,970 of 200,000.
  - **Live recording**, $0.40: `d416f79d`'s packet under v12 settled at B with all three cases counted
    and no coverage gaps, every fact of that claim being tested. Its first reply added a stray
    `evidence_limits` key, which Claude Code refused and the session resent.
  - **Replays** of `3303fd93`'s C2, C3 and C4 (second round) packets, rebuilt with today's code and
    matching what was sent apart from the rubric and the record's new counts, $1.68. C3 settled at B,
    its proposal, with 8 `coverage_gaps` (the Hill-slope and r² thresholds, Emax, Emin, the tested-range
    rule and fold-shift), and C4 at B with 5, among them the sparse-sampling and biphasic gotchas its
    first critique had required. **Under today's code both would come back to the planner.** C2's
    sample judged one more case `leaked`, so it would settle below its proposal and take the ordinary
    revision path, with 5 required revisions and 6 gaps.
  - Not verified: any of this in a run.

**3. The concern return**, on the operator's go-ahead ("let AI reader do the job"; then "build it and
do all tests you need"). A revision could answer some of the revisions its critique required and still
settle, as C4's did here and in `fbd49132`, because the next critique was never shown the required
revisions (only objections and rejected cases), and its prose answer to "is each concern answered"
changed nothing. Contracts first:
- `tool-contracts.md`, `select_local_candidate`: the critique receives earlier required revisions and
  coverage gaps among its concerns and gives each a verdict in `prior_verdicts`: `answered`,
  `searched_no_source`, `unanswered` or `no_longer_applies`. *The concern return*: while rounds
  remain, a critique agreeing with a proposal below A that judges a concern `unanswered` returns
  `local_grade_revision_required` with `unanswered_concerns`. A `searched_no_source` verdict stands only
  when Python's search record shows a search or fetch for the claim since the previous critique;
  otherwise Python counts the concern unanswered, as it overrules an AI reading its own reader settles
  the other way. Both returns share one refusal, `return_unsearched`.
- `workflow.md`'s local transition and `local-contract.md`'s packet and negotiation paragraphs follow.
- Code:
  - `documentary.py`: rubric v12 → v13, with `prior_verdicts` and criterion 5 pointing to it; the reply
    schema holds exactly one verdict per concern; each stored verdict carries the concern it judges.
  - `local.py`: earlier required revisions join the concerns; each critique stores Python's search
    count and `unanswered_concerns` after that check; `select` makes the return, kept as
    `concern_return_ref`, and the acceptance check covers both returns; the report prints each
    concern left unanswered and says when a claim came back for one.
  - `local_entry.py`: step 4 of the planner prompt names both returns.
- **The critique's deadline**, owned by `local-contract.md`, goes from five minutes to ten, and each
  concern's reason is held to one sentence. Live critiques took 90 to 210 seconds before v13, and both
  first v13 replays of a packet carrying eleven concerns ran past five minutes, which in a run would
  end the claim as an operational failure.
- Verification:
  - Suite 433 → 438 tests, 436 passing and 2 skipped. New, through `select`: an agreeing critique that
    finds a carried required revision `unanswered` sends a B plan back, and the second critique is
    shown "An earlier review required: …"; accepting at once is refused as `return_unsearched`, and
    after a recorded search accepted; the report prints the concern and the return; a
    `searched_no_source` verdict with no search since the previous critique is counted unanswered, and
    with one it stands; an answered request, or a plan at A, settles at once. The reply schema refuses
    a missing, extra or unknown verdict.
  - Sizes: the pinned `local-contract.md` is 39,772 of 40,960 bytes; the verification bootstrap is
    unchanged at 199,970 of 200,000.
  - **Live recording**, $0.31: `d416f79d`'s packet under v13 settled at B with all three cases counted,
    no gaps and no earlier concerns, in 76 s. Its first reply added a stray `StructuredOutput` key,
    which Claude Code refused and the session resent.
  - **Replays**, $3.55 for the five that completed (the two that timed out left no cost record):
    `3303fd93`'s C4 second round, rebuilt with today's
    code and now carrying the first round's five required revisions, in three samples (154 to 200 s).
    **Each judged the same three unanswered**, the sparse-sampling case, the biphasic case and
    broadening c2's synonyms, with the objection behind the last, and the two the planner made
    `answered`. Under today's code C4 would come back with four unanswered concerns as well as its gaps.
  - **Negative control**: `26312681`'s C2 second round, whose revision answered all four requests.
    Both first samples ran past five minutes; under the final rubric they took 291 and 218 s. Three
    requests were `answered` and the fourth, "record the search that failed" for the point count,
    `searched_no_source`, which Python's check overrules because that search came before the request.
    Neither sample would return the claim: one supported A, the other B below the proposed A.
  - Not verified: any of this in a run.

**4. Run `1d1c3b6e`**, tooluniverse-dose-response, on `f469ad6`, from a session whose `serve-local`
started at 18:45, after that commit, with `--timeout 7200`; `local_method_ref` is `dcfadc5e…`.
`3303fd93`'s files, 2,862 and six candidates, were moved first, to `cleaned-3303fd93` in scratchpad
`c7991202…`.
- **Result.** C1 (the 4PL model) at A; C2 (data preparation) and C3 (reading the parameters) at B,
  all `pass`; C4 (quality gotchas) at D, `inconclusive`, with no design. 51 of 51 counted trials
  passed, all by Python's reader; the AI reader decided none. Of 3 uncounted trials, 1 passed.
- **Rounds.**
  - C1: A → B (4 counting cases, one `leaked` and one `beyond_scope`), then A → A.
  - C2: A → B three times, a case `leaked` each round (`c2_x_values` twice), fixed at B by the
    round limit.
  - C3: A → B, with 5 coverage gaps and 5 required revisions. After one search the planner wrote
    "Time is tight" and accepted B. Two of those revisions pointed at pages it had already fetched.
- **No return fired.** Every proposal was A, so no critique agreed with a grade below A, and no
  acceptance was refused as `return_unsearched`.
- **The concern verdicts ran.** C1's second critique judged 16 earlier concerns, and C2's second and
  third 16 each. In C2's third, Python counted 5 `searched_no_source` verdicts unanswered, there
  being no search since the round before. Neither changed a grade: C1 settled at A, and C2 ran out
  of rounds.
- **C4.** At 57 minutes the planner wrote "With the attempt deadline near, I'll secure claim 4 via the
  documentary path", with 62 of its 120 minutes left. It fetched one page; its first assessment was
  refused for an inexact quote; the assessor found that page short of the claim. The documentary
  path was legal there (`workflow.md`, the local transitions: a lookup and one retrieved reference),
  as the operator accepted for `84e90683`. The planner was never told its deadline, and
  `local-contract.md` told it a six-claim run "used all but 8 seconds of its 90 minutes".
- **Search record.** WebSearch: C1 4 queries, C2 2, C3 1, C4 none. Fetches: 5, 3, 1 and 1. **Five
  of the ten fetches showed as "unreadable result"**: each reply was over 16,000 characters, the
  workflow log keeps that much of the planner's copy, and the record parsed that copy. The critiques
  of C1 (round 1), C2 (round 3) and C3 then asked the planner to reconcile its fetches or its
  provenance text with the record.
- **Facts tested**, from each final critique's list: C1 6 of 10, C2 5 of 8, C3 5 of about 10.
- **Time and cost.** 3,583 s of 7,200, and 54 of 128 subject calls. About $23.0 at API rates: the
  planner $15.14 over 50 turns, 54 subjects $2.33, 6 critiques $4.52 (165 to 261 s each), 50
  claim-only sessions $0.82, 3 readings $0.05, the assessor $0.12. The 5-hour window went from 3%
  to 49%.
- **Against `3303fd93`:**
  - grades 1 A + 2 B + 1 D, against 1 A + 3 B;
  - AI-reader trials 0, against 8;
  - every design proposed at A, against B for C2 and C3;
  - facts tested: C1 6 of 10 (3 of 6), C2 5 of 8 (2 of 7), C3 5 of about 10 (3 of about 12);
  - WebSearch for C3 1 query, against none; for C4 none in either.
- Report: `.verifier/runs/1d1c3b6e-7d26-4a9e-b6db-59af72c207ee/report-card.md`, outside Git.

**5. The planner's clock and the search record**, on the operator's go-ahead ("yes, build both fixes
and record the run"), contracts first:
- `local-contract.md`, "Acceptance", owns the clock. Every reply to the planner carries
  `attempt_seconds_remaining`, the whole seconds left before the planner is stopped. "At most five"
  no longer says "90 minutes". `tool-contracts.md`'s "Local profile tools" points to it.
- `local-contract.md`'s critique paragraph: the search record's fetches, and their outcomes, are
  Python's own record of each call.
- Code:
  - `local_entry.py`: `BoundRuntime` adds the field to every reply, refusals included. It is
    computed from the deadline the runner already gives the planner's tool server for the end-of-run
    re-run. The planner prompt says to judge time by it, never by a guess.
  - `local.py`: `search_record` reads each fetch from the `tool_started` and `tool_finished` events
    Python writes for the call, and WebSearch queries and their claim from the planner's stream as
    before. A call that never reached Python's tools fetched nothing. A page's size is no longer
    printed: Python's call record does not hold it, and it appeared only for pages over 40 KiB.
- Verification:
  - Suite 438 → 439 tests, 437 passing and 2 skipped.
    - New: every reply through `BoundRuntime`, a refusal included, carries the seconds left. The
      value is 0 past the deadline, and the field is absent with no deadline or an unreadable one.
      The prompt and the pinned contract name it.
    - The search-record test now records its fetches through `recorded_call`: a reply over 16,000
      characters, still `reference_fetched`; a refusal; a raised fault; a call that never reached
      Python; and malformed events.
  - **On this run's own log**, the new record reads all ten fetches as `reference_fetched`, where
    the old one read five as unreadable. The counts per claim are unchanged.
  - Sizes: the pinned `local-contract.md` is 40,281 of 40,960 bytes, and the verification bootstrap
    is unchanged at 199,970 of 200,000. The `tool-contracts.md` pointer, first put in its common
    protocol, which that bootstrap pins, took it past 200,000; it now sits in "Local profile tools".
  - The rubric did not change, so nothing was re-recorded.
  - Not verified: either fix in a run.

### Decisions taken 2026-10-01

- **Build the coverage-gap return** (operator), answering open question 4 of the 2026-09-30 entry.
- Proposed here and built: only below A, since A is the strongest grade and its critique judged
  the coverage enough; once per claim; acceptance afterwards needs a new search or fetch in Python's
  record; the gaps travel to the next critique; the report discloses the return.
- **Build the concern return with the next critique as the AI judge** (operator). Proposed here and
  built: the critique, not a separate reader, since it already reads the old concerns beside the new
  design; below A only; while rounds remain rather than once, since each round costs a critique and
  the round limit bounds it; Python checks `searched_no_source` against its record; one refusal reason
  for both returns. `gaps_unsearched` became `return_unsearched` before any run used it.
- **Tell the planner its time, and read fetches from Python's record** (operator), after run
  `1d1c3b6e`. Proposed here and built: the time goes in every reply, not the prompt alone, since a
  session sees no clock; there is no field when nothing bounds the attempt or the deadline cannot be
  read, so a bad value never fails a reply; the page size leaves the record.
- **Not built:** a check on accepting a lowered grade (open question 4).

### Open questions for the operator

1. The 2026-09-30 entry's questions 1 to 3, 5 and 6 stand; question 4 is answered above.
2. **The AI reader now decides grades.** C2 and C4 pass only through it, and "wider concentrations"
   for "concentration range" is a paraphrase, not a format difference (2026-09-29, question 1). In
   `1d1c3b6e` it decided no trial.
3. A revision answering only some required revisions is now answered by the concern return (section
   3). **Its search check is strict:** a request answered by recording a search made before it was
   raised still needs a new search before the grade is accepted, one search call at worst. The
   negative control met exactly this, harmlessly. Relaxing it to any search for the claim would let a
   planner cite searches made for other facts.
4. **A lowered grade can still be accepted at once.** The returns guard only a critique that agrees
   with a grade below A. A planner that proposes A and accepts the B it is given passes neither, as
   C3 of `1d1c3b6e` did with five required revisions unanswered. Requiring a new search would not
   have stopped it, since it made one. Whether the clock is enough is for the next run to show.

### Urgent next steps, if any

None. Committed and pushed on `skill-environments` with this entry.

### Suggested next move

Run tooluniverse-dose-response again, so the planner works with its clock, and see whether every
claim gets a design and whether a lowered grade is still accepted at once.

### Recommended next action

With the operator's go-ahead:
1. Move, do not delete, into the session scratchpad:
   - `.verifier/runs/1d1c3b6e-7d26-4a9e-b6db-59af72c207ee`
   - `.verifier/attempts/9b34b883-422f-4918-a717-10f4c36b8dcd`
   - `.verifier/subject-runs/1d1c3b6e-7d26-4a9e-b6db-59af72c207ee`
   - the eight candidates it wrote, dated 2026-10-01, 18:58 to 19:40

   Keep the glycoengineering run, its attempt, subject-runs and five candidates, and
   `.verifier/store/`. `3303fd93`'s files, 2,862 and six candidates, were moved on 2026-10-01 to
   `cleaned-3303fd93` in scratchpad `c7991202…`.
2. Start a new Code-tab session, so that `serve-local` starts after this commit (the run's
   `local_method_ref` is then `cb7ef8a4…`), and check Docker and the 5-hour window as the 2026-09-28
   entry says.
3. Run tooluniverse-dose-response.

Record, against `1d1c3b6e`:
- the `attempt_seconds_remaining` the planner saw when it finished each claim, accepted a lowered
  grade or took the documentary path, and whether every claim got a design;
- each coverage-gap return and concern return, with the concerns judged unanswered and any
  `searched_no_source` verdict Python overruled, and what the planner did after each;
- the fetch outcomes in the critiques' search record;
- the facts tested and WebSearch queries per claim, the grades and the trials the AI reader decided;
- run time against 7,200 s and subject calls against 128.

It is finished when each has a recorded answer.

## Claude: 2026-10-02 (run 90c60cbe; one false fail, and a bar for changes so that fixes do not overfit)

### Current stage and status

Version 0.7.0, local workflow, on `skill-environments`. Run `90c60cbe` used the 2026-10-01 fixes
(`ddc5f84`) and settled all four claims at A, a first for this skill. C1's status is `fail` on one
case, whose question, not its key, was at fault. The operator raised a concern that fixes drawn
from single runs overfit. The records support it, so no fix is made for that case, and a bar for
future changes is recorded below. The two returns built on 2026-10-01 have not fired in any run
since.

### What has been done

This session, 2026-10-02:

**1. Run `90c60cbe`**, tooluniverse-dose-response, on `ddc5f84`. Its session's `serve-local` started
at 23:01 on 2026-10-01, after that commit, with `--timeout 7200`. `1d1c3b6e`'s files had already
been moved, at 20:44 on 2026-10-01, to `cleaned-1d1c3b6e` in scratchpad `d9761800…`, so nothing was
moved. The Western-blot run `32e60bd6` was left in place, as the operator asked.
- **Result.** C1 (the 4PL model) at A, `fail`; C2 (data preparation), C3 (reading the parameters)
  and C4 (quality gotchas) at A, `pass`. 57 of 60 counted trials passed, and every case was
  unanimous. The AI reader decided one trial, "Cheng-Prusoff correction" for the term key
  "Cheng-Prusoff", in C4. By Python's reader alone C4 is 14 of 15, `fail`.
- **Rounds.** C1 and C2: A → A. C3 and C4: A → B, then searches and a revised design, then A → A.
  Two proposals were refused as `prior_review_in_packet`, and two fetches sent in parallel as
  `illegal_transition`. No return fired.
- **The clock worked.** Every reply carried `attempt_seconds_remaining`: 7,068 s at the first lookup,
  3,042 s at the last selection. The planner designed and ran every claim, made no remark about
  time, and ended with about 2,830 s left.
- **The search record worked.** Every critique's record showed each fetch's outcome:
  `reference_fetched`, or `refused: illegal_transition` for the parallel calls. No critique asked
  to reconcile the record.
- **Against `1d1c3b6e`'s list:** facts left untested per final critique 2, 2, 3 and 3; WebSearch
  queries 5, 3, 2 and 2 (C1's include 2 made for C2 before the planner named that claim); fetches
  4, 6, 6 and 4; earlier requests judged unanswered at the final round, both at A, 2 in C3 and 4
  in C4; grades 4 A against 1 A, 2 B and 1 D.
- **Time and cost.** 4,371 s of 7,200, and 78 of 128 subject calls. About $29.6 at API rates: the
  planner $20.70 over 66 turns, 78 subjects $3.38, 6 critiques $4.47 (101 to 297 s each), 58
  claim-only sessions $0.98, 6 readings $0.10. The 5-hour window went from 3% to 60%, the most for
  this skill.
- Report: `.verifier/runs/90c60cbe-4ffd-44f1-8e2c-c2122af3e5d6/report-card.md`, outside Git.

**2. Why C1 failed: one case, a false fail.** `dr1_agonist_measure` asked "Which half-maximal
concentration parameter does the fit report for that activation curve?". Its key was `EC50`, of
type `exact`.
- **The key is right.** SKILL.md says "'IC50' for inhibition, 'EC50' for activation".
- **The question is at fault.** SKILL.md also says the tool "Returns `ic50`, …" for any curve, and
  the `exact` format line asks for "the exact token, written as it appears in code or data". All
  three subjects answered `ic50`, each adding that the value is read as the EC50 for an agonist; two
  searched the skill's scripts for the token first. The claim-only sessions got the same question
  and format line, had no skill, and answered `EC50`.
- **The process could not see it.** The critique and the claim-only sessions see the claim, not the
  skill. The AI reader read the replies correctly as `differs`. Under the unanimity rule one case at
  0 of 3 fails the claim; without it C1 is 12 of 12. Its grade stands either way.
- **The other two misses were handled as designed.** In C3, `dr3_range` keyed an option that is
  GraphPad's sentence with its condition ("If the top plateau is not defined…") cut, so it reads as
  "curve fitting is useless". Subjects and claim-only sessions all chose "none of these", and
  Python's claim-only check dropped the case, which the critique had counted against its own
  rubric rule. In C4, `dr4_cheng` was the AI reader's trial above.

**3. The overfitting check**, after the operator's concern:
- Across the 10 runs whose records are kept (166 counted cases on sar-analysis, scikit-survival,
  glycoengineering, western-blot-quantification and five dose-response runs), only
  `dr1_agonist_measure` has claim-only sessions reaching a key that every subject missed.
- Since the `exact` format line was added in `73496d6`, 10 other `exact` cases, in the 5 of 7 runs
  that used the type, passed all 30 of their trials.
- In the three runs since the two returns were built, `1d1c3b6e`, `90c60cbe` and `32e60bd6`, every
  proposal was A except two acceptances of a lowered B, one in `1d1c3b6e` and one in `32e60bd6`.
  `32e60bd6` was run from another session and is not recorded here. An acceptance runs no
  critique, so neither return could fire. The acceptances are the 2026-10-01 entry's open
  question 4.
- So neither proposed fix was built: a planner rule against asking what a tool "reports", and a
  reworded `exact` format line.
- The scan is `divergence.py` in scratchpad `c7991202…`; it ran no model session.

### Decisions taken 2026-10-02

- **A bar for changes** (operator: "yes, record it in the plan"):
  - fix a bug or a missing fact at once, as the search record and the clock were fixed;
  - change a planner, critique or reader rule only for a failure seen on at least two skills, and
    check the change against kept runs of other skills before adopting it;
  - run the next verifications on skills other than tooluniverse-dose-response.
- **No fix for `dr1_agonist_measure`.** It is a recorded false fail. A rule waits until the same
  pattern, claim-only sessions reaching a key every subject misses, appears on a second skill.
- **The returns stay, and nothing like them is added.** They are judged after runs on other skills.
  If they still never fire, they are complexity the workflow does not need.

### Open questions for the operator

1. The 2026-10-01 entry's questions 2 to 4 stand. Question 4, a lowered grade accepted at once, came
   up again in `32e60bd6`.
2. Keep or remove the two returns, after the next runs on other skills.

### Urgent next steps, if any

None. Committed and pushed on `skill-environments` with this entry.

### Suggested next move

Verify a skill other than tooluniverse-dose-response on `ddc5f84`, to see whether the recent rules
hold away from the skill that produced them.

### Recommended next action

With the operator's go-ahead:
1. Choose a skill other than tooluniverse-dose-response.
2. Move, do not delete, into the session scratchpad:
   - `.verifier/runs/90c60cbe-4ffd-44f1-8e2c-c2122af3e5d6`
   - `.verifier/attempts/462b41d5-ad18-4937-bde6-5102d1bdaf48`
   - `.verifier/subject-runs/90c60cbe-4ffd-44f1-8e2c-c2122af3e5d6`
   - the ten candidates it wrote, dated 2026-10-02, 01:30 to 02:26

   Leave the Western-blot run `32e60bd6`, its attempt `350bcb4c…`, its subject-runs and its eight
   candidates (2026-10-01 23:52 to 2026-10-02 00:54) to the operator. Keep the glycoengineering run,
   its attempt, subject-runs and five candidates, and `.verifier/store/`.
3. Use a session whose `serve-local` started after `ddc5f84` (its runs' `local_method_ref` is
   `cb7ef8a4…`), and check Docker and the 5-hour window as the 2026-09-28 entry says. A run has
   taken up to 63 points of that window.
4. Run the chosen skill.

Record: any case where claim-only sessions reach a key that every subject misses, and why; whether
either return fires; how many lowered grades are accepted at once; the time left as the planner
ends each claim; grades, statuses and the trials the AI reader decided; run time against 7,200 s
and subject calls against 128. It is finished when each has a recorded answer.

## Claude: 2026-10-05 (an HTML page after every run; the final reviewer planned; whole-skill task tests built; question tests removed, 0.8.0; a recorded task critique)

### Current stage and status

Version 0.8.0, local workflow, bumped in section 6. `skill-environments` was merged into `main` and
deleted, and the work since is on the new branch `whole-skill-tests`, which is the operator's to merge. Every completed run
gets one web page, made from its records, for the operator and the lab, unless the user asks for
none (section 3); the agent that asked for the verification writes its plain-language summaries. A
final reviewer is planned, not built (section 2).

The whole-skill test design (section 4) is **built** (section 5). A skill is split into claims that
are groups of whole sections, nothing left out, and each claim is tested by tasks: the test AI gets
the whole skill, input files and a job, and writes `results.json`, which Python checks against values
it built into the files from a referenced model, or quoted from a reference. Python proves each task
fair first by running the planner's own reference solution. Question tests are removed, a wrong result
now outweighs an unreadable one, and the operator's image has scipy (section 6). Checked by the suite,
by the container steps run live, and by one live test session and one live task critique, which both
worked. **No live verifier run has used task tests.** Starting one needs the operator's go-ahead and a
new Code session.

### What has been done

This session, 2026-10-05:

**1. The HTML run report**, on the operator's request ("Now build the html … we will test the html
first").
- `scripts/report_html.py RUN` writes `.verifier/reports/<run>.html`. The page is one file with no
  scripts and no outside styles. Every recorded string is escaped, and only `http(s)` sources become
  links.
- It reads only the run's records:
  - the report card;
  - the run journal, for grading rounds and time per claim;
  - the workflow log, for session costs and Python's search record;
  - the store, for designs and sources.

  A part that is missing leaves its figure blank.
- The page follows the operator's outline:
  - the skill in plain words, with its sections and the claim that tested each, folded when there
    are more than ten;
  - a summary table, one row per claim: grade, status, answers right, agreement, tests and trials
    counted, AI-reader passes, grading rounds, searches and fetches, facts left untested, time and
    cost;
  - one chapter per claim:
    - a plain description and a summary;
    - a table with one row per test;
    - one fold holding each test's full question, answer format, key, source quote, reviewer
      verdict, claim-only answers and every try, plus the sources, grading rounds, untested facts
      and the planner's recorded limits;
  - cautions and limitations;
  - how to read the page.
- The plain-language text comes from a notes file, `.verifier/reports/<run>.notes.json`: the skill
  summary, claim descriptions and summaries, what each test asks, review notes and cautions. The page
  marks it "✎ written by Claude" and says it is not part of the scored record. I wrote run
  `90c60cbe`'s notes in this session. The final reviewer is to write into the same file.
- Checked on every kept run that has a report card: `90c60cbe` with notes, and without notes
  `32e60bd6`, `1d1c3b6e` (one documentary claim), `3303fd93`, `26312681`, `fbd49132`, `d3892f6c`,
  `0aeca4c6` and `d416f79d`. `32e60bd6`'s page was written outside its run, which was left untouched.
  Five kept runs have no report card: four kept only their event logs, and `4a8c380d` stopped at the
  usage limit with a partial report. For those the script says so.
- Read in Edge at 1,400 px, every column shows, and each fold opens to readable text.
- `LOCAL-INSTALL.md` tells the operator how to make the page.
- Verification: suite 439 → 444 tests, 442 passing and 2 skipped. The new tests check that:
  - a hostile reply is escaped and a `javascript:` source is never linked;
  - there is one chapter per claim and one row per test;
  - a choice key shows the option it names;
  - notes appear, marked;
  - the same records give the same page;
  - a run without a report card says it stopped early.
- Not done: stopped runs' partial reports are not rendered. That runs did not make the page themselves
  is superseded by section 3.

**2. The final reviewer, planned** (the operator: "leave the final reviewer into the dev plan").
- Decided by the operator, 2026-10-05:
  - it reviews every failed test plus a sample of passed ones;
  - a test it disputes is re-run, with the question, key or other part at fault fixed.
- Proposed here, for the build:
  - **Where and what it sees.** A fresh session after all claims ran and before the report. It sees
    the skill's own text and, for each test it reviews, the question, the answer-format line, the key
    and its source quote, the subjects' replies and the claim-only answers. The critique sees none of
    the skill; `90c60cbe`'s false fail came from the skill's own words ("Returns `ic50`") and our
    format line.
  - **It can only withdraw a verdict, never give one.** A disputed fail is `inconclusive` until the
    re-run settles it, and the first verdict stays in the record beside the review.
  - **Each finding names its fault from a short list** (the question, the key, the answer format or
    reader, the skill) with a reason.
  - **Fixes.** A fault in a question or key is fixed through the normal design path (qualification,
    critique, claim-only answers), and the claim is re-run once. A fault in our own process (a format
    line, the reader) is recorded for the developers, and the test stays `inconclusive`.
  - **It meets the 2026-10-02 bar.** False fails have come up on sar-analysis (`b43780be`,
    `3b3f3c94`) and on dose-response (`90c60cbe`).
  - **Test it first.** Run it over the kept runs before it joins the workflow: it should flag
    `dr1_agonist_measure` as a question fault and leave the true passes alone.

**3. The page after every run, summarized by the calling agent.** The operator: "I need this html
generate automatically after each run unless the user explicitly says not to in the prompt. Then the
default agent should be able to touch it and summarize the claim. Current claim description is too
long and very unreadable."
- Contracts first:
  - `local-contract.md`, which owns the public interface, now reads `verify_skill(source_path,
    html_report)`. A completed run also gets the page and a notes file for the calling agent's
    summaries, unless `html_report` is false or `--no-html` is given.
  - `LOCAL-INSTALL.md` tells the operator what is written and how to skip it.
- Code:
  - The renderer moved into the package as `report_html.py`; `scripts/report_html.py` only calls it.
  - After a completed run, `verify()` publishes, unless the caller passed `html_report` false. The
    page goes to `.verifier/reports/<run>.html`. Beside it goes an unfilled notes file: a short guide,
    then, for each claim and test, what the agent needs (the claim as written, each question, key and
    answers, the result, the facts left untested) next to empty plain-language fields. Notes already
    written are kept.
  - The tool's reply gains `html_report`: the page, the notes file, the command that redraws the
    page, and the next step. Its key sorts before the long report, so an agent sees it in the first
    lines.
  - `verify_skill` takes the optional `html_report`, and the server's instructions tell the agent to
    follow the next step unless the user asked for no page. The CLI's `verify` takes `--no-html`.
  - The schema check learned booleans.
  - A page that cannot be drawn is reported beside the result and never changes it.
- Without notes, a claim shows "No plain summary yet" and the planner's one-sentence scope, and its
  full statement (90 to 190 words in `90c60cbe`) is folded away. A test shows the sentence that asks,
  not its whole question.
- Shown working on `32e60bd6`. Publishing wrote its page and notes outside its run, which was left
  untouched. Acting as the calling agent, I filled the notes for 4 claims and 24 tests and redrew the
  page. `90c60cbe`'s page was redrawn too.
- Verification: suite 444 → 448 tests, 446 passing and 2 skipped. New tests:
  - without notes the long claim folds away and a test shows its question;
  - publishing writes the page and an unfilled notes file, and keeps notes already written;
  - `verify()` publishes after a completed run, writes nothing when told not to, and reports a page
    it cannot draw without changing the result;
  - the public tool takes an optional boolean `html_report` and refuses anything else.
- Sizes: the pinned `local-contract.md` is 40,484 of 40,960 bytes; the verification bootstrap is
  unchanged at 199,970 of 200,000.
- `src/` changed, so a run needs a session whose `serve-local` started after this commit.
- Not verified: a live run that publishes the page, and an agent following the next step unprompted.

**4. A new test design: test the whole skill by running it.** Discussed with the operator; built the
same day (section 5), where this outline's open choices are settled.
- Why:
  - **Claims cover little of a skill.** Measured by the words of `SKILL.md` in sections that had a
    claim:
    - western-blot-quantification `32e60bd6`: 13% (333 of 2,558 words; 4 of 30 sections);
    - scikit-survival `d3892f6c`: 31% (565 of 1,810; 5 of 14);
    - tooluniverse-dose-response `90c60cbe`: 73% (567 of 772; 4 of 8).

    The Western-blot skill's untested parts include Common Pitfalls (415 words), the Decision
    Framework (342), Best Practices (179) and the workflow steps for image processing, measurement,
    fold change and visualization. A claim's six or so tests and eighteen tries went as readily to a
    one-paragraph rule or a single formula as to a long section.
  - **Tests rarely run the skill.** In `90c60cbe` 10 of 78 tries used the sandbox, mostly for
    arithmetic, and none ran the skill's fitting script (no scipy). Most tests ask whether the skill
    states a fact correctly.
  - The operator: "our ultimate goal is to test if the 'whole' skill works, we are not try to debug
    the skill." The narrow-claim pattern shows on two skills, so this meets the 2026-10-02 bar.
- Decided by the operator:
  - the planner groups the whole skill into claims by topic, and Python checks that nothing is left
    out;
  - the number of claims grows with the skill's length, the planner choosing it, and the time limit
    rises to 3 hours;
  - a claim is tested as a whole, not section by section;
  - a test gives the test AI a task and checks the output: "giving an input to step 1, and check if
    the output by step 5 works".
- Proposed here, for the build:
  - **Claims.** A claim is a group of whole sections. A section with nothing to test (Metadata,
    References, an empty parent heading) is set aside with a reason, and the page lists it. Python
    refuses a manifest that leaves any section neither in a claim nor set aside.
  - **Tests are tasks:** input files, a job in plain words and a fixed output format, such as
    `results.json`. The test AI gets the whole skill, not the claim's text; the claim only decides
    which task is set. Each test names the sections it uses, and Python refuses a design that leaves
    a section of the claim unused.
  - **Expected answers come from outside the skill.** Where a model exists, Python builds the answer
    into generated data, from parameters the planner chooses, by running the planner's generator
    program in the sandbox and storing the files and the built-in values. The model must come from a
    fetched reference, never from the skill, as calculated answers already require. References stay
    the source for:
    - the model behind every generator;
    - the right response to a planted problem;
    - real datasets with published results;
    - facts and guidance with nothing to compute.
  - **Advice is tested by doing.** A planted problem, such as a curve that never levels off or
    U-shaped data, must be flagged. Each such input also holds a clean case that must not be flagged.
  - **Fair tests.** Every try gets the same input. Before a test is used, Python solves it with its
    own reference method and refuses it unless the built-in answer comes back within the tolerance.
  - **Status.** One wrong result fails the claim, and the page shows which task failed.
  - **The test computer must have what the skill needs.** A skill that cannot run as shipped is a
    finding, recorded as such.
- **Retired by this design:**
  - one claim per section, and the five-claim cap;
  - fact-by-fact coverage and the critique's coverage list;
  - the coverage-gap and concern returns.

  The claim-only check needs rethinking (open question 5).
- **Budget.** About 3 tasks per claim, 3 tries each: 9 test sessions per claim, against 18 or more
  today, though each runs longer.
  - The time limit: `__main__.py` accepts at most 7,200 s, so 3 hours needs a code change and
    re-registering with `--timeout 10800`.
  - The real limit is the 5-hour usage window, about 15% per claim today (`32e60bd6`: 4 claims,
    63%). More claims need cheaper claims first; pausing at the limit and continuing is the fallback.
- **The dose-response sketch.** `dose_sim.py` in scratchpad `c7991202…`: 2,000 simulated plates per
  case, fitted with scipy the way the skill's script does.
  - **Claim 1, "Fit an experiment and compare potency"** (When to use this, Steps 1–3).
    - Test 1's plate:
      - inhibitors A (built-in IC50 100 nM) and B (1,000 nM), Hill slope 1;
      - ten concentrations from 1.5 nM to 30 µM, three wells each;
      - vehicle and blank wells, with noise of 4% of the signal window.
    - The test AI writes `results.json`. Python checks:
      - each IC50 within ±35% of its built-in value;
      - the fold shift 10 ± 45%;
      - `more_potent` is A;
      - the Hill slope between 0.7 and 1.4;
      - no flags.
    - A correct analysis passes on 99.1% of plates (96.0% at ±25% for the IC50s and ±35% for the
      fold shift).
    - Common mistakes fail by far:
      - log10 concentrations fed to the fitter report about 2 nM for 100;
      - an inverted ratio gives 0.1 for 10;
      - µM gives 0.1 for 100.
  - **Claim 2, "Warn when the data can't give a clean IC50"** (Step 4, Honest limitations).
    - Test 2 plants C's IC50 above the tested range, and it must be flagged `incomplete_curve`. The
      skill's own script flags it on 90% of plates when the IC50 is 3× the top concentration and on
      60% at 10×; its fitted IC50 ranges from 10⁻¹⁵⁷ to 10¹⁰ nM.
    - Test 3 gives E a U-shape, and it must be flagged `biphasic`. The skill says such data will look
      poor, with a low r², but the fit kept r² ≥ 0.90 on every plate, with a bump of 25% or 45%
      above control. An AI that trusts the skill's r² sign would miss it.
  - Set aside: Related skills.
  - **As shipped, the skill cannot run offline.** Its main tool, the ToolUniverse `tu` command, is
    not on the test computer, and its script needs numpy and scipy, which the skill does not declare.

**5. The whole-skill task design, built.** The operator answered open questions 4 to 7: a task
whose answer Python builds can reach A ("if its easy that python could build it, then it could do
A"); drop the claim-only check for tasks; yes, every section of a claim must be used by a task; do
nothing about cost for now. Then: "Merge the current branch into main, delete it and then start on
a new branch and build all we have talked about, do everything by your recommendation if we haven't
discussed about."
- **Branches.** `main` fast-forwarded to `ba4eeb7` and pushed; `skill-environments` deleted locally
  and on GitHub; new branch `whole-skill-tests`, pushed. The build is commit `08a4cb5` and the
  commit carrying this entry.
- **Contracts first**, in the same commit as the code:
  - [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md), new and pinned for the
    planner (9.8 KB), owns claims and task tests;
  - [`local-contract.md`](skills/scientific-verifier/references/local-contract.md): "Claims" rewritten;
    grade A's reference rule gains planted values; claim-only answers and the returns are for
    question designs only; a task's subject input;
  - [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md): "Cases each
    grade requires" counts tasks (A at least 3 counting tasks, B and C at least 2) and gains the
    verdict `unsound`. To keep the verification profile's bootstrap under its 200,000-byte budget, the
    replay history behind the claim-only rule was cut from it; it is in the 2026-09-24 archive entry;
  - `workflow.md`'s matrix and `qualify_local_tasks` in `tool-contracts.md`, together, with
    `tasks_required`, `sections_incomplete` and `sections_unused`; `artifact-contracts.md` records;
    `LOCAL-INSTALL.md` and `LOCAL-CONFIG.md`; `CLAUDE.md` lists `local-tasks.md` as authoritative.
- **Claims.** `load_submitted_skill` numbers the sections of `SKILL.md` `S1`, `S2`, ... Each claim
  names its sections, sections with nothing to test are set aside with a reason, and Python refuses
  a manifest that leaves one out, holds one twice or names an unknown one. At most 12 claims, since
  12 claims of 3 tasks and 3 trials use 108 of the 128 subject calls; the planner chooses the number.
- **Tasks** (`qualify_local_tasks`, [`local_tasks.py`](src/sci_ai_verifier/local_tasks.py)). One to
  six tasks, each with a job, the claim's sections it uses, and one to twelve output fields of type
  number, text, boolean or set:
  - the planner's generator, implementing a model quoted from a fetched reference, runs once per task
    in the operator's image with no network, writes the input files and prints the planted values;
    a planted text, boolean or set (which compound is more potent, whether a problem is present) also
    quotes the rule it follows;
  - an output may instead quote its value from a reference, and a task may take a fetched dataset as
    an input file;
  - the planner's reference solution runs on each task, with the input the test AI gets, and every
    output must pass on its results, or the design is rejected naming each miss;
  - every section of the claim must be used by some task;
  - Python stores the files, and every trial gets the same bytes at `/task`, read-only.
- **Trials.** The test AI gets the whole skill, never the claim, and writes `/work/results.json`.
  Python reads it: a number within its tolerance (relative, absolute or 0.000001), a text or set
  ignoring case and spacing, a boolean exactly. A wrong value fails the trial; a missing file or field
  with nothing wrong is `invalid`. No AI reader reads a task. One wrong result fails the claim.
  Python also records each module or command the trial's tools reported missing, as a finding.
- **Grades and the critique.** A design whose answers are planted from a quoted model, or quoted
  token-exactly, can reach A with 3 counting tasks and 3 trials. The critique gets its own rubric,
  `local-task-critique-v1`, and the text of the claim's sections; it has no coverage list and no
  verdict per earlier concern, and there are no claim-only answers and no coverage-gap or concern
  returns for tasks. The question rubric, v13, is untouched, so its recorded replies stay exact.
- **What no longer runs on this machine.** With a container configured, `qualify_local_candidate` and
  `qualify_local_evaluator` are refused as `tasks_required`, so question designs, calculated answers
  and generated evaluators go unused. Their code and contracts stay for a setup without a container
  and for reading old runs; two integration tests exercise them with the rule switched off. A task
  design cannot yet be exported to a catalog.
- **Time and limits.** `__main__.py` accepts up to 10,800 s, and I re-registered the user-scope
  connection with `--timeout 10800`, every other argument and the token placeholder unchanged
  (checked in `~/.claude.json`). The default per-session limit rose from 120 to 600 s, and I changed
  the operator's `.verifier/local-settings.json` to 600 likewise (the previous file is saved in the
  scratchpad of session `c7991202`); a task session gets 40 turns instead of 24; the end-of-run
  re-run budgets 5 minutes per task trial.
- **The planner** is told to test by tasks (prompt step 3) and sees the operator image's packages
  (numpy 2.5.3, pandas 3.0.6, RDKit, Pillow; no scipy), where generators and solvers run.
- **Report and page.** `report-card.md` has a row per task trial naming each output that missed; the
  HTML page has a task table (job, sections, checked outputs with tolerances, each try), a fold per
  task (files, where each expected value came from, the solver's results, each try's outputs), the
  generator's model and both programs, set-aside sections with their reasons, and run problems.
- **Verification.**
  - Suite 450 → 469 tests, 467 passing and 2 skipped. New tests check the output rules, the trial
    status, each refusal of a design, a generator or solver fault named for the planner, the re-check
    of a saved design from its records, a full claim through qualify, critique, execution and report,
    a wrong result failing the claim, a missing results file, a critique lowering the ceiling, a
    design for another claim's sections, the read-only mount, the page, and the export refusal.
  - Live, no AI: in the operator's image a generator built a two-inhibitor plate (planted IC50s
    100 and 1,000 nM, Hill 1, 4% noise) and a numpy-only four-parameter fit recovered 91 and 931 nM,
    fold shift 10.2, in 3.5 s; the re-check from records passed. A subject container mounted the
    plate read-only (a write was refused) and returned `results.json` as its only new file.
  - Live, AI, about $0.66 in all: one test session (Opus 5, 69 s, $0.29) used the dose-response skill
    on that plate, found neither scipy nor `tu`, wrote its own numpy fit and passed all four outputs
    (IC50 92 and 941, fold shift 10.2, more potent A), with `missing Python module scipy` recorded.
    One task critique (Opus 5, 107 s, $0.37) answered in its schema, counted the task and objected
    with substance: the Hill slope the claim promises was not checked, a 35% tolerance with 3-fold
    steps lets reading off the nearest concentration pass, and the noise made negative signals.
- **Docker Desktop** would not start on this machine: its backend crashed renaming stale socket files
  (`Docker\run\sailor-ingest.sock`, then `docker-secrets-engine\engine.sock`). I renamed both folders
  aside (`run.stale-20261005`, `run.stale2-20261005`, `docker-secrets-engine.stale-20261005`; nothing
  deleted) and it started.
- **Not done:** no live verifier run; the final reviewer; catalog export of task designs; a version
  bump. `src/` changed, so a run needs a Code session started after this commit. Export and the
  version bump were done in section 6.

**6. Question tests removed, version 0.8.0.** The operator answered open questions 8 to 11: "I think
we already give the verifier power for installing pre-request packages. If not, give the verifier the
power and add scipy", "Yes" to removing the question tests, "yes" to a wrong result winning, "yes" to
0.8.0, and "Also do the clean up for me".
- **Packages a skill imports.** The verifier installed only packages a skill declares, and
  dose-response imports numpy and scipy without declaring them. Now an undeclared import listed in a
  reviewed table of 26 modules (`IMPORT_DISTRIBUTIONS` in [`environment.py`](src/sci_ai_verifier/environment.py),
  owned by "Packages a skill declares or imports" in
  [`resource-policy.md`](skills/scientific-verifier/references/resource-policy.md)) is installed too,
  and anything else is reported, never guessed. A skill that declares nothing gets a build only when
  the operator image lacks a listed import. The planner's block and the report name what was added
  from imports. Contracts first: `local-contract.md` ("Skill environment"), the policy table,
  `LOCAL-CONFIG.md`. 5 new tests.
- **scipy in the operator's image.** `images/rdkit/requirements.txt` gains `scipy==1.18.1`, hash-pinned.
  Built as `sci-verifier-rdkit:2026.3.6-scipy1.18.1`, ID `sha256:6876c07f…79da6d`: numpy 2.5.3,
  pandas 3.0.6, RDKit 2026.3.6, Pillow, scipy 1.18.1. The operator's `.verifier/local-settings.json`
  pins it; the previous file is in scratchpad `c7991202…`. The build reused cached apt layers, so a
  fresh machine may need new Debian pins. Dose-response's script can now run; its `tu` command is
  still absent and is still reported.
- **Question tests removed.** Gone: `qualify_local_candidate` and `qualify_local_evaluator` (the
  Desktop manifest lists 33 tools, was 35), `local_evaluators.py` and `local-evaluator-spec.md`,
  calculated answers, the claim-only check, the AI reader, the question critique (rubric v13) with its
  coverage-gap and concern returns, and the text-only subject (`TextRuntime`). The code is in Git
  history. Old runs' records still render, and saved question designs stay on disk, unlisted.
- **Status.** A failed trial fails the claim whatever the others say; with none failed, an invalid
  trial leaves it inconclusive (`local-contract.md`).
- **Found while porting the tests, and fixed:**
  - the documentary step read a question field from a task design and would have crashed;
  - the task critique had lost v13's rule that a described search is judged by Python's search
    record; restored in criterion 4, as rubric `local-task-critique-v2`;
  - a task design's critique packet has no size guarantee: about 2.3 MB at every schema maximum,
    against a 512 KB limit, where real ones are 17 to 23 KB. Selection now refuses an oversized
    packet as `critique_packet_too_large` before any session, instead of ending the claim
    (`tool-contracts.md`);
  - task designs now export with their input files, and an import qualifies them again in the
    importer's container, which must rebuild the same files and planted values (`local-contract.md`).
    Release ranges default to 0.8.0 up to 0.9.0;
  - `validate_task_critique` was split out, so the tests' critique double goes through the real
    validator again.
- **Version 0.8.0** in `__init__.py`, `pyproject.toml`, the Desktop manifest, `SKILL.md`, `README.md`,
  `LOCAL-INSTALL.md` and `CLAUDE.md`; saved records from 0.8.0 are accepted. `README.md`,
  `LOCAL-INSTALL.md` and `LOCAL-CONFIG.md` no longer describe generated evaluators, the AI reader or
  question replies, and the `subject_refused` row now says the claim is re-run once.
- **Cleanup of `.verifier/`**, moved and not deleted, into scratchpad `c7991202…`: run `90c60cbe`
  with its attempt, subject runs and 10 candidates (`cleaned-90c60cbe/`), the live task checks and two
  synthetic fixture workspaces. Kept: runs `76ce4af1` and `32e60bd6` (untouched), the store, the
  reports and 13 candidates.
- **Verification.**
  - Suite 469 → 378 tests, 376 passing and 2 skipped. The question tests went. The rest were
    rewritten for tasks, with new tests for the import table, the status rule, the packet refusal, a
    catalog round trip that rebuilds the files, and the task critique's schema.
  - `tests/recorded/` keeps the assessor, refusal and session-limit streams, plus two retired
    sessions that show Claude Code's schema-correction loop.
  - The synthetic end-to-end fixture completes, and the operator's settings load.
  - Sizes: the verification bootstrap is 196,388 of 200,000 bytes. The stage 2 bootstrap is 119,604
    of 120,000, only 396 bytes spare. The largest pinned local document is `local-contract.md`, at
    34,540 of 40,960.
- **Not verified live:** a verifier run with tasks; the import table on a live skill. No real reply
  to the task critique's schema is recorded, so `test_recorded_replies.py` checks that schema with a
  hand-written one. Superseded by section 7.

**7. A recorded task critique, and room in the stage 2 bootstrap.** The operator answered open
questions 12 and 13: "yes, record it" and "trim a pinned document".
- **The recording.**
  - No verifier run has produced a task packet, so the packet comes from a live check. Today's code
    qualified three two-inhibitor plates in the operator's image in 17 s. The plates came from the
    live check's generator, and its reference solution passed all twelve outputs. The design used
    sections S2 to S5 of the real dose-response skill.
  - Python computed the ceiling, A with no limits, and `critique_packet` built the 22,776-byte
    packet. The reference page, claim and justification were written for the check.
  - One `claude-opus-5` session judged it under rubric v2, in 133 s for $0.49. It supported B,
    counted all three tasks, and named five objections: the Hill slope the claim promises is never
    scored; there is one plate layout; normalization is not exercised; a 35% tolerance lets an
    interpolation pass; the reference is a fixture.
  - Its first reply put the task verdicts beside the other fields instead of under `case_verdicts`.
    Claude Code refused it, and the session resent it.
  - The stream (`tests/recorded/critic-task-structured.jsonl`, 71,948 bytes) and the packet are in
    `tests/recorded/`, with no credential bytes. The script is `record_task_critique.py` in
    scratchpad `c7991202…`.
  - New tests: the reply answers its own packet under the live rubric's digest, and `critique_tasks`
    replayed over it sends that packet, schema and deadline. A change to the task rubric now needs a
    new recording.
  - `tests/recorded/README.md` allows a live check's packet while no run has produced one.
- **The trim.** `SKILL.md`, pinned in the stage 2, stage 3, verification and demo bootstraps, went
  from 11,227 to 9,635 bytes. Where it restated a rule, it now names the owner:
  - "Session bootstrap and trust classes" in `workflow.md`;
  - "Negotiating the grade" in `evidence-rubric.md`;
  - `stage2-contract.md`;
  - `workflow.md`'s plan requirements.

  Its claim that the local profile "does not execute proposed code" was false and is corrected.
- **Bootstrap sizes.** Stage 2 is now 118,018 of 120,000 bytes (1,982 spare, from 396), and
  verification 194,805 of 200,000.
- **Also fixed:**
  - `stage2-contract.md` said "The 0.5.0 reader supports … 0.2.0 … 0.5.0". It now points at
    `SUPPORTED_IMPLEMENTATION_VERSIONS`.
  - `CLAUDE.md` said tasks are used "whenever a container is configured".
- **Verification:** suite 380 tests, 378 passing and 2 skipped.

### Decisions taken 2026-10-05

- **The page is for the lab and the operator**, and may later be served from a web server (operator).
- **The final reviewer**: failures plus a sample of passes; disputed tests re-run, fixing the part at
  fault (operator).
- **Build the page first and test it before the reviewer** (operator).
- **A page after every completed run unless the user declines, and the calling agent writes its
  summaries** (operator).
- Proposed here and built:
  - plain text comes from a notes file and is marked as written after the run;
  - the page has no JavaScript;
  - the opt-out is an argument the agent sets from the user's words, and `--no-html` on the CLI;
  - the agent fills a template beside the page, and a page that fails never changes a run.
- Superseded the same day: "a view made by a script, not yet a run artifact, so no contract changes".
  Runs now make the page, and the public interface sentence in `local-contract.md` changed.
- **Test the whole skill by running it** (operator, section 4):
  - the planner groups the whole skill into claims, and Python checks that nothing is left out;
  - the number of claims grows with the skill's length;
  - a 3-hour limit;
  - claims are tested as wholes, by tasks whose output is checked.

  Built the same day (section 5).
- **Operator, after section 4:** a task whose answer Python builds can reach A; drop the claim-only
  check for tasks; every section of a claim must be used by a task; nothing about cost for now;
  merge `skill-environments`, delete it, and build on a new branch.
- **Proposed here and built (section 5):**
  - sections numbered by Python, set-asides with reasons, at most 12 claims;
  - a separate tool and module for task designs, with a generator and a reference solution, and the
    four output types;
  - planted judgments must quote the rule they follow;
  - inputs read-only at `/task`, results in `/work/results.json`, read by Python with no AI reader;
  - a wrong value fails a trial even when another field is missing;
  - A needs 3 counting tasks, B and C 2;
  - a separate critique rubric, leaving the question rubric and its recordings untouched;
  - with a container, question designs, calculated answers and generated evaluators are refused;
  - missing modules and commands recorded as findings; the operator image's packages shown;
  - 600 s per session, 40 turns per task session, 5 minutes per task trial in the re-run budget;
    the three-hour registration.
- **Superseded today:** "one claim per section, at most five" and "tested fact by fact" (entries of
  2026-09-29 to 2026-10-01) are retired; claim-only answers (2026-09-24) and the coverage-gap and
  concern returns (2026-10-01) now apply to question designs only, which no longer run here.
- **Operator, after section 5 (section 6):** give the verifier the power to install a skill's
  packages and add scipy; remove the question tests; a wrong result outweighs an unreadable one;
  version 0.8.0; clean up `.verifier/`.
- **Proposed here and built (section 6):** the import table, with nothing guessed outside it; refusing
  an oversized critique packet; exporting task designs with their files, and qualifying them again on
  import.
- **Operator, after section 6 (section 7):** record a real task critique; trim a pinned document
  rather than raise the stage 2 budget.
- **Superseded in section 6:** section 5's "the question rubric, v13, is untouched", "question designs
  … are refused as `tasks_required`; their code and contracts stay", "a task design cannot yet be
  exported", the image without scipy, and open question 8's recommendation to wait for a live run.

### Open questions for the operator

1. The 2026-10-02 entry's questions stand.
2. For the final reviewer: how large a sample of passes; how much time and how many subject calls a
   re-run may use; and whether a re-run repeats the whole claim or only the disputed tests.
3. Should the final reviewer, once built, write into the same notes, beside the calling agent's
   summaries?
4. to 7. Answered by the operator (section 5).
8. to 11. Answered by the operator (section 6).
12. and 13. Answered by the operator (section 7).
14. **Re-record from a real run?** The recorded critique's packet came from a live check, with a fixture
   reference and a claim written for it. Replace it with the first real run's packet, about $0.50?
   Recommended: yes, after that run, unless the rubric has not changed and the recording still passes.

### Urgent next steps, if any

None for the code: committed and pushed on `whole-skill-tests` with this entry. Before the first
live run with tasks, a prerequisite: start a **new** Code session, so that its `serve-local` runs this
branch's 0.8.0 code with the three-hour registration; a session started earlier keeps old code.

### Suggested next move

Run the verifier live on task tests, on a skill already run with questions, so the two designs can
be compared: tooluniverse-dose-response first (8 sections, 5 earlier runs). Merge `whole-skill-tests`
once a run has worked. The final reviewer comes after, on the new tests.

### Recommended next action

With the operator's go-ahead, after their cleanup of `.verifier/` and a check of Docker and the usage
window:
1. Start a new Code session on `whole-skill-tests` and run `verify_skill` on
   `D:\Su Lab\verifier-submissions\examples\tooluniverse-dose-response`.
2. It is finished when the report and page exist, and the run shows:
   - a manifest holding every section, with Related skills set aside with a reason;
   - each claim tested by a qualified task design whose reference solution passed;
   - the critique's verdicts per task, and whether it pushed for tighter tolerances;
   - each trial's `results.json` read by Python; with scipy in the image, the skill's script runs,
     and `missing command tu` should appear among the run problems;
   - time and cost per claim, against the 4 claims and $30 of run `90c60cbe`.
3. Record it in a new entry, with what to change before the next skill.

## Claude: 2026-10-06 (runs f84c131c and 2bef9e0d, the first with task tests; a reviewed command table for ToolUniverse's `tu`; the coverage return for tasks; departures, rules given and passes on tolerance)

### Current stage and status

Version 0.8.0, local workflow, on `whole-skill-tests`, which is the operator's to merge. The first
live run with task tests, `f84c131c` on tooluniverse-dose-response, completed. All four claims
settled at grade A with status pass, and 48 of 48 trials passed. That is a second skill family's
A branch working under tasks. It does not show full coverage: each reviewer named parts of its
claim that no task tested, and the data were nearly noise-free. The verifier now installs
ToolUniverse's `tu`, which the run lacked, through a reviewed command table. That table was checked
live but no run has used it yet. A critique that agrees with a grade, A included, but lists untested
parts of the claim now sends the claim back once (section 7).

Run `2bef9e0d` on western-blot-quantification, the first with the coverage return, also settled four
claims at A with status pass, 57 of 57 trials, and covered 75% of the skill's words against 13% under
questions. It also showed what a pass can hide: the skill's two-step formula is wrong when lanes are
loaded unequally, no task loaded them unequally, and the tolerance absorbed the difference
(section 8). The operator chose four options from open questions 6 and 7, and all four are built
(section 9): a departure of the skill from the reference holds the grade, a task may not state a
rule the claim supplies, a pass far from the reference is marked, and no search ends a coverage
return. No run has used them yet.

### What has been done

This session, 2026-10-06:

**1. Run `f84c131c`.** The operator: "use scientific-verifier-local to verify this skill … Show me
observation table where each row is one claim … per claim table, each row is one test".
- **Preflight.**
  - Docker had stopped when Claude restarted; launching Docker Desktop brought the engine up in
    20 s.
  - The 5-hour window was at 0%, and the run took it to 55%.
  - This session's `serve-local` started at 00:18, after the last commit.
- **Result.**
  - Four claims: S1, S2 and S4; S3; S5; S6 and S7. S8, Related skills, was set aside.
  - Each claim had 4 tasks of 3 trials: grade A, pass, 12 of 12 trials passing, unanimous, no
    invalid trials, one critique round, every task counted.
  - Run time 78 of 180 minutes, cost $23.04: planner $12.61 over 46 turns, trials about $8.5,
    critiques about $1.9.
  - 47 of 48 tries ran the skill's own fitting script, which scipy in the image made possible.
    Run problems: `tu` missing in 3 tries, `cygpath` in 1.
  - The models came from GraphPad Prism's curve-fitting guide. Claim 3's two judgment rules came
    from Wikipedia, a tertiary source.
- **Delivered.** The page's notes were filled and the page redrawn, and the operator got tables per
  claim and per task. Records: [report-card.md](.verifier/runs/f84c131c-b936-4534-b7ff-043ca2cb0216/report-card.md).

**2. Why parts stay untested.** The operator asked: "what's the reason there are still parts we
don't test? did we set a too high budget for number of tests we can give?" No cap was binding:
each claim used 4 of 6 tasks and at most 5 of 12 outputs, and the run used 48 of 128 trial calls
and 78 of 180 minutes. The records show three causes:
- **The skill's own thresholds have no outside source.** These are the r-squared rule, the
  steep/shallow slope labels and the minimum point count. Grade A forbids keying an expected value
  to the skill's text, and the planner said so for claims 3 and 4.
- **Python checks that every section is used, not every rule.** The planner built grade A's 3
  tasks plus one spare and listed what it skipped: the confidence interval and log IC50, the
  point-count rule, the IC50-versus-Ki warning.
- **Gaps had no consequence.** Every critique named gaps and weak tests, such as blanks too small
  for blank subtraction to matter, but agreed with A and required no revision. The coverage-gap
  return that acted on that was retired with question tests on 2026-10-05.

Proposed, not decided: open questions 1 and 2.

**3. `tu` and the command table.** The operator: "yes, run the check and add tu if it passes".
- **Why it was missing.** The skill declares nothing, and `tu` is a shell command, not a Python
  import. The install rules covered declarations and the import table only, so setup recorded
  `not_needed`.
- **The check.**
  - `tooluniverse` 1.5.6 on PyPI provides `tu`, its console script `tooluniverse_cli_entry:main`.
  - Its dose-response tools compute locally with scipy; its source says "No external API calls".
  - Built through the verifier's own `_build`: 70 s, 109 wheels and 155 MB, against caps of 200
    wheels and 1 GiB. The largest wheels are scipy, faiss-cpu, numpy, pandas and tooluniverse.
  - In a trial container (no network, read-only root, user 65534, 512 MiB, 1 CPU) all three tools
    ran in about 2.6 s each: IC50 0.762 with r-squared 0.9998, and a fold shift of 13.4.
- **Built.** Contracts came first:
  - [`resource-policy.md`](skills/scientific-verifier/references/resource-policy.md) gains a
    command table, `tu` to `tooluniverse`;
  - [`local-contract.md`](skills/scientific-verifier/references/local-contract.md) "Skill
    environment" gains **Commands.**;
  - `LOCAL-CONFIG.md` says the same.

  Then [`environment.py`](src/sci_ai_verifier/environment.py):
  - `COMMAND_DISTRIBUTIONS` holds the table;
  - `run_commands` reads the first word of each simple command in a shell or unmarked fenced
    block of Markdown. On an unclosed quote it falls back to the line's first word, which the
    skill's three-line JSON needs;
  - the image probe reports `commands_unavailable`, and with nothing declared a listed command the
    operator's image lacks triggers a build that also holds every listed import;
  - the planner's block and the report line name the commands.

  Three new tests cover detection, the build and no build.
- **End to end on the real skill.** Setup found `tu`, built numpy, scipy and tooluniverse
  (109 wheels, 67 s), `tu` answered in a trial container, and the image was removed.
- **Cost.** Every verification of this skill now spends about 70 s of setup and downloads about
  155 MB, since environments are not cached.

**4. A skill bug.** The skill's `scripts/fit_dose_response.py --help` crashes: two help strings
hold a bare `%`, which argparse formats. Fitting is unaffected. The fix belongs to the skill.

**5. Docker** crashed at startup again on stale socket files. Two rounds of renaming
`%LOCALAPPDATA%\Docker\run` and `%LOCALAPPDATA%\docker-secrets-engine` aside (`*.stale-20261006`,
then `*.stale2-20261006`; nothing deleted) brought the engine back.

**6. Verification.**
- Suite 380 → 383 tests, 381 passing and 2 skipped.
- Sizes: the verification bootstrap is 194,947 of 200,000 bytes; stage 2 118,018 of 120,000;
  `local-contract.md` 35,020 of 40,960.

**7. The coverage return for tasks.** The operator: "add the coverage return for tasks", and yes to
re-recording the critique from one of `f84c131c`'s real packets.
- **Contracts first.**
  - `select_local_candidate` in
    [`tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md) owns the rule:
    **The coverage return**, the refusal `return_unsearched`, and `coverage_gaps` in the critique's
    reply.
  - `workflow.md`'s transition text moves with it.
  - `local-tasks.md`, step 4 of "Negotiating the grade" in `evidence-rubric.md`,
    `artifact-contracts.md` and `local-contract.md` point at it.
- **The rubric, v3.** The critique lists in `coverage_gaps`, whatever its grade, what the claim's
  sections say to do, check or conclude that no task tests, each with the task or search that would
  test it. The reply schema requires the field.
- **The return.**
  - A critique that agrees with the proposal (the settled grade equals it) and lists gaps sends the
    claim back once per claim, **at every grade, A included**. The question-era return skipped A, so
    it would have asked nothing in `f84c131c`, where every claim was A.
  - Accepting the same design afterwards needs a search or fetch for the claim in Python's record
    made since the return, or it is refused as `return_unsearched`; with no workflow log nothing is
    checked.
  - A revised design is critiqued as usual and never returned for gaps again; its critique sees
    "An earlier version left untested: …" among the carried concerns.
- **Report and page.** `report-card.md` gains "Coverage gap:" lines and "Returned once for coverage
  gaps". The page now shows the untested count and list for task claims too.
- **The re-recording.** Run `f84c131c` claim 3's stored packet, with v3 in place of v2, judged by
  `claude-opus-5` in 195 s for $0.70.
  - A, all four tasks counted, three objections, and five coverage gaps: the slope labels, the
    r-squared rule, the bottom plateau, the in-range IC50 check and the fold-shift caveat. Under the
    new rule that claim would have come back once.
  - Its first reply added a stray `paramete r_name` key, which Claude Code refused, and the session
    resent it.
  - It replaces the live-check recording, so `tests/recorded/README.md` drops the live-check
    exception.
- **Verification.**
  - 4 new tests: the return at A with the search check; once per claim; no log; no gaps, or a grade
    below the proposal.
  - Suite 383 → 387 tests, 385 passing and 2 skipped. The verification bootstrap is 195,150 of
    200,000 bytes.

**8. Run `2bef9e0d`.** The operator: "clean and run the verifier on western blot skill", then "yes,
record it and draft the options".
- **Cleanup.** Moved, nothing deleted, into session `0f5df502`'s scratchpad: run `f84c131c` with its
  attempt, subject runs and 5 candidates (`cleaned-f84c131c/`, 4,641 files), and the false start
  below (`cleaned-6bd93bfc/`, 94 files). Kept: runs `32e60bd6` and `76ce4af1`, the store, the reports
  and 13 candidates.
- **A false start.** This session's `serve-local` dated from 06:37, before commits `3d41f1b` and
  `a31f708`. I ran the same action through `scripts/verify.py verify` with the registration's
  arguments in a background shell instead. That run, `6bd93bfc`, died two minutes in when the app
  restarted the session. The restarted session's server postdated both commits, and `verify_skill`
  ran `2bef9e0d` from it.
- **Preflight.** Docker was up. The 5-hour window was at 3%, and the run took it to 72%, the most of
  any run so far.
- **Result.** [report-card.md](.verifier/runs/2bef9e0d-f74d-4362-8a06-55e3a8385014/report-card.md).
  The page's notes were filled and the page redrawn.

  | Claim | Sections | Tasks before → after the return | Trials passed | After the return | Gaps listed |
  | --- | --- | --- | --- | --- | --- |
  | 1. Loading-control normalization | S4, S5, S11–S13, S27 | 4 → 4 | 12 of 12 | two web searches, same design | 3 |
  | 2. Fold change, then averaging | S6, S7, S14, S15, S26 | 4 → 4 | 12 of 12 | two web searches, same design | 7 |
  | 3. Choosing the analysis route | S8, S17–S19 | 4 → 5, rewritten | 15 of 15 | revised | 8 → 7 |
  | 4. Mistakes that spoil quantification | S20–S24, S28, S29 | 4 → 6 | 18 of 18 | revised | 7 → 6 |

  - Every claim: grade A, pass, unanimous, no invalid trials, every task counted, two critique rounds.
  - Set aside with reasons: S1–S3 (title, metadata, overview), S9 and S10 (image steps whose tools the
    skill does not ship), S16 (plots), S25 (output files) and S30 (references). Coverage: 1,916 of
    2,558 words (75%) and 22 of 30 sections, against 333 words (13%) and 4 sections in the
    question-era run `32e60bd6`.
  - Run time 98.5 of 180 minutes, cost $34.7: planner $19.97 over 53 turns, 57 trials $9.41, 6
    critiques $5.36. `f84c131c` took 78 minutes and $23.0, `32e60bd6` 78 minutes and $30.9.
- **The coverage return.** Every critique agreed with A and listed gaps, so every claim came back
  once.
  - Claims 3 and 4 were revised. For claim 3 the planner, citing the critique, found each branch of
    the decision tree tested on one side only. Claim 4 gained tasks on the order of averaging and on
    a highly variable repeat.
  - Claims 1 and 2 each ran two web searches at once, opened no result and accepted the same design.
    That satisfied the `return_unsearched` check.
- **A flaw the pass hid.**
  - The skill's two-step formula divides the modified form by the total form over the loading
    control. That is the modified form times the loading control over the total form, so it does not
    cancel unequal loading.
  - All four tasks built on it (wb2, wb4, c2d, e4) loaded every lane within about 6%. The planner
    noted that then "the answer does not depend on which of the two published ratio conventions is
    used".
  - The test AI followed the skill and came out up to 3.4%, 5.4%, 5.5% and 2.4% off the key, inside
    tolerances of 10%, 10%, 8% and 8%.
  - Claim 1's critique computed exactly this, wrote that a subject following the sections verbatim
    passes, and listed it as a coverage gap. The rubric's fairness criterion asks that a correct
    analysis following the skill passes, which assumes the skill's procedure is the correct one.
- **Tasks that state their rule.** Claim 4's jobs gave the deciding thresholds (15%, 15%, 10%, a
  coefficient of variation of 0.5); g3 named the planted defect and g5 both orders of averaging. Its
  critique objected that the tasks test "correct execution of a given rule, not whether the skill
  surfaces the defect or chooses the criterion", and counted them.
- **Checked against `f84c131c`,** the other task run, since the 2026-10-02 bar asks for more than one
  skill:
  - Every answer there was within 0.18% of the reference solver's result for the same file, even
    where 20–28% off a small planted plateau, which is fitting noise. Here the four two-step tasks
    were 2.4–5.5% off the solver, and every other task within 0.01%. "Off the solver but inside the
    tolerance" separates the two runs exactly.
  - Its `c4_midpoint_not_sampled` job also defined its criterion ("between 25 percent and 75
    percent"), so tasks that state their rule occur in both skills.
  - Its critiques named regimes its tasks avoided, such as midpoints well inside the range, but its
    answers matched the solver, so it shows no hidden departure like the two-step one.

**9. Departures, rules given, passes on tolerance, and no search to end a return.** The operator:
"build the recommended options: 6a, 6c, 6d drop, 7a", then the claim-1 re-recording.
- **Contracts first.**
  - [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md) owns the task rules: a
    job may not give a rule, threshold or order of steps the claim's sections supply, and a rule
    they lack is named in `criterion_given`; **Where the skill departs from the reference**; and
    **Passed on tolerance**, with its 0.5% margin.
  - [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md): "Not given
    away", "Right", the `leaked` and `unsound` rows, and steps 4 and 5. `unsound` no longer calls a
    key unfair because following the skill misses it.
  - `select_local_candidate` in
    [`tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md) owns
    **Departures** and the hold, drops `return_unsearched`, and names `departures` and
    `criterion_given` in the critique's reply. `workflow.md`, `artifact-contracts.md` and
    `local-contract.md` point at them.
- **Rubric v4.** Criterion 3 asks that some task expose each departure of the skill's own
  procedure from the reference solution. `rubric.departures` and `rubric.criterion_given` say how
  to report them, and the `leaked` and `unsound` verdicts follow the table. The reply adds
  `departures`, and per task `criterion_given`, empty or the rule.
- **The hold.** While the critique lists a departure, the settled grade is one below the proposal
  it judged: A to B, B to C, C to no grade (policy `evidence-strength-v10`). Accepting that grade
  holds it no lower. A revised design whose critique lists none can settle at the proposal. The
  reply carries `departures` and says how to answer them, and earlier departures reach the next
  critique.
- **Passed on tolerance.** Scoring keeps `reference_result` and `off_reference` for a number that
  passed more than 0.5% from a nonzero reference result. The report lists those tasks and the page
  marks them; status and grade do not change.
- **The coverage return** needs no search to end. The report says whether the planner kept the
  design, and how many gaps it left open, or revised it.
- **Report and page** show departures, rules given, passes on tolerance and how a return ended.
- **The re-recording.** Run `2bef9e0d` claim 1's stored packet, with v4 in place of v3, judged by
  `claude-opus-5` in 274 s for $0.96: a live check of the hold on the case that motivated it.
  - A, all four tasks counted, five objections, three required revisions, three coverage gaps and
    one departure. Followed literally, the skill's two-step formula is the modified form times the
    loading control over the total form, which keeps the per-lane loading, and it agreed with the
    key only because every phospho/total task held loading equal. The critique called them "not two
    defensible readings of one claim" and required a fifth task with about 2-fold loading variation.
  - Under the hold, that claim would have settled at B until such a task existed, not at A.
  - Its first reply added a stray `paramaters` key, which Claude Code refused, and the session
    resent it.
  - It replaces `f84c131c`'s recording, and `tests/recorded/README.md` says so.
- **Verification.**
  - New tests: the hold at A, B and C, and accepting it; a revised design that exposes the
    departure; the tolerance mark, unit and end to end with the page; a rule given, end to end;
    the reply's new shapes. The test of the search check went with it.
  - Suite 387 → 391 tests, 389 passing and 2 skipped.
  - Sizes: the verification bootstrap is 195,574 of 200,000 bytes; every pinned local block is
    under 40,960, the largest `local-contract.md` at 35,047.

### Decisions taken 2026-10-06

- **Operator:** run the `tu` check, and add `tu` if it passes. Done.
- **Operator:** add the coverage return for tasks, and re-record the critique from a real packet.
  Done (section 7).
- **Operator:** clean and run western-blot-quantification, then record the run and draft options for
  its weak spots. Done (section 8).
- **Operator:** build 6(a), 6(c), dropping the search in 6(d), and 7(a), and re-record the critique
  from `2bef9e0d`'s claim-1 packet. Done (section 9).
- **Proposed here and built (section 9):**
  - Python applies the hold, one grade below the proposal the critique judged, instead of trusting
    the critique to lower its own grade; accepting the held grade does not lower it again.
  - `criterion_given` is the critique's judgment, per task.
  - A zero reference result is not compared for the tolerance mark.
- **Proposed here and built:** the return applies at every grade, A included, unlike the
  question-era return, which skipped A.
- **Proposed here and built (section 3):**
  - commands are read from shell or unmarked fenced blocks of Markdown only;
  - an unlisted command is never installed, and a trial that needs it records it as a run problem;
  - the image probe reports missing commands;
  - with nothing declared, a listed command the operator's image lacks triggers a build.

### Open questions for the operator

1. Answered by the operator (section 7).
2. **The skill's own thresholds.** Leave them untested and listed, as now, or test them as "the skill
   follows its own rule" at a grade below A, since the expected values would come from the skill?
3. Answered by the operator (section 7).
4. **Merge `whole-skill-tests`** now that a task run has worked? The merge is the operator's.
5. The 2026-10-05 entry's open questions on the final reviewer stand.
6. Answered by the operator (section 9): (a), (c), and dropping the search in (d). The options as drafted:
   **An A that hid a flaw** (section 8). The design avoided the case where the skill goes wrong, the
   tolerance absorbed the difference, and two web searches closed the return. These options combine:
   - (a) **Flag answers that pass only on tolerance.** After the trials, Python compares each number
     with the reference solver's result for the same file. Beyond 0.5%, which separates the two task
     runs exactly, the report and page mark the task "passed on tolerance only", with the size of the
     difference; grade and status stay. Owners: "Reading a trial's results" in `local-tasks.md`, and
     the report. No rubric change. A subject that rounds hard can trip it, so it informs the reader
     rather than deciding.
   - (b) **As (a), but the flagged task counts as inconclusive,** so the claim's status becomes
     inconclusive and its grade stays. Here claims 1, 2 and 3 would have been inconclusive.
   - (c) **Make a known departure a required revision.** Where the skill's procedure, followed
     literally, departs from the reference solution in a situation the claim covers, at least one
     task must put the departure outside its tolerance. A critique that finds none requires one and
     may not support the proposed grade until it exists. Owners: the task rule in `local-tasks.md`,
     and criterion 3 and the verdicts in `evidence-rubric.md` and the task rubric. The rubric moves to
     v4, which needs a live re-recording of about $0.70, asked first. On this skill claim 1 would most
     likely fail, which is the right result.
   - (d) **The search that ends a return.** Drop it: the planner may keep a design, the report says how
     many gaps it left open, and `return_unsearched` goes. Or require one line per gap, saying why it
     cannot be tested or naming a reference fetched since the return, which Python counts. Or require
     a fetch instead of a search.
   - Recommended: (a), (c), and dropping the search in (d), since under (c) the gaps that matter become
     required revisions. (a) rests on two skills, (c) on one.
7. Answered by the operator (section 9): (a). The options as drafted: **Tasks that state their rule**
   (section 8). `local-tasks.md` already says the job must not tell the
   test AI "which steps of the skill to follow … or which problem was planted", but `leaked` covers
   only naming the problem, and the critique counted such tasks while objecting. Options:
   - (a) Widen `leaked` to a job that states a step, an order or a criterion the claim's sections
     supply; such a task does not count. Where the sections give no criterion, as for when a signal
     stops being proportional to the load, the job may state one, and the report marks the task
     "criterion given".
   - (b) Mark only: the report flags every task whose job states a criterion, and nothing else changes.
   - (c) Leave it to the critique's objections, as now.
   - Recommended: (a). It enforces a rule the contract already has, it occurred in both task runs, and
     it shares 6(c)'s rubric bump and re-recording. Here g3 and g5 would likely not count, which still
     leaves claim 4 four counting tasks.

### Urgent next steps, if any

None. `src/` changed again, so before the next run restart the session and check that its
`serve-local` postdates the commit; do not run around it, since a background `verify` dies with the
session (section 8). Check Docker and usage first.

### Suggested next move

Re-run two skills on the new rules: western-blot-quantification, where claim 1 should now meet a task
with unequal loading or settle below A, and tooluniverse-dose-response, to check that the hold and the
marks do not fire on a skill whose answers match the reference (the 2026-10-02 bar).

### Recommended next action

With the operator's go-ahead, after a session restart and a Docker and usage check:
1. Run `verify_skill` on western-blot-quantification.
2. It is finished when the report shows, for claim 1, either a task with unequal loading and its
   status, or a grade held below A with its departure; and which tasks passed on tolerance only and
   which jobs gave a rule.
3. Then run tooluniverse-dose-response and check that no departure, tolerance mark or rule given
   appears where its answers match the reference. Each run costs $25–35 and most of a 5-hour
   window.

## Claude: 2026-10-07 (the critique answers questions and Python gives each task's verdict; run cfe9e57a)

### Current stage and status

Version 0.8.0 on `whole-skill-tests`, the operator's to merge. The 2026-10-06 entry built a hold for
departures, a mark for passes on tolerance, the rule against tasks that state the skill's rule, and
no search to end a coverage return. Today the task critique stopped choosing verdicts: it answers
one question per row of the verdict table, and Python gives the verdict. Replays of real packets
show the change working, and no run has used it yet.

### What has been done

This session, 2026-10-07:

**1. Other problems in run `2bef9e0d`.** The operator asked whether there were problems besides the two
fixed. Checked against both task runs:
- **The critique never refused a task.** All 43 verdicts in runs `f84c131c` and `2bef9e0d` were
  `counts`, while its objections named six flaws the verdict table excludes: two near-repeats, a
  task that named its planted defect, two keys whose quotes did not support them, a task that
  passed with the normalization skipped, and a solver that hard-coded a planted value. The rule that
  objections and verdicts must agree was already in its rubric.
- **Planner justifications held wrong numbers** in 3 of 4 claims of `2bef9e0d`, and the report shows
  them as written. One skill only, so left for more evidence.
- **What tasks cannot test:** the skill's image steps need tools it does not ship, and plots and
  reporting advice have no output field.
- **Cost and time keep growing:** 98.5 minutes and 69% of a 5-hour window for `2bef9e0d`.
- Minor: one source per run lost to a refused redirect; three trials per task never disagreed in
  105 tries.

**2. Problem 1, checked before building.** The operator: "How would you recommend tackle problem 1",
then "yes" to a replay check.
- A draft rubric replaced the critique's verdicts with five yes-or-no questions, one per row of the
  verdict table, answered before the grade; Python gave the verdict of the first yes.
- Six real packets replayed on `claude-opus-5` for $5.11, 155 to 491 seconds each: four holding the
  flaws, and `f84c131c` claims 1 and 3 as clean controls.
- Four of the five clear flaws stopped counting. The controls kept every task at A. The question
  "would a wrong analysis pass every output?" also caught tasks too loose to tell right from wrong:
  three of `2bef9e0d` claim 3's first design, and two of `f84c131c` claim 2, where skipping blank
  subtraction passes, which its live critique had noted and counted.
- It showed three things to fix: a task that names where its planted problem is, a "rule given"
  note that marked output units and facts about the data, and reviews near the 600-second
  deadline.

**3. Built.** The operator: "yes" to fixing those three and building it.
- **Contracts first.** [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md)
  owns it: the critique answers one question per row of the verdict table, and Python gives a case
  the verdict of the first row answered yes, or `counts`. `leaked` adds where the planted problem
  is, and `unsound` adds any plausible wrong analysis that passes every output.
  `local-tasks.md`, `tool-contracts.md` (the reply shape), `workflow.md` and
  `artifact-contracts.md` point at it, and `local-contract.md` gives the critique fifteen minutes.
- **Code.** Rubric v5 holds `TASK_QUESTIONS`, and the reply's `task_checks` come first and the grade
  last. `task_verdict()` derives `case_verdicts`, so selection, the report and the page read them as
  before. A missing replacement is said, never invented. `criterion_given` excludes units, formats
  and facts about the data. `CRITIC_TIMEOUT_SECONDS` is 900, the policy `evidence-strength-v11`,
  and the page lists each task's five answers.
- **Confirmation through the real code.** `critique_tasks` on two of the replayed packets, three
  sessions for $2.74:
  - `f84c131c` claim 1, the control: all four tasks counted at A, with no "rule given" mark; 184 s.
  - `2bef9e0d` claim 4: g5 dropped as leaked, and "rule given" named only the jobs' cut-offs. g3
    counted in both reviews: the stain mark its job mentions shows in its data anyway, and the
    critique could name no wrong route that passes it.
  - In that first claim-4 review the critique wrote that an un-normalized reading "also passes" g2,
    and still answered no, since g2 was not built to catch it. The question now asks about any wrong
    analysis, even one the task was not built to catch, and says that one it can name means yes.
    Re-checked: g2 and g4 dropped because skipping normalization passes every output; three tasks
    counted and the critique's own grade was B; 438 s, $1.07.
  - That last review is the new recording; its first reply was accepted.
- **Verification.** Suite 391 → 392 tests, 390 passing and 2 skipped. The verification bootstrap is 195,877 of 200,000 bytes; every pinned local block is under 40,960.

**4. The critique's effort.** The operator asked what effort the verifier's sessions use. None was
set: the planner, the subjects and the critique all ran at Claude Code's default for `claude-opus-5`,
`high` per Anthropic's effort documentation; the CLI accepts `--effort` from `low` to `max`. The
operator: "just change the reviewer setting to xhigh, no test". The critique now runs at `xhigh`,
recorded as `effort` on each critique, with twenty minutes instead of fifteen, since it thinks
longer ("Critique" in `local-contract.md`). The planner and the subjects keep the default: a subject
that thinks harder could quietly correct a skill's mistake. No replay checked it; the next run does.
Suite 392 tests, 390 passing and 2 skipped.

**5. Run `cfe9e57a`, and two fixes.** The operator: "clean and run the verifier on western blot
skill", then "yes, do both" to the fixes below.
- **Cleanup.** Run `2bef9e0d`'s files (4,714) moved into session `0f5df502`'s scratchpad
  (`cleaned-2bef9e0d/`); nothing deleted.
- **Result.** Five claims; 2,118 of 2,558 words (83%) in claims, against 75% in `2bef9e0d`, since
  the image steps (S9, S10) became a claim tested on intensity profiles. 145.6 of 180 minutes and
  $35.2: planner $20.79, critiques $8.55, 30 trials $5.62, assessor $0.24.
  - Claims 1, 2 and 5 settled at A and passed, 9 of 9 trials each. The critique dropped tasks in
    claims 1 to 4. Two of claim 5's tasks passed on tolerance only.
  - Claims 3 and 4 ran no task. Each redesign's critique passed the 256 KiB output limit at `xhigh`
    (`claude_output_limit` after 638 and 664 s), so no plan was fixed, and both ended at D,
    inconclusive, by the fallback documentary assessment. Claim 4's first critique had listed two
    departures, the saturation check and including all repetitions against a documented
    exclusion, and held its grade at B.
  - The two-step flaw passed again. The planner did build a task with unequal loading, but its job
    asked for "the phosphorylated fraction of the SMAD2 that is present". The test AI computed that,
    1.4, where the skill's own formula gives 2.45, and the critique counted the task.
- **Fixes.**
  - The critique may write 2 MiB (`CRITIC_OUTPUT_BYTES`); the assessor keeps 256 KiB ("Critique" in
    `local-contract.md`).
  - Rubric v6 adds the question `job_decides` (`leaked` if yes): does the job say how to compute an
    output, so the test AI could answer without the claim's sections? Naming what to report is not
    saying how; a job settling even one output answers yes. `local-tasks.md` tells the planner to ask
    for outputs in the user's terms, and `evidence-rubric.md`'s `leaked` row covers it.
  - Considered and not built: a no-skill control trial per task, which Python would score. Left for
    after the next run.
- **The re-recordings.** Two sessions on `cfe9e57a` claim 1's final packet at `xhigh`, $3.05:
  - The first answered `job_decides` no for every task: the wording "settles that one output", it
    wrote, but another output still needed the skill. The question now says that a job settling
    even one output answers yes.
  - The second dropped all three two-step tasks as leaked, so claim 1 would need a redesign in which
    the skill decides the computation. 579 s; its 284 KB stream would have passed the old limit. Its
    first reply was wrapped in a stray `StructuredOutput` key, refused and resent. It is the new
    recording.
- **Verification.** Suite 392 tests, 390 passing and 2 skipped.

### Decisions taken 2026-10-07

- **Operator:** check problem 1 by replay before building; then fix the three issues it showed and
  build. Done (sections 2 and 3).
- **Operator:** tighten the wrong-analysis question after the re-check. Done (section 3).
- **Operator:** raise the critique's output limit and add the question on jobs that say how to
  compute an output, tightened after its first re-check. Done (section 5).
- **Operator:** run the critique at effort `xhigh`, untested until the next run. Done (section 4).
  The deadline rising to twenty minutes was proposed here and built with it.
- **Proposed here and accepted with the build:** g3, whose job says the Control lane sits over a
  stain mark, counts. Its data show the high background anyway, and the job never says what it does
  to the answer; all three reviews under the questions judged so.

### Open questions for the operator

1. The 2026-10-06 entry's open questions 2, 4 and 5 stand: the skill's own thresholds, merging
   `whole-skill-tests`, and the final reviewer.
2. **Planner justifications with wrong numbers** (section 1): mark them in the report, or wait for a
   second skill to show the same? Recommended: wait.

### Urgent next steps, if any

None. `src/` changed, so restart the session before the next run, and check Docker and usage first.

### Suggested next move

Re-run western-blot-quantification to see claims 3 and 4 reach a fixed plan and claim 1 meet a
two-step task the skill decides, then tooluniverse-dose-response. Do not move to a longer skill yet:
`cfe9e57a` used 146 of 180 minutes for five claims, with each critique taking 8 to 11 minutes.

### Recommended next action

With the operator's go-ahead, after a session restart and a Docker and usage check:
1. Run `verify_skill` on western-blot-quantification.
2. It is finished when the report shows each task's answers, which tasks dropped and why, whether
   claim 1 met a task with unequal loading or settled below A, and the run's time and cost.
3. Then run tooluniverse-dose-response and check that its clean claims keep their tasks. Each run
   costs $25–35 and most of a 5-hour window.

## Claude: 2026-10-08 (run 50104eac stopped on the session limit; the critique back at high effort)

### Current stage and status

Version 0.8.0 on `whole-skill-tests`, the operator's to merge; the 2026-10-07 entry's state stands.
The first run on a longer skill, neurokit2, stopped on the subscription's session limit, and the
critique runs at effort `high` again.

### What has been done

This session, 2026-10-08:
- **Run `50104eac`, neurokit2.** The operator: "Check my usage and Docker, then run the verifier on
  neurokit2". The window was at 20%, Docker up, and the session's server postdated `4877b54`. The
  skill's `uv pip install "neurokit2==0.2.13"` was read as a declared package. After 2 h 22 min, with
  five claims (three with results, one stopped operationally, one still in design) and 40 trials,
  the planner stopped on HTTP 429, "You've hit your session limit". Neither the run nor its claims
  are a finding about the skill.
- **The critique's effort back to `high`.** The operator: "change the reviewer's effort back to
  "high", clean the failed previous run due to usage limit and then run the verifier on neurokit2".
  `CRITIC_EFFORT` is `high`, still passed explicitly; the twenty-minute deadline and the 2 MiB
  output limit stay ("Critique" in `local-contract.md`).
- **Cleanup.** Run `50104eac`'s run, attempt, subject runs and 8 candidates (7,658 files) moved into
  session `60cf88bc`'s scratchpad (`cleaned-50104eac/`); nothing deleted. Run `cfe9e57a` stays.
- **Verification.** Suite 392 tests, 390 passing and 2 skipped.

### Urgent next steps, if any

The session's `serve-local` loaded the critique module with `xhigh` during `50104eac`, so restart
the session before the next run.

### Suggested next move

Run neurokit2 again with the window near empty: at about an hour per two claims it needs most of
a 5-hour window and may reach the 180-minute cap.

### Recommended next action

After a session restart and a usage and Docker check, run `verify_skill` on neurokit2. It is finished
when the report exists, or when the run stops on its time cap with the claims it reached.
