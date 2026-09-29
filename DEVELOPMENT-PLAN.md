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

The last is now answered by **skill environments** (below), which are tested with fake Docker and
**not yet live**. Calculated answers have still not met a run. The 2026-09-28 entry has the details.

Automated suite: **382 tests, 380 passing and 2 skipped, none failing**. The one that used to
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
**Skill environments are tested with fake Docker only: no live build and no run yet.** A Windows
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
- **The build** runs in setup, after the model probe and before the run or planner exists:
  1. a resolver container, the only container with a network, runs `pip download` for wheels only;
  2. Python checks and hash-locks the wheels;
  3. an offline installer applies the lock with `--require-hashes`, then `pip check`;
  4. `docker commit` makes the image, tagged `sci-verifier-env:<key>` and cached by labels.

  Any failure stops the run before a planner is spent.
- **Only subject trials use the built image.** Calculations, evaluators, scoring and catalog
  requalification keep the operator's image, so no package the skill chose runs where keys are
  produced or trials scored. The image is folded into the subject identity (`--subject-image` to
  the internal server) and `environment_digest` includes the record.
- **The planner** gets a pinned block rendered only from checked values, and the full record as the
  `environment` context section. A skill changed between setup and `load_submitted_skill` ends the
  run as `source_changed`.
- **Settings:** `package_index` (null by default), `max_package_bytes` and `max_packages`.

Verification of items 4 and 5:
- Suite 349 → 382 tests: 380 passing, 2 skipped, none failing.
- 31 new tests in `test_environment.py` run on fake Docker. Among them, a guard checks that only
  `environment.py` gives a container a network.
- Twelve one-line mutations of the safeguards were each caught.
- `resource-policy.md`'s new section was kept short so that the historical verification profile's
  bootstrap stays under its 200,000-byte test bound (199,805).
- **Not verified:** a real resolve and build, and a run in the built image.

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
6. **The timeout.** The app passes 5,400 s. `0aeca4c6` used 3,827 s for five claims, and a first
   environment build adds a few minutes of setup.
7. **For a skill environment:** the operator sets `package_index` (e.g. `https://pypi.org/simple`)
   in `.verifier/local-settings.json`. The first build downloads the scikit-survival stack, about
   100 MB of wheels, once. The live build check under "Recommended next action" should come first.

### Cleaning the previous run

Move, do not delete, into the session scratchpad:
- `.verifier/runs/0aeca4c6-5f2c-4d72-87a4-e8452340a5dc`
- `.verifier/attempts/f32cd389-5e51-4b87-adb9-b17de85e397d`
- `.verifier/subject-runs/0aeca4c6-5f2c-4d72-87a4-e8452340a5dc`
- the nine candidates it wrote at `local-reference-comparison-6`, dated 2026-09-28

Keep the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs and its five
candidates. Leave `.verifier/store/` alone: environment build records live there. `d416f79d`'s
files are already in an earlier session's scratchpad.

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
   - The setup log's `preflight.environment` status. The first time should be `built`, a second
     run `reused` with no networked container.
   - The lock, and whether `pip check` passed with the skill's numpy/pandas pins over the RDKit base.
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

Prove skill environments live, then run scikit-survival again. The question is whether subjects
execute the library once it is installed, and whether planners design executed cases.

### Recommended next action

With the operator's go-ahead (it downloads about 100 MB from PyPI and edits the operator's
settings):
1. Set `package_index`.
2. Run `prepare_environment` alone on scikit-survival over the RDKit image.
3. Confirm, in this order:
   - the lock is written;
   - `pip check` passes with the skill's numpy/pandas pins;
   - the image carries its labels;
   - a `--network none` container imports `sksurv`;
   - a second call reuses the image with no networked container;
   - `package_index: null` gives `disabled`.

It is finished when all six hold, or the first that fails is named. After that, a scikit-survival
run from a new session answers item 7 of "What to check in the run".
