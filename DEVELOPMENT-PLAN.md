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

Every run above used Opus 5. The verifier's pin moved to `claude-opus-5-5` after run
`7efbdd8c`, so later runs begin a new series and are not directly comparable with these.

What that does and does not establish: the **A and B branches** both carry settled grades
from live runs, and the planner has now used all three comparison methods, including an
open `exact` case written specifically to make the subject generate an answer rather than
recognise one. **Grade C and `qualify_local_evaluator` have never been exercised.** The
documentary path has run twice, once to completion and once rejected, and in none of the
last three runs.

No run has yet produced a scientific result free of harness noise. The same fault has
appeared three times in different forms — a plural in `e13f50ee`, a capital letter in
`fb64115f`, markdown bold in `7efbdd8c` — each time a correct answer the scorer could not
read. The first two were reported as `fail`, falsely accusing the skill; the third was
reported as `invalid`, which is honest but still left three of four claims inconclusive.
All three are now fixed, and the reply reader was replayed against every saved
observation from `7efbdd8c` without changing a single passing verdict.

Automated suite: **265 passed, 2 skipped**. Fixtures remain synthetic, reviewed registries
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

## Claude: 2026-09-22 (third and fourth sar-analysis runs; indexed choices; replies read by first line)

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

**8. A general review of the repository** for conflicting directions, overlapping
instructions, ambiguous references and dead content. The expensive class is clean: the
local state x tool matrix in `workflow.md` was diffed mechanically against `CLAIM_LEGAL`
and `OPERATIONS` in `local.py` and matches exactly, every documented constant matches its
code constant, no relative link in any document is broken, no module-level definition of
262 is unreferenced, and no fixture under `examples/`, `tests/recorded/` or `catalog/` is
orphaned.

Four small problems were fixed directly. `evidence-rubric.md` contradicted itself inside
one sentence, opening with eligibility over "reference and test-bundle facts only" and
closing with "a statement about the reference"; the closing clause now says evidence
design, matching `POLICY["axes"]`. That drift is not academic -- it is what made a correct
proposal look like a design violation during this session's discussion.
`local-contract.md` and `LOCAL-INSTALL.md` still described two comparison methods after
`choice` was added earlier the same day. And `evaluators/` was removed: it held nothing
but `__pycache__` bytecode for the helper deleted on 2026-09-15, untracked and invisible
to `git status`, while its name implied the helper still existed.

**9. The fourth run answered the three questions the third left open.** Run
`7efbdd8c-80e6-4545-a641-82826316833e`: four claims, 57 of 57 observations obtained, zero
faults, zero missing, 45 minutes, $12.01, model `claude-opus-5`. Grades A, B, A, A.

| Claim | Grade | Status | Accuracy | Invalid |
| --- | --- | --- | --- | --- |
| `rdFMCS` threshold | A | invalid | 9/12 | 3 |
| `makeDummiesQueries` | B | invalid | 17/18 | 1 |
| pIC50 | A | pass | 15/15 | 0 |
| `RGroupDecompose` | A | invalid | 11/12 | 1 |

*Did the planner adopt `choice`?* Yes, and used all three methods deliberately: five
candidates were `choice`, one was `numeric` for the pIC50 arithmetic, and one was `exact`,
titled "remedy named from scratch". That last one was the planner's own response to a
critique objecting that choices test recognition — it switched a case to make the subject
generate the answer. The critique in turn lowered `makeDummiesQueries` from A to B after
three rounds, attacking recognition directly: "all six cases supply that identifier or its
documented description among the options, so the instrument tests recognition of the
answer."

*Did any case come back `invalid`?* Five did — but not for the predicted reason. The
question anticipated a subject replying with option text instead of a number. **Every one
of the five was the correct number, in markdown bold**: `**1**`, sometimes followed by a
paragraph of explanation. Counting those, the subject answered **57 of 57 correctly**. No
case produced a genuinely wrong answer.

*Did coverage return to six?* No. Four again, missing the same two API-surface claims.

*Did any case draw unanimous `none of these`?* No trial selected it, so no option set was
broken.

**10. Replies are read from their first line, with emphasis removed** (fixed this session,
contracts first). This is the same fault a third time, in a third form:

| Run | Correct answer | Scored as | Cause |
| --- | --- | --- | --- |
| `e13f50ee` | any-atom queries | fail | plural |
| `fb64115f` | molar | fail | capitalization |
| `7efbdd8c` | 1 | invalid | markdown bold |

Indexing turned the third into an honest `invalid` rather than a false `fail`, which is
exactly what it promised and is why the subject's 57 of 57 was visible at all. The fix is
in the reader, not the prompt: the subject has now broken formatting three different ways
in three runs, the planner's prompt already asked for "the number of the single best
option", and the verifier's model is changing, so a prompt tuned to one model's habits
would not transfer.

`reply_number()` in `local_candidates.py` takes the first non-empty line, strips whitespace
and markdown emphasis (`*`, `_`, a backtick) from its ends, and parses what remains. It
**never searches inside the line**: `The answer is 1` stays `invalid`, because extracting a
number from prose is how a wrong reply becomes a false pass. It applies to `choice` and
`numeric` only. A number cannot contain those characters, so stripping them cannot change
its meaning; in `exact` answers they are content — `rgroup_label`, and `[*]` is a dummy
atom in SMARTS — so `exact` is never normalized. A trailing `.` is deliberately not
stripped either, because that would turn `.5` into `5`.

Every `choice` and `numeric` candidate now proves the rule during its own qualification:
three new controls check that a bold reply and a bold reply with an explanation both pass,
and that a sentence containing the right number stays `invalid`. `METHOD_VERSION` moved to
`-4` accordingly, so the seven candidates this run qualified without those controls are not
reused. Five tests were added, including one built from the verbatim observations, and
three mutations were each caught: removing normalization, making it greedy, and applying it
to `exact`. The greedy one matters most, since it is the false-pass path. Replayed through
the new code, the 57 saved observations went from 52 pass and 5 invalid to 57 pass, and no
passing verdict changed. Suite 260 → 265.

**11. The verifier's model pin moved to `claude-opus-5-5`.** Operator's request. The
registration was changed by the documented remove-and-re-add procedure, with the previous
registration backed up first and diffed after: exactly one argument changed, and the token
field stayed a `${SCI_VERIFIER_OAUTH_TOKEN:-}` placeholder throughout. `LOCAL-INSTALL.md`
was updated to match. The same paragraph had claimed that pinning makes "that whole class of
lost run" disappear, which has been false since 2026-09-21, when the fault recurred with the
pin in place; it now says so, and that switching models starts a new series.

`LOCAL-INSTALL.md` also stated that only one live run had ever completed and that grades
B, C, D and U had "still never run live" — false four runs ago. Under the one-owner rule it
now points at "Current state" here instead of restating status. That section had itself
drifted, saying "Three runs" above a table of four; the prose count is gone, so the table is
the only thing that states it.

### Decisions taken 2026-09-22

**1. Index the choices rather than loosen the comparison.** Operator's proposal. Turning
the answer into a number removes the surface-form question instead of managing it.

**2. Keep open answers where the surface form is already forced.** Numbers especially. The
pIC50 case that made the subject compute `-log10(1e-9)` and answer `9` was the strongest
evidence in the run: generation, not recognition. Turning arithmetic into a menu would
downgrade it, so the `choice` method is the default for everything else and not universal.

**3. A reserved always-incorrect option.** Operator's proposal, adopted with the framing
shifted from trap to diagnostic.

**4. `local-contract.md` is authoritative, and the co-edit rule is now general.** The
2026-09-22 review found CLAUDE.md contradicting itself: it listed six authoritative
documents without `local-contract.md`, while stating elsewhere that the local profile's
enforceable behavior is documented there. `agent.py:269` settles it — the local profile
pins that file, in full, as a planner instruction, which is more direct than the
section-only pinning some listed documents get. It is now item 5 on the list, and
`SKILL.md` names it and `local-evaluator-spec.md` in its reference guide.

The narrow co-edit rule was the second half of the bug. It protected exactly one pair by
name, so adding the `choice` method left `local-contract.md` wrong twice and
`LOCAL-INSTALL.md` wrong once for a day while the named pair stayed perfectly in sync.
CLAUDE.md now states the general form: a fact stated in more than one place has one
owner, every other mention links the owner rather than restating it, and the owner moves
in the same commit. `tool-contracts.md` owns the installed comparison methods,
`workflow.md` owns tool legality, `evidence-rubric.md` owns the grade standards. The
duplicate method lists in `local-contract.md` and `LOCAL-INSTALL.md` were replaced with
pointers, so the four copies of that list are now one.

**5. Fix reply formatting in the reader, never the prompt.** Three runs, three different
formatting habits, and a prompt that already asked for a bare number. The reader strips
presentation and never searches content; that line — strip wrapping, never search inside —
is what keeps a lenient reader from producing false passes, and it is tested by mutation.

**6. The verifier moves to Opus 5.5.** Operator's decision. Runs before `7efbdd8c` and
after it are separate series.

### Designed, flagged do-not-implement: a case-level contract

**Nothing below is implemented, approved for implementation, or tested.** The operator
considered it and declined it as unnecessary complexity for the project's current size.
It is recorded because the design is finished and the trigger for revisiting it is
specific.

**The question it answers.** There is no general contract saying which kinds of test may
support which grade. `evidence_ceiling()` computes from reference and test-bundle facts
only — origin, scorer authorship, determinism, token-exactness, case count, trial count —
and is blind to what a case asks. Exactly one type rule exists, added 2026-09-21: a
behavioural claim whose cases only recite naming or spelling does not support grade A.
That rule works; it demoted two claims from ceiling A to a settled B in run `fb64115f`.

**The design.** Do not enumerate test types, which is a taxonomy that rots. Classify what
the subject must *do* to answer, which is close to exhaustive in three levels: **generate**
(produce a value present in nothing it was given — compute, execute, derive),
**discriminate** (choose among plausible alternatives it is shown), and **recall**
(reproduce a string from the material). The ceiling then follows from whether the case
level meets what the claim demands:

| Claim asserts | Recall case | Discriminate case | Generate case |
| --- | --- | --- | --- |
| a name or API surface | matches, A | A | A |
| a behaviour or meaning | below, max B | matches, A | A |
| a computed value | below, max B | below, max B | matches, A |

Row two column one is the existing 2026-09-21 rule; the table only generalizes it. Row
three column two is the case not yet met: a computation claim tested by multiple choice
turns arithmetic into recognition and should not reach A either.

**How it would bind.** The same division of labour as everywhere else. The planner
declares the claim kind and each case's level as small enums; Python computes the ceiling
from the table, which is arithmetic once declared and sits beside
`insufficient_distinct_cases`; the critique audits the declaration rather than judging
taste, because "this case is declared generate but its answer is printed in the prompt" is
concrete and checkable. That is the unlock: Python cannot classify a case but can enforce a
ceiling on a declared classification, which makes the demotion mechanical instead of
depending on drawing a diligent critique session.

**Why it was declined.** Cost is a schema change, `evidence_ceiling()` arithmetic, two
contract files, report-card rendering and tests, against one known problem that a single
sentence already solves. It also carries the coverage risk below: claim extraction fell
from six to four after one restriction was added, and this would be the second.

**Trigger to revisit.** Ad-hoc type restrictions accumulating in the rubric. One is a
sentence; four or five are a taxonomy pretending not to be, and at that point the table
above is cheaper and more consistent than the prose it replaces. A single new restriction
is not a trigger.

### Open questions for the operator

**1. Should the aggregation rule become a plan field?** Carried forward unchanged.

**2. Claim coverage fell from six to four.** The two that disappeared,
`DrawMoleculeACS1996` and `GenerateDepictionMatching2DStructure`, are the most
API-surface-flavoured of the six — exactly the kind the new rubric sentence says remains
legitimate. Claim extraction happens before qualification and varies between runs, so this
cannot yet be attributed to the rubric edit. It is the narrowing regression the previous
entry flagged, and it now has **two consecutive observations** behind it: `fb64115f` and
`7efbdd8c` extracted the same four claims and dropped the same two. The next run changes
model, so it cannot settle this either — if Opus 5.5 extracts six, the model and the rubric
are confounded. Settling it needs either a run on the new model with the rubric sentence
temporarily reverted, or a decision that four is acceptable.

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

**Restart Claude Desktop before the next run.** The MCP server reads its arguments at
startup, so until it restarts it is still serving `claude-opus-5`, and a run started now
would silently use the old model while the install guide says otherwise.

Everything else is committed, pushed and green.

### Suggested next move

Run `sar-analysis` on Opus 5.5 and find out whether the reply reader closes the last of the
harness noise on a live subject. The reply reader is already established by unit tests and
by replaying every saved observation; a live run cannot establish it further, because Opus
5.5 may simply not use bold. What a live run can show is whether any *new* surface form
appears.

### Recommended next action

After restarting Claude Desktop, run `sar-analysis` once and check two things in the saved
card. First, did every trial come back `pass` or `fail`, with no `invalid`? If any reply is
still `invalid`, read its verbatim text: a new presentation form is a reader gap, whereas a
number inside prose is the reader working as designed. Second, record the claim count
without drawing a conclusion from it, since the model change confounds it. It is finished
when both are recorded. A run with no `invalid` and no false `fail` would be the first
result this project has produced with no harness noise at all.
