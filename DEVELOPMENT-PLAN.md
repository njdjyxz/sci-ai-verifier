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
| `0aeca4c6` (2026-09-28) | scikit-survival | 1 at A, 3 at B, 1 at D by fallback after a safety refusal; 62 of 64 obtained trials passed, 0 invalid |

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
and reused answers filed under a case's old ID. Both are fixed and **not yet seen live**; the
2026-09-24 and 2026-09-25 entries are in the archive. Run `0aeca4c6`, the first on a
non-chemistry skill since glycoengineering, saw the reply schemas work live, and the **fallback D
ran for the first time**. That run also exposed three problems:
- a content-triggered safety refusal voided one claim;
- a code-fenced reply was misread;
- the sandbox could not run scikit-survival at all.

The last is now answered by **skill environments** (below). They are live-checked on a blank
`python:3.12-slim` base but have not yet been used in a verifier run. Calculated answers have still
not met a run. The 2026-09-28 entry has the details. The code fence, and reply format in general,
is now answered by **typed answers and an AI reader** (the 2026-09-29 entry): seven answer types
read by one reader, and a fresh session that reads again what that reader does not pass. Replayed
over all 945 saved replies they read every right answer as right and no wrong one, but neither
has met a verifier run.

Automated suite: **425 tests, 423 passing and 2 skipped, none failing**. The one that used to
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
6. **The timeout.** The app passes 5,400 s. `0aeca4c6` used 3,827 s for five claims, and each
   environment build adds about 30 s of setup.
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

## Claude: 2026-09-29 (typed answers and the AI reader, on skill-environments)

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
below). **None of this has been used in a verifier run, and nothing is committed yet.** The whole
suite passes, and three live sessions recorded the new critique rubric and two AI readings.

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
- The verification bootstrap is 199,824 of its 200,000 bytes. Each document pinned for the local
  planner fits the 40 KiB section reply, now tested.
- Not verified: any of this in a verifier run.

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

### Open questions for the operator

1. **How lenient the AI reader should be.** It may judge `7.6e-9 M` to match 7.6 nM. That is a
   scientific equivalence rather than presentation. Live, it also ignored a question's "without the
   namespace prefix". Both are allowed under "an AI reading counts", and both should be watched in
   the run.
2. **Uncounted trials are not read**, to save time near the 90-minute limit. Their report rows keep
   Python's verdict.
3. **List and set items are typed by their own form**, so a capitalised item such as `Core` is
   compared exactly.
4. The 2026-09-28 entry's open questions stand.

### Urgent next steps, if any

None blocking. The work is uncommitted on `skill-environments`; commit when the operator asks.

### Suggested next move

Run scikit-survival once with skill environments, typed answers and the AI reader together.
The run tests claim scope too: compare its case-count caps, `duplicate` verdicts and sections
covered with the survey under "Claim scope".
Planners should now write open cases where they used to write choices, and the run shows whether
subjects answer them in forms the reader accepts.

### Recommended next action

With the operator's go-ahead:
1. Commit this branch.
2. Follow "Before the next run" and "Cleaning the previous run" in the 2026-09-28 entry. The
   candidates at method version `-6` are no longer offered, since `-7` supersedes them, so moving
   them is tidying only.
3. Start a new session, so `serve-local` loads this code, and run scikit-survival.

Check, beyond the 2026-09-28 list, whose item 1 this replaces:
- every critique's `rubric_ref` is v9,
  `0ae090e44124cc46a30433b188bd93a1ea1ba1cd81140c146cda33af6d1788e3`, audits carry policy
  `evidence-strength-v7`, and every reading's `reader_ref` is
  `738e3dbe40c8c3fbd00a5f6a727324b86b6fdef1bacca2ea3779ecec5d54ea65`;
- the share of `choice` cases, and each open type the planners used;
- every trial the AI reader read, quoting the reply, the copied answer and the reason;
- any refused reading, and why;
- any status that differs from Python's reader alone;
- the claim-only answers the reader changed;
- claim scope, against the survey's baseline:
  - how many claims there are, and how many of the skill's sections they cover;
  - how many settled below their source only for their case count (24 of 41 before), which is
    now each claim's "Limited by its number of independent cases" line;
  - how many cases were `duplicate` (17 in 17 runs before);
  - whether any claim became a vague summary of the skill;
  - whether two claims quote the same paragraph, which decides the drafted rule above;
  - whether Workflow, Decision Framework, Best Practices, Substructure Alignment and Activity
    Heatmap (or the scikit-survival equivalents) now get claims.

It is finished when each has a recorded answer.
