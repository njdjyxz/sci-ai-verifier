# Development plan

This file introduces the project to whoever picks it up next, records what is true of it
today, and holds the roadmap. It was rewritten on 2026-10-25 at the hand-over from the first
operator. The dated log of every development session is in
[DEVELOPMENT-LOG-ARCHIVE.md](DEVELOPMENT-LOG-ARCHIVE.md); read its last entries for the
texture of recent work, and this file for the whole.

## How to maintain this file

1. **This file is the current state and the roadmap; the archive is the log.** After a
   session's work, append a dated entry to the archive (`## <Author>: YYYY-MM-DD`, one per
   agent per day, edited in place for the rest of that day, in `America/Los_Angeles`) with
   five fields: current stage and status; what has been done, with commits and the
   verification performed; urgent next steps, or `None`; suggested next move; recommended
   next action, bounded, with how to recognise that it is finished. Then update the sections
   below that the work changed: "Current state", "Known defects and open questions", and the
   roadmap. Keep this file free of dated narrative.
2. **One owner per fact.** The contracts under `skills/scientific-verifier/references/`
   outrank this file. When this file and a contract disagree, the contract is right and this
   file is stale. Do not restate a rule, a limit or a list that a contract owns; link it.
   [CLAUDE.md](CLAUDE.md) names the owners.
3. **Separate confirmed facts, decisions and recommendations.** Never present a proposed
   change as implemented or tested. Live acceptance comes only from a recorded live run.
4. **Link files by relative path.** Record what was committed and pushed, and what was not.

## 1. What this project is

A personal, local verifier for scientific agent skills. A *skill* is a folder with a
`SKILL.md` and often scripts and reference files, written to make an AI agent do a piece of
scientific work (compute descriptors, design primers, fit a kinetic model). Nobody checks
whether such skills are right. This verifier does: given a skill folder, it produces a
report that says, claim by claim, what was tested, how, what the evidence is worth, and
whether the skill's own rules and code held up.

The design commitments, each of which has been tested against a failure:

- **The skill is run, not read.** Each claim is tested by tasks: Python builds input files,
  three fresh Claude Code sessions run the skill on them inside a disposable container, and
  Python checks every output against a value it planted or quoted from a reference it
  retrieved itself. No AI session reads a trial's answer to decide whether it is right.
- **Grade and status are independent.** The evidence grade (A, B, C, D, U) says how strong
  the evidence is; the status (pass, fail, inconclusive) says what the evidence showed. A
  unanimous fail is graded exactly like a unanimous pass. An operational failure (a refused
  or timed-out session, a package that would not install) is reported as such and never
  becomes a verdict. [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md)
  owns the grade standards.
- **No one enters a grade.** The planner proposes the grade its design supports, Python
  refuses any proposal its recorded facts cannot carry (in either direction: aiming low is
  refused like overclaiming), and a critique session that never saw the planning can only
  lower it. "Negotiated evidence grade" in
  [`local-contract.md`](skills/scientific-verifier/references/local-contract.md) owns the rule.
- **The tester follows the skill and reports disagreement.** Since 2026-10-14 the test
  session must apply the skill as written, even when it thinks the skill is wrong, and say
  where it disagrees. Before that, test sessions silently corrected skills and passed them.
- **Python owns state; Claude owns judgment.** Claude Code is the planner and the test
  subject; Python owns the state machine, tool legality, limits, persistence, execution and
  the grade ceiling. The planner cannot call a tool the state does not allow.
- **Everything is content-addressed and reproducible.** Snapshots, references, task designs
  and results are stored by digest; a run pins the exact model, image and settings it used.
- **Local, on a subscription.** It runs on the operator's computer with the operator's Claude
  subscription through the installed Claude Code CLI. A hosted, multi-user product is a
  separate future project, not a goal here.

Non-goals, settled on 2026-09-11 and not reopened: a text-only or chemistry-only release, a
same-chat demonstration as the product, and any human sign-off gate that assigns a grade.

## 2. How a verification works

The public action is **verify this skill**: the MCP tool `verify_skill` served by
`python scripts/verify.py serve-local`, or `python scripts/verify.py verify <path>` on the
command line. One call blocks until the run ends and returns the report paths. In outline:

1. **Load.** Python snapshots the skill folder (bounded, no links, no traversal), reads its
   files, records safety findings (plain facts about the files, never run), and gives the
   planner a state token. Every workflow tool call must carry the newest token; a call with
   a stale one is refused and counts against the illegal-transition budget.
2. **Claims.** The planner divides `SKILL.md` into claims, each a group of whole sections;
   sections about the software rather than the science may be set aside with a reason.
   [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md) owns the rules.
3. **Environment.** If the skill declares packages and the settings allow a package index,
   Python installs exactly those packages into a copy of the base image, for this skill's
   trials only; otherwise the trials use the operator's pinned image. A declared package
   that cannot be installed stops the whole skill with `skill_environment_unavailable`.
4. **Tasks and keys.** For each claim the planner designs tasks, writes a generator for their
   input files, searches for references, and writes a reference solution; Python runs the
   generator and the solution, pins the files and the expected values, and qualifies the
   design mechanically (leak checks, discrimination, scope). The planner proposes a grade;
   Python computes the ceiling its facts allow and refuses a mismatch.
5. **Critique.** A fresh no-tool session reads the claim, the design, the provenance and a
   fixed rubric, and answers whether each task counts and what grade the evidence supports.
   It can only lower. The planner revises or accepts; the budget is one round per grade.
6. **Trials.** For each task, three fresh Claude Code sessions run the skill in the
   container on the pinned inputs and write a results file. Python reads the results,
   compares field by field, and records each trial's status and the tester's disagreements.
   One model per trial set; a model change voids the claim.
7. **Grade and status.** Python settles the grade from the counted tasks and the critique,
   derives the status from the trials (unanimity), and records every limit and reason.
   Claims that could not execute go to a separate documentary assessment (D) or end at U.
8. **Report.** `report-card.md` and `.json` under `.verifier/runs/<run-id>/`, plus an HTML
   page under `.verifier/reports/` whose plain-language fields the calling agent fills in
   afterwards. The attempt's timeline is under `.verifier/attempts/<attempt-id>/`.

What each step may and may not do is in the contracts; the states and the state x tool matrix
are in [`workflow.md`](skills/scientific-verifier/references/workflow.md), each tool in
[`tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md), the host's
duties in [`runtime-contract.md`](skills/scientific-verifier/references/runtime-contract.md),
and the local profile's enforceable behaviour in
[`local-contract.md`](skills/scientific-verifier/references/local-contract.md).

## 3. Architecture and repository map

| Path | What it is |
| --- | --- |
| `skills/scientific-verifier/SKILL.md` | The planner's instructions. Loaded into every planner session. |
| `skills/scientific-verifier/references/` | The contracts, in dependency order: `workflow.md`, `tool-contracts.md`, `runtime-contract.md`, `artifact-contracts.md`, `resource-policy.md`, `evidence-rubric.md`, `local-contract.md`, `local-tasks.md`. The `stage2-`, `stage3-`, `verification-` and `demo-contract.md` files belong to the historical profiles (section 7, item R4). |
| `src/sci_ai_verifier/local_entry.py` | The one public action: starts the planner's Claude Code process with the pinned instructions, serves it an internal MCP server, and collects the report. The planner prompt lives here. |
| `src/sci_ai_verifier/local.py`, `local_tasks.py`, `local_science.py`, `local_candidates.py`, `local_resources.py`, `local_catalog.py`, `local_config.py` | The local profile: operations the planner calls, task tests, grade ceilings and negotiation, references and saved task designs, datasets and app adapters, portable bundles, operator settings. |
| `src/sci_ai_verifier/claude_runner.py`, `sandbox.py`, `environment.py`, `subject_server.py`, `process_guard.py`, `execution_control.py` | Fresh bounded Claude Code processes; disposable Docker containers; skill environments; the private tools a subject container may call; Windows job ownership; cancellation and deadlines. |
| `src/sci_ai_verifier/documentary.py`, `safety.py`, `answers.py` | Fresh no-tool sessions (critique, judges, documentary assessor); safety findings; expected values and their quotes. |
| `src/sci_ai_verifier/tools.py`, `agent.py`, `storage.py`, `runlog.py`, `mcp.py`, `internal_server.py` | The profile-aware dispatcher and tool schemas; runtime bootstrap and the illegal-transition and repair budgets; content-addressed objects and the event journal; the redacted workflow log; the MCP transport; the private child-process entry. |
| `src/sci_ai_verifier/report_html.py`, `reporting.py`, `partial_report.py` | The HTML page, deterministic report accounting, and the partial report written when a planner stops. |
| `src/sci_ai_verifier/catalog*.py`, `routing.py`, `scientific.py`, `evaluation.py`, `audit.py`, `execution.py`, `planning.py`, `fixtures.py`, `demo.py`, `app_bridge.py` | Shared with, or belonging to, the historical profiles. `catalog_release.py` and `catalog_publication.py` serve the local catalog commands too. |
| `scripts/` | `verify.py` (CLI, `serve-local`, `doctor`, and `serve --profile` for the historical profiles), `configure_local.py`, `report_html.py`, `local_catalog.py`, `local_policy.py`, `record_critique.py`, `run_local_fixture.py`, `build_local.py`, `catalog_release.py`. |
| `tests/` | The automated suite and the recorded live replies under `tests/recorded/` that pin the critique, judge, assessor and refusal formats. The recordings were made on this project's machine and carry its temporary paths; they are data, not configuration. |
| `images/rdkit/` | A reviewed image: pinned `python:3.12-slim`, RDKit, pandas, SciPy, hash-pinned. |
| `examples/` | Synthetic fixtures: `local-reference-fixture` for `run_local_fixture.py`, `chemical-mass-fixture` for the historical verification profile's tests. |
| `registry/`, `catalog/` | Reviewed catalog data (empty by rule) and the historical catalog manifest. |
| `.verifier/` (ignored) | `local-settings.json`, `runs/`, `attempts/`, `reports/`, `candidates/`, `registry/`, `objects/`. Private; never committed. |
| `INSTALL.md`, `LOCAL-CONFIG.md`, `README.md`, `CLAUDE.md` | Setup on Windows and macOS; configuration reference; the front page; the rules for agents. |

Run data of the first operator lives outside the repository too: thirty staged third-party
skills with their ledger under `verifier-submissions/batch-2026-10-20/` beside the checkout,
their answer keys under `verifier-keys/batch-2026-10-20/`, and the hand-over package (summary
PDF and all report pages) under `verifier-handoff-2026-10-25/`. Those folders are the
operator's, not part of this repository.

## 4. Current state (2026-10-25)

**Version 0.8.0 on `main`, pinned to `claude-opus-5-5`** (Claude Code 2.1.302 or newer; the
pin moved from `claude-opus-5` on 2026-10-21, which started a new series). The automated
suite passes: 439 tests, 1 skipped, on 2026-10-25 after the hand-over cleanup, which removed
the desktop package tests (448 tests, 2 skipped, before it). No third-party Python packages
are required.

**Live acceptance is partial, with far more evidence than a month ago.** Every live run from
the first complete one (glycoengineering `76ce4af1`, 2026-09-16) to the end of the
question-test era is listed, with its result, in the archive's "Current state" table as it
stood on 2026-10-21 (the entry of that date, and the entries it points to). Since task tests
replaced question tests on 2026-10-05 (version 0.8.0), the verifier has completed:

- the first task-test runs on tooluniverse-dose-response and western-blot-quantification
  (2026-10-06 and 2026-10-07), four demo-skill runs for grades D and U (2026-10-13), a run on
  a280-quant on the fourteen review decisions (2026-10-19), and
- **a thirty-skill sweep of third-party skills, 2026-10-21 to 2026-10-24**, the project's
  first measurement of itself at scale.

### The thirty-skill sweep

Thirty unverified biology and chemistry skills were collected byte for byte from thirteen
public repositories in four strata: 8 known-good (false-alarm control), 10 pre-fix (an earlier
upstream revision that a later upstream commit corrected, the diff kept outside the tree as
the key), 6 aggregator copies, 6 wild. All thirty were attempted, unattended, one at a time,
under a usage rule. Totals, from the saved report cards:

| Measure | Value |
| --- | --- |
| Runs with graded claims | 24 (5 refused at the package-build stage; 1 planner fault) |
| Claims | 106: grade A 56, B 20, D 25, U 2, no grade 3; status pass 57, fail 22, inconclusive 22, withheld 5 |
| Scored trials | 870 |
| Cost | $441 at API prices for the subscription usage; graded runs mean $18, median $16; 21 hours of run time |
| Skills with at least one failed claim | 14 |

What it established:

- **No false alarm.** The five known-good skills that ran cleanly passed every counted trial.
  The one known-good failure (pkpd-modeling's terminal-window rule) is a real weakness.
- **Findings are reliable; coverage is not.** None of the ten keyed upstream errors was
  confirmed by a test: two skills never built, five were misses by omission (no task on that
  section or statement), two by abstention (the documentary reading marked the statement
  not addressed), one partial. None was a wrong pass. Six of those eight runs found a
  different real defect in the same skill.
- **Defects reproduce across copies; grades do not.** The Lipinski rule-of-five error
  appeared in four skills from three catalogs and was caught in every trial. A claim that
  settled at A in one copy settled at B or D in the other while the defect findings held.
- **Passes by compensation exist.** tooluniverse-enzyme-kinetics passed three claims at A
  while its testers reported a unit error in the bundled script; the grade cannot see it,
  the disagreement reports can.
- **Environment losses are the biggest single loss.** Five skills were refused because a
  declared package has no wheel for the sandbox's Python 3.12 on Linux, is renamed, or is
  not on PyPI; one built but would not import; one lost its only trial to the 600 s
  per-trial limit. Three claims were lost to provider safety refusals.
- **One verifier fault.** datamol `8ea6c851`: the planner sent nine file reads in one message
  and spent the illegal-transition budget of 8 before seeing a result. Diagnosed from the
  run's events and fixed in commit `4cb56f8` (the planner prompt says one call per message
  and that a plain read rotates the token; the local budget is 32). Not yet re-run.

The ledger with one row per skill, the per-run report pages and the summary PDF are in the
operator's `verifier-handoff-2026-10-25/` folder; the keys stay in `verifier-keys/`.

### What is and is not established

Established by live runs: the A and B branches settle grades; the critique lowers grades and
rejects keys; the documentary fallback runs; safety refusals, timeouts, model changes and
build failures are reported as operational, never as verdicts; task tests catch wrong rules
and wrong code in real skills; the tester's disagreements surface defects the grades miss.

Not established: grade C has settled once, on a case profile, and `qualify_local_evaluator`
has never been exercised live; the catalog contribution path (export, draft PR, review,
revision) has never been run against GitHub; no run has been made on macOS; Opus 5.5 as the
critic has not been measured by replay the way Opus 5 was (2026-10-08); no live run has yet
shown the one-call-per-message sentence working.

## 5. Working conventions for the next agent

[CLAUDE.md](CLAUDE.md) is the rule set; these are the facts behind the rules that cost the
most to relearn.

- **Contracts before code.** A change to tool legality edits the matrix in `workflow.md` and
  the tool's section in `tool-contracts.md` in the same commit. A change to local behaviour
  edits `local-contract.md` or `local-tasks.md` first.
- **Restart before a run.** A `serve-local` started by a desktop session keeps the code it
  loaded; after any change under `src/`, start a fresh session (or use `scripts/verify.py`
  directly, which loads fresh code).
- **Never read a run's logs while it runs.** Opening `workflow.jsonl` on Windows broke the
  log's atomic replace and lost two claims (run `74000d89`). Watch directories instead.
- **Runs cost real usage.** $5 to $35 and 20 to 70 points of the 5-hour subscription window
  each; start one only when the window is below about 45% used, and ask the operator before
  starting any run that was not explicitly authorised. Check Docker's engine first: a
  stopped daemon costs a whole run.
- **Read full tool results from `runs/<run>/events/*.json`**; `workflow.jsonl` clips long
  results at about 16 KB.
- **A changed model pin starts a new series.** Probe the CLI first
  (`claude -p "Reply OK" --model <id>`); runs on different pins are not compared blindly.
- **A changed critique rubric needs a live re-recording** (`scripts/record_critique.py`,
  about $1); the recording under `tests/recorded/` pins the format the code parses.
- **Fixes need evidence across skills.** Before adding a rule drawn from one run, scan the
  kept runs of other skills; bugs may be fixed at once, rules may not.
- **Windows specifics.** Scripted edits of repository files must write bytes or
  `newline="\n"` (`.gitattributes` pins LF). Long temporary paths exceed the 260-character
  limit unless the extended-path form is used; 25 leftover folders once broke one test.
- **Commit to `main`, push when asked.** No branches are left behind.

## 6. Known defects and open questions

Collected from the archive's entries of 2026-10-13, 2026-10-19 and 2026-10-25 and the sweep,
deduplicated. Each is the operator's to rank; none is built.

1. **Misses by omission.** The planner tests a subset of what a claim states and lists the
   rest as untested. In the sweep that list is where every keyed error lived. Options:
   require a task for every statement or an explicit reason why not; make the critique ask
   which statements no task reaches and treat an unreached rule as a coverage objection.
2. **Passes by compensation.** A tester that silently corrects a skill's error passes the
   task. Options on the table since 2026-10-13: (a) a display-only "testers disputed this
   test" flag, built on 2026-10-19 and found to fire on any disagreement; (b) a judged
   dispute check, two fresh judges reading the job, the keys with their quotes and the
   disagreements, holding a claim below A when both say the key or the skill's rule is wrong
   (about $0.05 to $0.10 per flagged test, one live recording); (c) have the tester name the
   step it disputes in a fixed form so Python can tell a key dispute from a complaint.
3. **Environment losses.** Wheels-only builds for Python 3.12 exclude every skill that needs
   a package without such a wheel. Options: a conda-based or source-building base image; a
   per-skill image the operator builds on request; or declaring such skills out of scope in
   `INSTALL.md`. Related: a nonexistent declared package blocks every section of a skill,
   including ones that need nothing (glycoengineering); whether `--python` in an install
   command may be treated as harmless; sdist-only packages.
4. **The 600 s per-trial limit** lost single-cell-rna-qc's only trial, and the first trial is
   never retried. Decide whether a timeout on trial one retries once, and document the
   setting's choice for long skills.
5. **Batched planner calls.** Opus 5.5 batches tool calls; the one-call-per-message sentence
   and the 32 budget are in place but unobserved live. If batches persist, make an accepted
   read keep the token (changes `tools.py`, `workflow.md`, `tool-contracts.md`,
   `runtime-contract.md` and inverts one test).
6. **What status grade U carries.** The rubric's table says `null` with
   `no_reference_grade`; three other places and part of the code say `inconclusive`.
   Recommended: `null`, since a U has no reference to hold a verdict against.
7. **A critique, judge or assessor session that fails before replying ends the claim.** One
   bounded second session for a non-schema failure is recommended; it costs a session.
8. **Repeated whole-skill disagreements** fill a page with near-identical blocks when every
   trial objects to the same section.
9. **Rules the planner never searches for** end as "not looked up" rather than U.
   `local-tasks.md` tells the planner U needs a search; a skill with a cut-off of its own
   (protein-bench-helper was the candidate) would show whether it does.
10. **Catalog requalification** (2026-10-08) and the catalog contribution path have no live
    test.
11. **Two directive forms the staging guard does not refuse** (a backtick before `!`, a tilde
    fence); whether Claude Code expands either is unknown. Try both once against the CLI.
12. **Re-record `critic-refused-tool.jsonl`** under the current rubric (about $1).
13. **`report_html.py`'s question-era branches** (about 120 lines) render only runs from
    before 2026-10-05. Delete with the `mixed` fixture once those run folders are gone.
14. **Minor labels** noted in the 2026-10-19 review and left alone: the MCP host closing stdin
    is logged as the operator's cancellation; a `taskkill` timeout escapes `execute`'s handler;
    an installer container and wheels volume leak if Python dies mid-build; implied imports
    can exceed the declared requirement cap inside `max_packages`.

## 7. Roadmap

In priority order. Each item names what done looks like. R1 and R2 are the two findings of
the sweep that change what the reports mean; R3 recovers the skills the sweep lost; the rest
is hygiene and reach.

- **R1. Close the coverage gap (open question 1).** Change `local-tasks.md` and the planner
  prompt so that every statement a claim makes is either tested by a task or named with a
  reason, and let the critique object to an unreached rule. Done when the ten pre-fix skills
  from the sweep are re-run on the change and the report of each either tests the keyed
  statement or names it in the untested list with a reason, and at least one key is caught.
- **R2. Decide what a disagreement does to a grade (open question 2).** Build option (b) or
  (c), with one live recording, and re-run tooluniverse-enzyme-kinetics and medicinal-
  chemistry. Done when the enzyme-kinetics unit error holds that claim below A, and the
  biopython-v2 copy's complaints about a missing folder do not change its grades.
- **R3. Widen the sandbox (open question 3).** Choose between a conda-based base image and
  operator-built per-skill images; document the choice in `LOCAL-CONFIG.md`; make a missing
  package block only the sections that need it. Done when tellurium, flowkit and libsbml
  build, or are reported as out of scope by a rule the install guide states.
- **R4. Retire the historical profiles.** The Stage 2, Stage 3, chemical verification and
  demo profiles are reachable only through `serve --profile`; the desktop extension that
  exposed them was removed on 2026-10-25. The profile code is wired through `tools.py`,
  `agent.py` and `storage.py`, and `catalog.py`, `catalog_release.py` and
  `catalog_publication.py` serve the local catalog commands too, so this is a bounded
  refactor, not a deletion: remove `serve` and `request` from `__main__.py`, `demo.py`,
  `fixtures.py`, `routing.py`, the profile branches of the dispatcher, the four historical
  contracts and their tests (`test_stage2.py`, `test_stage3.py`, `test_verification.py`,
  `test_demo.py`, and `examples/chemical-mass-fixture`), keeping every module the local path
  imports. Done when `python scripts/verify.py` offers only `verify`, `serve-local` and
  `doctor`, the suite passes, and a kept 0.8.0 run still renders.
- **R5. Re-run datamol and single-cell-rna-qc** on the current commit (open questions 4 and
  5), and count batched planner calls in every later run by grouping tool_use blocks by
  message id in `workflow.jsonl`. Done when datamol completes and a longer per-trial limit
  gives single-cell-rna-qc a verdict or a named reason.
- **R6. macOS acceptance.** Follow `INSTALL.md` on a Mac, run `run_local_fixture.py`, then one
  small live verification. Done when the install guide's macOS section says "verified on"
  with a date, and any POSIX defect (the process guard is Windows-only) is fixed or recorded.
- **R7. Measure Opus 5.5 as the critic** by replay, as Opus 5 was on 2026-10-08
  (`scripts/record_critique.py`, about $1 a packet), and settle the critique effort for the
  new series.
- **R8. Exercise the catalog contribution path once** against GitHub: export a candidate,
  open the draft PR, read a comment back, revise. Done when `local_catalog.py publish` and
  `review` have each run live and the plan records the PR.
- **R9. Settle the small open questions** (6, 7, 8, 9, 11, 12, 13, 14), each a bounded
  change with a test, in any order.
- **Later, a separate project:** a hosted multi-user or API deployment. Not part of this
  repository's definition of done.

## 8. History, condensed

Full text in [DEVELOPMENT-LOG-ARCHIVE.md](DEVELOPMENT-LOG-ARCHIVE.md). Designs described here
were often later changed; the archive records how, and the contracts outrank both.

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
  instructions.
- **Claude 2026-09-15** — Requested repair and full code review: three design defects
  fixed, dead files removed, `tmp/legacy_fixed_workflow/`, `reviews/` and the superseded
  `evaluators/chemical_mass/` helper deleted.
- **Claude 2026-09-16** — First live run reached real Claude Code and failed before
  snapshotting (`source_not_authorized`). Two host-boundary defects fixed with tests. Rerun
  `76ce4af1` completed end to end: four claims at grade A, 66 of 66 trials passed.
  Acceptance declared partial, A-branch only.
- **Claude 2026-09-18** — Two sar-analysis runs; the second graded but discarded its most
  useful finding. Proposed the six-axis report card.
- **Claude 2026-09-21** — The six-axis redesign built, contracts first: grade no longer
  welded to behaviour. Run `e13f50ee`: six claims, first settled B. Model pin confirmed live;
  `subject_model_changed` seen from a CLI fallback.
- **Claude 2026-09-22** — Four sar-analysis runs. Indexed choices, first-line reading of
  replies; every false failure of the week was a correct answer the scorer could not read.
  `local-contract.md` made authoritative, every duplicated fact given one owner. An Opus 5.5
  switch failed (CLI too old) and was reverted.
- **Claude 2026-09-23 to 2026-09-25** — Runs `7f88fbef` (stopped on the session limit),
  `b0955d2f`, `3dc02567`, `84e90683`, `31b67427`, `3b3f3c94` (first settled C), `d416f79d`.
  One model per trial, a disclosed end-of-run re-run, a startup model probe, the fallback D,
  an RDKit sandbox image, critique rubric v7 with leak shapes, claim-only answers measured
  by Python; a starving workflow log and reused answers under an old case ID fixed.
- **Claude 2026-09-28** — Typed reply schemas; calculated answers drafted; run `0aeca4c6` on
  scikit-survival, the first non-chemistry skill: the fallback D ran, a safety refusal voided
  a claim, and the sandbox could not run the package, which led to skill environments.
- **Claude 2026-09-29** — Typed answers and the AI reader; run `d3892f6c` with claims sized to
  their tests; every sandbox command read the skill's own references rather than running it.
- **Claude 2026-09-30** — Runs `fbd49132` and `26312681` on tooluniverse-dose-response; the
  planner told to test each fact a claim states; the critique given Python's search record.
- **Claude 2026-10-01** — Runs `3303fd93` and `1d1c3b6e`; a plan that settles at its own
  proposal comes back; the planner is told its time left.
- **Claude 2026-10-02** — Run `90c60cbe`: one false fail; a bar for changes so that fixes do
  not overfit to one run.
- **Claude 2026-10-05** — An HTML page after every run; whole-skill task tests built;
  question tests removed; version 0.8.0; a recorded task critique.
- **Claude 2026-10-06** — Runs `f84c131c` and `2bef9e0d`, the first with task tests; a
  reviewed command table for ToolUniverse; the coverage return; departures and passes on
  tolerance recorded.
- **Claude 2026-10-07** — The critique answers questions and Python gives each task's
  verdict; run `cfe9e57a` (critique at xhigh, 144 minutes).
- **Claude 2026-10-08** — Run `50104eac` stopped on the session limit; `55d345a3` on
  neurokit2; reference solutions run where trials run; `2f395087`; the critique's effort and
  model measured by 42 replays: Opus 5 at high.
- **Claude 2026-10-13** — Two demo skills for grades D and U; a refused tool call no longer
  ends a critique; how a claim shows the rules it leaves unsourced; the tester follows the
  skill and its disagreements are reported; safety findings; U split from near misses.
- **Claude 2026-10-19** — Code review before more skills: a grading bug, the two known bugs,
  six more fixes, fourteen decisions built, rubric v9 re-recorded; first live run on them
  (a280-quant `0e471ea0`, A and U); the disputed flag's sentence corrected.
- **Claude 2026-10-21** — The pin moves to Opus 5.5; thirty skills staged for a stratified
  sweep.
- **Claude 2026-10-21 to 2026-10-24** — The sweep run unattended, 29 completed or refused
  runs recorded in the ledger as they finished.
- **Claude 2026-10-25** — datamol's planner fault diagnosed and fixed (one call per message;
  budget 32). Hand-over: this file rewritten, the dated entries archived, the desktop
  extension builder and its fixtures removed, `INSTALL.md` written for Windows and macOS,
  the sweep summarised for the PI.

## 9. Glossary

- **Claim**: a group of whole sections of a skill's `SKILL.md`, tested together.
- **Task**: an input set Python builds, on which the skill is run; a **key** is the expected
  value Python planted or quoted, with its quote.
- **Trial**: one fresh Claude Code session running the skill on one task; three per task by
  default. **Counted** tasks are those the critique accepted as sound and in scope.
- **Evidence grade** (A, B, C, D, U) and **status** (pass, fail, inconclusive): see
  `evidence-rubric.md` and section 1.
- **Critique**: the fresh session that reviews a task design and can only lower the grade.
- **Documentary assessment**: a fresh no-tool session judging cited sources; grade D.
- **Disagreement**: a tester's report that it followed a step of the skill it believed wrong.
- **Safety findings**: plain facts about a skill's files, read and never run; no grade.
- **Skill environment**: the image built from the packages a skill declares, for its trials.
- **State token**: the value every workflow call must carry; refusing a stale one is how
  Python serialises the planner. The **illegal-transition budget** (32, run-wide) and the
  **repair budget** (32) are in "Legal operations" of `local-contract.md`.
- **Attempt** and **run**: an attempt is one `verify_skill` call with its log; a run is the
  scientific record it creates once the skill is loaded.
