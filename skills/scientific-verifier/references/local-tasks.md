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
one told it the order of averaging the skill prescribes.

**Each task names the claim's sections it uses**, in `sections`. Python refuses a design
whose tasks leave one of the claim's sections unused by every task. A design holds one to
six tasks, and each runs for the run's trial count.

**Outputs.** Each task has one to twelve output fields:
- `number`: a JSON number, passing within its tolerance (below);
- `text`: a JSON string, passing when equal ignoring case and spacing, so the job lists
  the allowed values, such as `A` or `B`;
- `boolean`: `true` or `false`;
- `set`: a JSON array of strings, passing when it holds the same items in any order,
  ignoring case and spacing.

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
container of the operator's image with no network, the task's files at `/task`, and on
standard input the same task input the test AI receives, for at most five minutes; it
writes `/work/results.json`.
Every output must pass on the solver's results, or the design is rejected, naming each
failure. This is how Python checks that a task is fair before it is used: the planted
values are in the files, the tolerances leave room for an honest analysis, and the
outputs can be filled as asked. A solver that copies planted values instead of analysing
the files proves nothing, and the critique sees its code.

Generator and solver run in the operator's image, never the skill's environment, so no
package the skill chose touches an expected value. A run reports what that image lacked
when the program failed.

## Reading a trial's results

Python reads `/work/results.json` from the trial's new files. The trial is:
- `pass` when every output passes;
- `fail` when some field holds a value of the right type that misses its expected value;
- `invalid` when there is no such file, it is not one JSON object, or, with no value
  wrong, a field is missing or a value has the wrong type.

The format is fixed, so no AI reader reads a task. Each trial's record keeps every
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

**Run problems.** Python also reads each trial's tool output for a module or command the
skill needed and the container lacked (`ModuleNotFoundError`, `command not found`) and
records it on the trial. The report lists them per claim. A skill that cannot run as
shipped is a finding about the skill, and says nothing about whether its advice is right.

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
text file), planted values, outputs with their tolerances and quotes, and the solver's
results. Its rubric asks whether each expected value is right and independent of the
skill, whether the tasks exercise the claim as a whole, whether the comparison is fair
and exposes any departure of the skill from the reference solution, whether a stronger grade
was passed over, and whether earlier concerns are answered. Each
task gets one verdict: `counts`, `beyond_scope`, `leaked`, `duplicate` or `unsound`,
defined in "Cases each grade requires" of `evidence-rubric.md`.
