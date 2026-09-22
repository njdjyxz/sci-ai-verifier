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

**Live acceptance is partial.** Three runs have completed end to end:

| Run | Skill | Result |
| --- | --- | --- |
| `76ce4af1` (2026-09-16) | glycoengineering | 4 claims at grade A, 1 operational limitation |
| `1bb3f07a` (2026-09-18) | sar-analysis | 1 at A, 1 at D, 2 voided by faults |
| `e13f50ee` (2026-09-21) | sar-analysis | 4 at A, 1 at B, 1 voided by a fault |
| `fb64115f` (2026-09-22) | sar-analysis | 2 at A, 2 at B, no faults, 51 of 51 observed |

What that does and does not establish: the **A and B branches** both now carry settled
grades from live runs, and run `fb64115f` is the first to grade every claim it extracted.
**Grade C and `qualify_local_evaluator` have never been exercised.** The documentary path
has run twice, once to completion and once rejected, and in neither of the last two runs.
The indexed-choice rules committed on 2026-09-22 have not yet been seen by a live planner.

No run has yet produced a scientific result free of false failures: `e13f50ee` reported two
from answer wording and `fb64115f` one from capitalization. Each was fixed after the run
that exposed it, which is why the next run reads the planner's behaviour rather than the
grades.

Automated suite: **260 passed, 2 skipped**. Fixtures remain synthetic, reviewed registries
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

## Claude: 2026-09-22 (third sar-analysis run; closed choices become indexed)

### Current stage and status

Run `fb64115f-c50f-42e6-8408-8ed4feacab43` **completed end to end** and is the cleanest run
the project has produced: four claims, all four graded, **51 of 51 observations obtained and
evaluated**, zero faults, zero invalid, zero split cases. 38 minutes, $9.73, 40 steps,
observed model `claude-opus-5`. Grades A, B, B, A; three pass, one fail.

**The 2026-09-21 fixes work.** Every multi-word answer became a closed choice, the wording
lottery is gone, and — the part that had never happened before — the critique **objected and
lowered the grade**, twice. Two claims whose mechanical ceiling was A settled at B after two
critique rounds, on exactly the naming-versus-substance ground the rubric sentence added.

Two defects were found and fixed in the process. One was in yesterday's own commit.

### What has been done

**1. `METHOD_VERSION` was not bumped when the qualification rules changed** (fixed, this
session). The catalog import path re-qualifies a candidate against current rules, but the
local lookup path in `candidates()` does not — it filters on `method_version` and trusts
what it finds. All thirteen saved candidates still read `local-reference-comparison-1`, so
the eight prose-answer candidates from run `e13f50ee` were still selectable and the planner
could have reused them, skipping the new rule entirely and making the run worthless as a
test of it. Caught before starting. That string is the only thing standing between a
superseded rule set and a later run, and there is now a test that says so.

**2. The run, claim by claim.** Docker Desktop was stopped again and was started first.

| Claim | Grade | Status | Trials | Accuracy |
| --- | --- | --- | --- | --- |
| `rdFMCS` threshold | A | pass | 12 of 12 | 12/12 |
| `RGroupDecompose` | B | pass | 15 of 15 | 15/15 |
| `makeDummiesQueries` | B | pass | 12 of 12 | 12/12 |
| pIC50 | A | **fail** | 12 of 12 | 9/12 |

**3. The naming rule fired, and the revision loop with it.** Two claims had
`evidence_ceiling: A` and `settled_ceiling: B` after two rounds, so the critique did what
the previous run's critique had declined to do. Its own words:

> "The claim is behavioural ..., but no case invokes RGroupDecompose on any molecule or
> core; the behavioural half of the claim is entirely untested and only the vocabulary of
> the output is probed."

> "Cases 3 and 4 do not test the claim ... both can be answered by name-level familiarity
> with the struct while holding an incorrect belief about what makeDummiesQueries does."

Eight candidate versions were written for four claims, so the planner revised rather than
accepting. This is the pass condition the previous entry set, met.

**4. The same bug returned in a new costume.** The pIC50 failure is not a finding. Case
`molar-unit-open` expected `"molar"` and observed `"Molar"` — capitalization — and failed
3 of 3, so it is a deterministic false failure rather than a coin flip. The 2026-09-21 rule
required a whitespace-free token, and `molar` is one; string equality is still case
sensitive. The multi-word hole was closed and the single-token hole was left open.

Case-insensitive comparison is not the answer: in cheminformatics case is semantic, `c` and
`C` in SMILES being aromatic and aliphatic carbon.

**5. Closed choices are now indexed** (`choice`, a third installed comparison method). The
subject replies with the **option number**, compared numerically, so no wording, casing,
plural or whitespace of a right answer can score as a wrong one — the whole class is
structurally impossible rather than patched. A reply that is not a number returns
`invalid`, which reports a harness problem instead of a verdict about the skill; previously
a surface slip was indistinguishable from a real defect.

Because the index is the planner's own ordering and appears in no reference, the
**provenance anchor moved one level down**: the option the index selects must be the
verbatim quote. Same guarantee, one indirection. `token_exact()` and `answer_text()` in
`local_science.py` resolve the option behind the index so the grade still rests on quoted
bytes.

`exact` reverts to open answers only and no longer takes options. An open answer must have
a forced surface form: a number, or a token fixed by a case change, digit or underscore.
`molar`, `greater`, `true` and `three` are therefore no longer legal open answers.

**6. Four alternatives minimum, plus a reserved `none of these`.** The previous floor was
two, and this run's critique independently flagged that as the weakest item it saw:
"combined with only two options it is the weakest of the four items." Arithmetic agrees —
over three trials a coin flip carries a case 12.5% of the time at two options and 1.6% at
four. Beyond four the return is negligible; the binding constraint is distractor
plausibility, which Python cannot check and which stays a planner assertion, now stated in
`QUALIFICATION_LIMITS`.

The reserved final option is never the answer, so scoring stays ungameable, but a case
whose trials all select it is far more likely to have a broken option set than a wrong
subject. That is a diagnostic to read, not a verdict: the claim still fails, but visibly
for the right reason.

**7. Verification.** Replayed against **78 distinct expected values** from all four live
runs: 53 stay open, 25 now require a choice. The 25 include every value that has ever
produced a false failure — `any-atom queries`, `ACS 1996 guidelines` and `molar` — plus
`true`, `false`, `larger`, `greater`, `enhanced`, `three`. Suite **260 passed, 2 skipped**
from a 257 baseline. The new rules were mutation-tested: disabling the surface-form check,
the reserved-option rule or the options-in-prompt check each fails a test.

### Decisions taken 2026-09-22

**1. Index the choices rather than loosen the comparison.** Operator's proposal. Turning
the answer into a number removes the surface-form question instead of managing it.

**2. Keep open answers where the surface form is already forced.** Numbers especially. The
pIC50 case that made the subject compute `-log10(1e-9)` and answer `9` was the strongest
evidence in the run: generation, not recognition. Turning arithmetic into a menu would
downgrade it, so the `choice` method is the default for everything else and not universal.

**3. A reserved always-incorrect option.** Operator's proposal, adopted with the framing
shifted from trap to diagnostic.

### Open questions for the operator

**1. Should the aggregation rule become a plan field?** Carried forward unchanged.

**2. Claim coverage fell from six to four.** The two that disappeared,
`DrawMoleculeACS1996` and `GenerateDepictionMatching2DStructure`, are the most
API-surface-flavoured of the six — exactly the kind the new rubric sentence says remains
legitimate. Claim extraction happens before qualification and varies between runs, so one
run cannot establish that the rubric edit caused this. It is the narrowing regression the
previous entry flagged, and it now has one observation behind it rather than none.

**3. A narrow capitalization residue remains by choice.** `forced_surface_form()` accepts
any token carrying both cases, so `Core`, `Threshold` and `Fuc` stay open answers. Their
case is genuinely semantic — a C++ string key, a property name, an SNFG symbol — but a
subject could still lowercase one. Tightening to require an *internal* case change
(camelCase) would catch them at the cost of turning legitimate scientific symbols into
menus. Not done; the looser rule is what was agreed.

**4. Recognition is untouched.** A choice can be passed by recognising the
conventional-looking option. This run's critique said so directly: "Closed-choice recall
with the correct wording present verbatim among the options tests discrimination, not
generation." Indexing does nothing about that, and neither does raising the option count.

### Urgent next steps, if any

None. Everything is committed, pushed and green.

### Suggested next move

Rerun `sar-analysis` and read the planner's behaviour rather than the grades, which are now
established across three runs.

### Recommended next action

Run `sar-analysis` once against this commit and answer three questions from the saved card.
Did the planner adopt `choice` for the 25 values that now require it, and did any case come
back `invalid` because a subject replied with option text instead of a number? Did claim
coverage return to six, or stay at four? Did any case draw unanimous `none of these`, and
if so was its option set genuinely broken? It is finished when all three have a recorded
answer. A run with zero false failures and no `invalid` replies would be the first clean
scientific result this project has produced.
