# Local profile: claims and task tests

This document owns how the local profile splits a skill into claims and tests each claim
by running the skill. Tasks run in the operator's container (`sandbox_image`); without
one nothing can run, and a claim ends on the documentary path or a recorded limitation.
`local-contract.md` owns the rest of the profile: the reference requirements of each
grade, the subject boundary, status and the documentary path. "Cases each grade
requires" in `evidence-rubric.md` owns how many tasks each grade needs.

The aim is to test whether the whole skill works, not to debug it: give the test AI an
input, let it follow the skill, and check what comes out. Before task tests, retired with
the question tests on 2026-10-05, a claim was one behaviour from one section, tested by
questions about facts the skill states. Claims
covered 13% of the Western-blot skill's words, 31% of scikit-survival's and 73% of
dose-response's, and in run `90c60cbe` 10 of 78 tries used the container at all, none of
them to run the skill's own fitting script.

## Claims

**Sections.** A section is the text under one heading of `SKILL.md`, down to the next
heading of any level. Text before the first heading is a section too; YAML frontmatter
and a heading with nothing under it before the next heading are not. `load_submitted_skill`
returns them numbered `S1`, `S2`, ... with each heading, level, first line and word count.

**A claim is a group of whole sections** that serve one purpose of the skill: a workflow
from input to result, a family of checks or warnings, one kind of analysis. Its
`statement` and `expected_behavior` say, in a sentence or two each, what a user of those
sections gets. Its `source_quote` is quoted exactly from one of them, as before. Name the
claim's sections in `sections`. Sections that only work together belong in one claim.

**Nothing is left out.** Every section is in exactly one claim or in the manifest's
`set_aside` list, each with a `reason`: a section with nothing to test, such as metadata,
a list of references or related skills, or installation notes. Python refuses a manifest
that leaves a section out, names one twice or names one that does not exist. The report
and the run's page list the sections set aside with their reasons.

**How many.** The planner chooses, and a longer skill gets more claims. Python accepts at
most 12, because a run's subject calls and its three hours cover about that many claims of
three tasks. A claim too small for a task of its own joins the claim it serves.

## Tasks

**A task is what a user of the claim's sections would do:** input files, a job in plain
words, and fixed outputs. The test AI receives the whole skill, the job, the paths of the
input files under `/task` (read-only) and the output fields, and writes its results to
`/work/results.json`, a JSON object holding exactly those fields. It never sees the claim,
the design, an expected value or another task. Write the job as a user would ask: name
the inputs, say what to find and what each output field means, with its unit and, for a
text field, its allowed values. Do not tell the test AI which steps of the skill to
follow, which result to expect, or which problem was planted, nor give it a rule,
threshold or order of steps the claim's sections supply: the task would then test applying
a given rule, and the critique does not count it (`leaked`). Where a field needs a rule the
sections do not give, such as how far a signal may stray from proportional, the job may
state one; the critique names it in that task's `criterion_given`, and the report shows it.
Run `2bef9e0d`'s tasks on spotting problems gave the test AI every deciding threshold, and
one told it the order of averaging the skill prescribes. Ask for each output in the user's
terms and let the claim's sections decide how to compute it: a job that says how, by a
formula or a definition such as "the phosphorylated fraction of the total", lets the test AI
answer without the skill (`leaked`). Naming what to report, such as a fold change or a
standard error, is not saying how. Run `cfe9e57a`'s two-step task defined its output so, and
the test AI computed the fraction, 1.4, where the skill's own formula gives 2.45.

**The test AI follows the skill as written.** Its instructions say the session tests the
skill and no one acts on its results file. It does exactly what the skill says, in the
skill's order, even where it believes a step is wrong, and uses its own judgment only where
the skill says nothing. It never changes the results file to correct the skill. Instead it
ends its final message with a line `Disagreement with the skill:` naming each step it
believes wrong, what it would do instead and why, or `none` ("Disagreements" below). Before
this, a test AI that judged a step wrong replaced it, and the skill passed: in runs
`cfe9e57a` and `5f7062fa` every trial of four tasks did so, and three claims passed, one at
A, on steps the trials had set aside. Replayed with this instruction on 2026-10-14, all 12 of
those trials followed the skill and failed, and every one named the wrong step. Nine trials
of tasks the skills get right still passed.

**Each task names the claim's sections it uses**, in `sections`. Python refuses a design
whose tasks leave one of the claim's sections unused by every task. A design holds one to
six tasks, and each runs for the run's trial count.

**Outputs.** Each task has one to twelve output fields:
- `number`: a JSON number, passing within its tolerance (below);
- `text`: a JSON string, passing when equal ignoring case and spacing, so the job lists
  the allowed values, such as `A` or `B`;
- `boolean`: `true` or `false`;
- `set`: a JSON array of strings, passing when it holds the same items in any order,
  ignoring case and spacing;
- `judged`: a JSON string in the test AI's own words, checked by judges against written
  criteria ("Judged outputs" below).

A number's tolerance is `relative_tolerance` (a fraction of the expected value from 0 to 1,
such as `0.35`) or `absolute_tolerance`, both decimal strings; with both, the wider passes, and
with neither the installed tolerance of 0.000001 applies. A tolerance comes from what the
data allow: the reference solution must pass with it, and a plausible mistake (a unit off
by 1,000, an inverted ratio, a log taken twice) must fail.

**Where the skill departs from the reference.** When the skill's procedure, followed
literally, gives a different result from the reference solution in a situation the claim
covers, at least one task must put that situation in its input, with the difference outside
the tolerance. A design whose inputs stay where the two agree, or whose tolerance admits
both, hides the departure; missing the key there is the skill's failure, not unfairness to
it. The critique lists a departure no task exposes, and the claim cannot settle at the
proposed grade until a task does (`select_local_candidate` in `tool-contracts.md`). Run
`2bef9e0d` loaded every lane equally in the tasks built on the skill's two-step
normalization, which as written does not cancel unequal loading, and the skill's answers
passed 2.4 to 5.5% off the key.

**Advice is tested by doing.** Where the skill tells its user to catch a problem (a
curve that never levels off, a saturated band, too few events), plant that problem in a
task's input and ask whether it is present, and put a clean case beside it in the same
input that must not be flagged: one `boolean` field for each. A task with no input files
suits only guidance with nothing to compute, and states its scenario in the job.

**Judged outputs.** Where the claim's sections lead to an answer no fixed key captures, such
as a plan, advice with several right answers or an interpretation, an output may be
`judged`. It holds `criteria`, one to six yes/no questions about the answer, each quoting
the outside source it rests on in `reference_ref` and `source_quote`, and `fail_example`, a
plausible wrong answer; no `planted`, `value` or tolerance. A rule only the skill states is
never a criterion: it is an unsourced rule (below). A task has at most one judged output and
keeps fixed outputs where it can. Two fresh judge sessions each read the job, the answer
and the criteria with their quotes, never the skill, the claim or the planning, and answer
every question yes or no with the fact it rests on. Python decides: a criterion is met when
both answer yes, unmet when both answer no, and undecided when they split; the output
passes when every criterion is met, fails when one is unmet, and is otherwise undecided.
At qualification the judges must pass the reference solution's answer and fail
`fail_example`, or the design is rejected, naming the criterion. Their answers are kept in
the design's receipts, so a saved design is rechecked without new sessions. A judge session
that fails is an operational fault, as a subject's is. AI judgment decides these verdicts,
so a design with a judged output settles at grade D at most ("Cases each grade requires" in
`evidence-rubric.md`). Run `b573cd15` keyed troubleshooting advice to one answer per task
by ruling the others out in each record; a judged output tests such advice as it is given.

## Where expected values come from

Every output's expected value comes from outside the skill.

**Planted values.** The design's `generator` holds `code`, a Python program, and the model
it implements, quoted exactly from a fetched reference in `reference_ref` and
`model_quote`, never taken from the skill. For each task with `arguments`, Python runs the
program once, in a new container of the operator's image with no network and no task
files, with the arguments on standard input and `/work/out` as its directory, for at most
two minutes. It writes the task's input files there, at most twenty, by plain names
without folders, and prints one JSON object of planted values by name, on its own or as
its last line: numbers, strings, booleans and lists of strings. An output names its value in `planted`. A planted number rests on the model
quote. A planted text, boolean or set, such as which compound is more potent or whether
a curve is incomplete, is a judgment about what was planted, so it also carries a
`reference_ref` and `source_quote` quoting the rule it follows. Python stores the files
and values, and every trial of the task receives the same bytes.

**Quoted values.** An output may instead give a literal `value` with `reference_ref` and
`source_quote`, the value appearing in the quote: a number as a complete token, a text as
its words, a set as items separated by commas, each in the quote. A boolean is never
quoted. **Reference files** give a task a fetched dataset as input: each of
`reference_files` names a file and the `reference_ref` of a fetched reference or asset
whose exact bytes it receives, for a published dataset whose quoted results are the
expected values.

Every quote must occur exactly in the pinned reference text Python retrieved: all of it,
even past the 40 KiB a reply carries (`fetch_local_reference` in `tool-contracts.md`).

## The reference solution

The design's `solver` holds `code`: the planner's own correct analysis, written from the
referenced model, not from the skill's code. For each task Python runs it in a new
container of the image the task's trials use, with no network, the task's files at `/task`, and on
standard input the same task input the test AI receives, for at most five minutes; it
writes `/work/results.json`, and Python keeps no other file it writes.
Every output must pass on the solver's results, or the design is rejected, naming each
failure. This is how Python checks that a task is fair before it is used: the planted
values are in the files, the tolerances leave room for an honest analysis, and the
outputs can be filled as asked. A solver that copies planted values instead of analysing
the files proves nothing, and the critique sees its code.

The generator runs in the operator's image, never the skill's environment, so no package
the skill chose touches a planted value. The solver runs where the trials run: in the
skill's environment when setup built one ("Skill environment" in `local-contract.md`),
otherwise in the operator's image. A task is then proven fair with the packages the test
AI has. When a job asks what a library the skill uses does, the solver calls that library
rather than imitating it. In run `55d345a3`, before this, the solver imitated NeuroKit2's
response detector in an image without NeuroKit2 and kept the four responses the generator
planted; the library keeps five, and every trial of that task failed on a key the library
never gives. The solver never sets an expected value, so a package can at most let an
unfair task qualify, and the critique reads the solver. A run reports what an image lacked
when a program failed. Catalog requalification still runs both programs in the
operator's image, so a design whose solver needs the skill's packages does not yet
requalify on another machine.

## Reading a trial's results

Python reads `/work/results.json` from the trial's new files. The trial is:
- `pass` when every output passes;
- `fail` when some field holds a value of the right type that misses its expected value;
- `invalid` when there is no such file, it is not one JSON object, or, with no value
  wrong, a field is missing, a value has the wrong type or a judged output is undecided.

The format is fixed, so no AI reads a fixed output; judges read only a judged one. Each trial's record keeps every
output's expected value, the value found and its verdict. Status follows the rule of
`local-contract.md` over every trial of every counting task, so one wrong result fails
the claim, and the report shows which task and which field.

**Passed on tolerance.** Python also compares each number that passed with the reference
solution's result for the same task. When that result is not zero and they differ by more
than 0.5% of it, the output's record keeps `reference_result` and `off_reference`, the
difference as a fraction of that result, and the report marks the task as passing on
tolerance only. Status and grade stay: the mark tells
the reader the skill computed something other than the reference, inside a tolerance meant
for honest variation. In run `f84c131c` every answer was within 0.18% of its reference
result; in `2bef9e0d` the four tasks that hid a departure were 2.4 to 5.5% off, and every
other task within 0.01%.

**Near misses.** Python also marks each number that failed by at most half its allowed
difference beyond it, so within one and a half times the tolerance of the expected value: its
record keeps `near_miss`, and the report marks the task as failing on a near miss. Status and
grade stay. The mark asks the reader whether the tolerance left room for honest measurement
before reading the fail as the skill's. In run `0d15e36c`, two of three tries measured a band
ratio from a noisy blot image at 0.53 where 0.54 to 0.66 passed, and the third got 0.58; all
three followed the same steps. Across six runs, 49 of 51 numbers measured from images were
within 3.3% of their key.

**Disagreements.** Python keeps what follows the last `Disagreement with the skill:` line
of the trial's final message, at most 2,000 characters, as the trial's `disagreement`. A
message without that line, or one whose line says `none`, has none. The report lists each
disagreement under its claim, by task and trial. A disagreement changes no status or grade:
it is the test AI's view, and the verdict comes from the results file. In the replay, each
test AI that failed by following a wrong step gave the right answer there.

**Run problems.** Python also reads each trial's tool output for a module or command the
skill needed and the container lacked (`ModuleNotFoundError`, `command not found`) and
records it on the trial. The report lists them per claim. A skill that cannot run as
shipped is a finding about the skill, and says nothing about whether its advice is right.

**Files not kept.** Python keeps a trial's new files as evidence, `results.json` first,
within `max_file_bytes` for one file and `max_artifacts` and `max_artifact_bytes` for all.
Any other file past a limit stays in the container, and the trial records its path and
size under `files_not_kept`. A results file past a limit is still the operational fault
`sandbox_artifacts_invalid`. Before this, one such file voided the claim: in run
`55d345a3` the skill's own script wrote its processed signal table, over 4 MiB, beside a
results file of four numbers, and the claim ended after its first trial.

## Selecting and critiquing a task design

`select_local_candidate` takes a task design as it takes any other: the planner proposes
the ceiling Python computes, and a fresh critique session judges it. Its `coverage`
justification says which tasks use each of the claim's sections and what their outputs
check. The critique's objections, required revisions, coverage gaps, departures and the
tasks it does not count carry forward to the next round, without grades. A coverage gap is
something the claim's sections say to do, check or conclude that no task tests; a critique
that agrees with the proposal but lists any sends the claim back once, as the coverage
return under `select_local_candidate` in `tool-contracts.md` says.

The critique sees the claim with the text of its sections, the design's generator and
solver code, each task's job, sections, arguments, files (names, sizes, the start of each
text file), planted values, outputs with their tolerances and quotes, each judged output's
criteria, `fail_example` and the judges' verdicts at qualification, and the solver's
results. Its rubric asks whether each expected value is right and independent of the
skill, whether the tasks exercise the claim as a whole, whether the comparison is fair
and exposes any departure of the skill from the reference solution, whether a stronger grade
was passed over, and whether earlier concerns are answered. For each task it answers fixed
questions, each tied to a row of the verdict table in "Cases each grade requires" of
`evidence-rubric.md`, and Python gives the task the verdict of the first question answered
yes, or `counts`.

**Unsourced rules.** The critique also lists in `unsourced_rules` each rule, threshold,
formula or named method the claim's sections state that no fetched reference states and no
search in Python's record found a source for, quoted exactly from the sections, with what
was sought, and in `searched` whether a search or fetch in Python's record sought a source
for it. A rule a task tests against a quoted source is not one. The claim reports a rule
sought and not found as grade U, and one never sought as not looked up, with no grade, beside
its grade ("Rules no source states" in `evidence-rubric.md`). So a rule the planner expects
to be the skill's own earns U only after a search for it. Runs
`f84c131c`, `b573cd15` and `3f073fec` graded claims A and B on their sourced parts while a
skill's own r² and QC cut-offs went untested, shown only among the coverage gaps.
