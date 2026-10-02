# Local profile: implementation 0.7.0

## Computational execution and operator settings

The public action accepts an operator-selected `--config` JSON file. Settings
are validated and pinned into the subject identity. The planner cannot change
them. A pinned, already installed Linux Docker image enables computational
skills; absent configuration produces an operational limitation for those
skills. Before a run starts, the packages a skill declares can be added to a copy
of that image for its subject trials, as "Skill environment" below describes. The
verifier never installs anything during a trial.

Each computational trial has a new local container, with no network, no host
credentials, no evaluator or expected-answer mount, an unprivileged user, a
read-only root, bounded writable temporary directories, and memory/process/time
limits. Only the immutable submitted files are mounted read-only. A private
subject MCP server exposes commands inside this container. The native Claude
CLI remains on the host and has no host shell or host Read tool in this mode.
It must invoke the pinned submitted Skill before producing its answer.
Scripts, binary input and generated regular files are supported. Submitted
hooks, settings and dynamic skill shell directives are never enabled. Generated
files are size/path/credential checked and saved as content-addressed evidence.
Container cleanup occurs on success, failure and interruption, with a bounded
container lifetime as a backstop. This is not a claim of VM-level isolation.

Private subject tools are not public workflow tools and cannot select runs,
containers, host programs, images or host paths. The frozen case input contains
no expected answer. External capabilities require explicit operator settings;
the model cannot broaden that capability set.

Resource imports use operator-selected names and exact file digests. Public
reference downloads reject private addresses and redirects. Binary resources
retain exact bytes. JSON/CSV/TSV and ZIP inspection is bounded; archives are never
expanded on the host. Units, version and license are mandatory provenance fields,
not claims that Python has independently verified scientific meaning or rights.

Read-only external app adapters are explicitly registered native programs with
fixed arguments, executable digests, bounded JSON stdio and selected environment
credential names. They are a trusted host integration boundary, separate from
container isolation. The verifier does not claim it can confine an arbitrary app
or prove a declared read-only adapter is read-only. No planner-selected executable,
shell argument substitution or automatic app write/publish operation is exposed.
App-specific credentials never enter a container or saved configuration.

Generated Python evaluators receive only one scoring packet per process and run
in separate containers from subjects. Cases need fetched/imported provenance.
Positive, negative, boundary, invalid and held-out controls are mandatory. Control
passing is mechanical qualification, not evidence of independent scientific
validity. Subject trials are scored individually before all-trials aggregation.
Operationally missing trials stay operational; invalid scientific observations
remain in coverage denominators.

## Skill environment

When `sandbox_image` is set, setup prepares the image the skill's subject trials run
in. It runs after the model probe and before the run or its planner exists, and it is
the only step of a verification that downloads packages; "Packages a skill declares"
in `resource-policy.md` owns that trust decision.

**Declarations.** Setup snapshots the skill exactly as `load_submitted_skill` will and
reads nothing else. A declaration is an install command inside a fenced code block of
a Markdown file (`pip`, `pip3`, `python -m pip`, `python3 -m pip`, `uv pip`, `%pip` or
`!pip`, then `install`), a line of a `requirements*.txt` file, or an entry of
`[project].dependencies` in `pyproject.toml`. Inline code in prose is not a
declaration. A requirement is a package name with optional extras and version
specifiers. URLs, paths, VCS references, environment markers and the installers
themselves (`pip`, `setuptools`, `wheel`, `uv`) are rejected, and so is a command that
sets any option other than a harmless one such as `--upgrade` or `--quiet`, so a skill
cannot choose the index. A `-r` naming a requirements file inside the snapshot is
skipped, because that file is read on its own. A `--hash` value is dropped, because the
verifier hashes what it downloads. At most 100 requirements are accepted. A module the
skill imports but never declares is not installed. No model and no tool argument can
add to the list.

**Status.** `not_needed` when nothing is declared; `all_rejected` when every
declaration was rejected; `disabled` when requirements exist but `package_index` is
null; `source_unavailable` when setup cannot snapshot the skill, in which case
`load_submitted_skill` records the fault as it would anyway; otherwise `built`. Only
`built` gives subject trials a different image; otherwise they run in `sandbox_image`.

**Build.** Every build starts from `environment_base_image`, a plain Python image the
operator pins, never from `sandbox_image`, so one skill's packages never land on
another's tools. `package_index` requires it. The build proceeds in four steps:
1. One container of that base resolves the requirements. It is the only container of a
   verification with a network. It downloads wheels only, from the configured index into
   a Docker volume, under its own deadline.
2. Python checks each wheel's file name, and the number and total size of the wheels
   against `max_packages` and `max_package_bytes`, then writes a hash lock.
3. A second container, with no network, installs exactly that lock from the volume with
   `--require-hashes` and runs `pip check`. It runs under the base's own entrypoint,
   which must be empty.
4. The result is committed as a new image tagged for this build alone. It is labelled
   with the build's key, covering the base, index, requirements and build scripts, and
   with the build record.

Every container, and the volume, is removed on success, failure, cancellation and timeout.
Any failure stops the verification as `skill_environment_unavailable`, naming the cause,
before any planner cost, like the model probe under "Subject boundary". Setting
`package_index` to null runs on `sandbox_image` instead.

**Removal.** A built image lives for one verification. It is removed when the
verification ends, however it ends, so every verification starts from the plain base
again and nothing accumulates. Setup also removes environment images more than a day old
that a killed verification left behind.

**Subject trials only.** The built image serves the skill's subject trials and nothing
else. Calculations, generated evaluators, scoring and catalog requalification keep the
operator's `sandbox_image`, so no package the skill chose runs inside code that produces
an expected answer or scores a trial. The built image is part of the subject identity, so
the identity checks catch any change, and `environment_digest` includes the environment
record.

**What the planner sees.** The planner's pinned instructions gain one block. The
verifier renders it only from values it checked itself: the image digests, the status,
package names and versions from the lock, counts, reason codes and the index host. The
block also says that nothing can be installed during the run. The full record is the
`environment` section of `get_verifier_context`. It includes where each declaration was
found, the text of rejected commands, and the packages and imports the built image
reports. That last part is untrusted, because an installed package could alter it. The
planner's `load_submitted_skill` must produce the snapshot digest the environment was
built from; a skill that changed in between ends the run as `source_changed`.

## Negotiated evidence grade, plan audit and deterministic grade policy

Selection freezes source, subject/configuration, candidate, trial count, tolerances
and the installed evidence-strength policy (`scripts/local_policy.py` prints it) and writes a deterministic audit before
execution. The grade is settled during that selection and requires no human review.

The planner proposes `target_grade` A, B or C with an explicit justification.
Python computes an **evidence ceiling** from facts it recorded itself. Only that
ceiling, or a grade the last critique of the same design supported, may be proposed;
both overclaiming and aiming low are refused before any session is spent:

- **A** needs every expected answer quoted token-exactly from reference bytes Python
  itself retrieved over public HTTPS, or calculated by Python from a formula so quoted
  after reproducing worked examples so quoted, as `qualify_local_candidate` in
  `tool-contracts.md` specifies; scored by an installed comparison method, with at
  least three trials of this model subject.
- **B** allows an operator-imported pinned dataset, or a generated Python evaluator
  whose controls all pass, with the same trial minimum. A planner-authored scorer
  cannot reach A, because direct validation excludes AI judgment in scoring. A
  calculated answer is not a scorer: the planner writes the program that produces a
  key, the quoted worked examples check it mechanically, scoring stays installed, and
  the report says the planner wrote it. Nor is the AI reader of "Reading replies": it
  reports which answer a reply gives, against a key and a rule fixed before any trial.
- **C** covers any reproducible comparison, including a single trial, a substring
  rather than token-exact quote, and a candidate reused offline whose reference origin
  was never recorded.
- Failed controls support no execution grade.

Those are the reference and trial requirements. Each grade also needs a number and
kind of counting cases, owned by "Cases each grade requires" in `evidence-rubric.md`.
The ceiling is the weaker of the two. The local planner receives that section and
"Negotiating the grade" pinned with its other instructions, since its session cannot
read files.

First, Python measures what `beyond_scope` describes, a rule *No more* in
`evidence-rubric.md` owns and `select_local_candidate` in `tool-contracts.md` specifies.
Fresh no-tool sessions that see only the claim answer each case twice, and a case any
answer misses does not count. The critique judging that design never sees those
answers. A session that cannot complete, or that another model answered after a
refusal, leaves its case unmeasured, not rejected, so a provider fault cannot lower a
grade.

A fresh no-tool session then receives the claim, the evidence design, the reference
provenance, the justification and the design's scope and limitations whole, Python's
ceiling, Python's search record, the concerns earlier reviewers raised
about earlier versions of this design (their objections, required revisions and coverage
gaps, and every case they did not count, with its verdict, reason and suggested
replacement), each of which it judges answered or not, and the fixed critique rubric.
The search record is read from this attempt's workflow log, not from the planner's notes:
every WebSearch query the planner ran, marked with the claim it was working on (the one its
last verifier tool call named), and every reference, resource or asset fetch with the claim
it was for and its outcome. Run `26312681`'s critiques read the planner's description of
its searches clipped at 2,000 characters and its limitations at 800, and took it as true
for two claims whose untested facts no search had sought. It never sees the
planning conversation, any subject answer, or any earlier reviewer's grade: objections
carry forward so a revision can be checked, grades do not, because a reviewer shown a
previous verdict would anchor on it. That separation is imperfect and is not claimed to
be complete: an objection such as "three cases cannot support direct validation" implies
a grade it does not state. Withholding the letter reduces anchoring; it does not remove
the signal. The planner's notes are held to the same rule, which step 3 of "Negotiating
the grade" in `evidence-rubric.md` owns: run b0955d2f's planner told one reviewer "The
previous round settled at C", and a proposal whose notes mention an earlier review is
now refused before its critique starts. It sees every case, each with its ID and answer form, and returns the
strongest grade the evidence actually supports plus one verdict per case. The settled
ceiling is the weakest of the proposal, Python's ceiling recomputed over the cases the
critique counted and the claim-only answers did not miss, and that critique's grade.

When the settled grade is below the proposal, the planner revises before it accepts, as
step 4 of "Negotiating the grade" in `evidence-rubric.md` says: a stronger design and its
new ceiling earn another round, and accepting the grade that design settled at settles
immediately without another session. A critique that agrees with a proposal below A but
names coverage gaps, or finds an earlier concern unanswered, returns the claim, and its
grade is accepted only after a new search (the returns under `select_local_candidate` in
`tool-contracts.md`).
Repeating a proposal on
a design already critiqued is refused and consumes neither a session nor a round, so
the budget of one round per rubric grade bounds real revisions rather than repetition.
Rounds with rejected cases, whether the critique or the claim-only answers rejected
them, are also counted against the two replacement rounds in `evidence-rubric.md`; once
those are spent, a round that still rejects cases settles the plan. Accepting a design that settled at no grade leaves the plan
ungraded: it still executes and produces comparison evidence, and the claim continues
to the documentary path. An unavailable critique is an operational limitation.

The critique's reply has a fixed shape that Claude Code enforces, as the reply-shape
paragraph under `select_local_candidate` in `tool-contracts.md` describes: a reply outside
it goes back to the same session to be corrected, and a reply that judges the design is
never re-rolled, whatever grade it gives. The critique session has ten minutes; the documentary assessor keeps two; each
claim-only session has two, four running at once. Judging every case, listing the claim's
facts and giving each earlier concern a verdict took live critiques 90 to 210 seconds on
2026-09-30 and 2026-10-01, and two replays judging eleven concerns ran past the five minutes
critiques then had; the two-minute deadline they once shared with the assessor killed one
in run 74eadedd.

The installed policy then requires every planned trial and case to be scored. Missing
observations are operational. Invalid observations remain counted. Only counting cases
enter accuracy, consistency and status; the others still run and are reported with
their verdicts. The achieved grade is the settled ceiling, fixed before any trial ran,
and nothing observed afterwards moves it: invalid observations and disagreement
between a case's trials can change the status, never the grade, and each is recorded
among the execution limits. `evidence-rubric.md` owns that rule; a skill failing every
trial against an A-grade reference keeps grade A. The verdict is pass only
if all scored trials pass, fail if at least one fails and none is invalid, and
inconclusive if any is invalid, each trial's status being the one "Reading replies"
settles. No eligible grade grants no scientific verdict and
requests a separate documentary assessment; it never silently invents a weaker grade.
Synthetic fixture observations never receive a grade.

Observed model identities must remain constant across trials of a claim. Changing
code, source, image, configuration, plan or candidate invalidates the bound audit.
A grade states how strong the evidence is. It is not an endorsement, and neither
mechanical qualification nor catalog membership adds to it.

## Independent documentary path

After an execution with no eligible A/B/C grade, the live local workflow enters
`local_documentary`. The planner either supplies bounded cited evidence for a
fresh assessor or records searches establishing no acceptable evidence. A new
Claude session, selected by the host, receives the exact claim, source quotes,
limitations and fixed rubric only. It has no tools or planning history. Its reply
must contain a status, supported rubric findings and exact citations to the pinned
packet.

Its shape is enforced the same way as the critique's, so a reply outside it is corrected
in the same session. A reply whose citations do not quote the pinned packet is never
retried: that is a judgement the assessor made about the evidence, and re-rolling it
until the answer is acceptable is grade shopping. The first assessment in shape is the
one that counts, whatever status it carries. A session that ends without one, or a
missing assessment, is an operational failure.

A completed assessment against the installed rubric is grade D with the assessor's
status. Grade D is documentary consistency only; execution accuracy remains
unverified, and AI judgment is primary and disclosed. U/inconclusive is a separate
no-evidence path; runtime failures never establish it. Both paths carry the evidence
preconditions stated for `assess_local_documentary` and `record_local_unverified` in
tool-contracts.md.

A claim that a subject-trial fault still stops after the one re-run of "Subject
boundary" receives a **fallback** documentary assessment, so it still gives the reader something to refer to.
`write_report_card` runs it after the planner has finished, so Python assembles the packet
itself. Its evidence is the reference quote each of the claim's planned cases was keyed to,
already proved exact at qualification, at most eight of them. Its limitations are Python's
own account of the stop. No subject answer enters it. Assessor, rubric and grade are those
of any D. The record keeps the runner fault in its `fault` field and reads `not_obtained`
for accuracy, consistency and completeness, because execution was attempted and lost. It
names itself a fallback. It is not attempted, and the reason is recorded, when documentary
assessment is disabled, when the claim never qualified a candidate, or when less time
remains before the attempt deadline than one assessor session plus five minutes for the
report. An assessor failure leaves the fault record as the claim's outcome. Run 84e90683's
ring-option claim is why: both attempts timed out, and the claim reported nothing.

This contract defines version 0.7's implemented local mechanisms and enforceable
boundaries. The repository's DEVELOPMENT-PLAN.md retains the full project goal
and records automated validation separately from pending manual CLI/desktop,
container/app and domain-scientific acceptance.

This profile supersedes the demo as the default product. Claude Code owns the
planner conversation and tool loop. Python exposes bounded internal operations,
validates transitions, snapshots inputs, executes fresh subject processes, and
writes immutable evidence. The public interface is `verify_skill(source_path)`
or `sci-ai-verifier verify <path>`. Historical profiles remain readable.

## Scope and evidence

The local implementation supports text and computational skills, pinned resources, the
installed comparison methods and qualified generated Python evaluators. Those methods
and the answer form each one requires are enumerated in `tool-contracts.md` under
`qualify_local_candidate`, which owns that list; do not restate it here.
The planner extracts source-grounded claims, as "Claims" below describes, searches for
independent primary references with WebSearch, and proposes known-answer cases in one of
those forms.
Python retrieves public HTTPS reference bytes itself; agent-authored quotes or
search summaries alone cannot qualify a candidate. Reference quotes must occur in
retrieved material, and so must every expected value except one Python calculated from
a quoted formula, as `qualify_local_candidate` specifies. At least three distinct cases, positive
and negative controls, numeric boundary controls, exact resource hashes, source
URLs, versions, license notes and scope limitations are required.

`qualified_local` establishes reproducible mechanics and quote provenance only.
It does not establish that a source is scientifically authoritative, that an input
is semantically matched to its reference, or that coverage is representative.
Those are what the independent critique judges when the grade is settled; a
qualified candidate that was never graded carries no scientific status. Reports
separate comparison outcomes from scientific status and grade.
No local registration changes the reviewed global registry.
An empty catalog initiates discovery without a manual seed. Inadequate evidence,
unavailable execution environments/tools and uncertain scope produce
claim-local limitations. Every accepted claim must be accounted for.

## Claims

The planner extracts the claims; Python checks their quotes, never their meaning. The
earlier profiles ask for atomic claims, which made local claims too small to test. Since
per-case verdicts began, 24 of 41 graded claims settled below the grade their source
supported only because they had too few independent cases, and critiques rejected 17
cases as restatements of another. A local claim is therefore sized to its tests:

- **One behaviour.** A claim is one behaviour the skill tells its user to rely on: a
  procedure step, a documented rule, or one function's behaviour. It states every fact
  the skill gives about that behaviour, so that about six independent questions can test
  it: the five an A needs, plus a spare ("Cases each grade requires" in
  `evidence-rubric.md`). A behaviour too small for that joins the neighbouring behaviour
  it serves. Unrelated behaviours never share a claim, and no claim summarises the whole
  skill.
- **Quoted whole.** A claim's quote carries every fact its statement states, because
  Python checks only that the quote occurs. When Python refuses a quote, correct its
  characters against the file; a shorter quote needs a shorter statement. In `fbd49132` a
  doubled space got one claim's quote refused, the retry cut it from five quoted gotchas to
  two, and the statement kept all five.
- **Section by section.** A section is the text under one heading of `SKILL.md`, down to
  the next heading of any level; a reference file belongs to the first section that
  names it. List the sections that promise a testable behaviour. Take one claim from each
  of them, preferring what the skill tells its user to do and conclude over facts about a
  library it calls, in the skill's order.
- **At most five.** Broader claims need more trials, and a run of six narrower claims
  used all but 8 seconds of its 90 minutes, so a manifest holds at most five claims and
  Python refuses a larger one. When more sections qualify, keep those whose behaviour the
  skill's workflow depends on most.

**Tested fact by fact.** A claim's facts are the rules, values, thresholds, steps and
reasons its statement gives, and its cases spread over them: each fact a source can key
gets a case before any fact gets a second, since a second case on a tested fact is usually
a `duplicate`. Search for an independent source for each fact before leaving it untested,
and keep the spare case "Cases each grade requires" in `evidence-rubric.md` asks for. When
a claim states more facts than the run's subject-call budget has cases for, test the ones
the skill's user relies on most. The `coverage` justification of `select_local_candidate`
in `tool-contracts.md` records which case tests each fact, and the critique checks each
search it describes against Python's search record: a search the record does not show was
not made. In `fbd49132` every claim
settled with facts untested: one claim's three cases reached two of its five gotchas with
no search made for the other three, and two claims settled at B although their critiques
named the missing cases and the rounds to add them remained.

The report lists the sections no claim covers, and says when only its number of
independent cases held a claim below the grade its source supports.

## Legal operations

The `Local profile` matrix in workflow.md and `Local profile tools` in
tool-contracts.md define the same legality. Every internal mutation uses the
existing run ID, state token, step/repair budgets and journal. The planner must
lookup before discovering. References and candidates are immutable objects;
selection pins the exact candidate before any subject observation. A local
candidate can be reused offline by digest, including its reference evidence.

## Subject boundary

Each case starts a fresh Claude Code process in a temporary workspace outside the
controller project. A generated local plugin contains a recognized `submitted`
skill, its original instruction body and supporting files. The wrapper
replaces execution-affecting frontmatter; original bytes and the transformation
digest remain in the receipt. Explicit Skill-tool invocation and a successful
matching tool result are required. A prompt mentioning the skill is insufficient.
Dynamic skill shell interpolation and nested Claude configuration are unsupported.
Dependencies come from the pinned image, plus the packages the skill declares when the
operator has configured a package index ("Skill environment"). No trial installs
packages, and the subject's command tool says so: in run 84e90683 every trial of the ring-option claim
first tried to install RDKit, and two spent their whole limit on the attempt and on
working the answer out by hand.

Text sessions expose Skill and a bounded private submitted-file reader. Computational sessions
expose Skill and the private container/resource/app tools described above. Host
shell, unrestricted reads, delegation and unrelated MCP tools are unavailable.
The controller has WebSearch
and the exact internal verifier MCP tools, with no file or shell tools. Separate
configuration directories outside the subject workspace, disabled hooks/memory,
explicit system prompts, restricted mode, all-path CLAUDE.md exclusions and a
fresh empty repository root exclude unrelated local customizations.
Claude Code v2.1.268 or later is required: it is the earliest version the verifier's
reply schemas were tested on. Managed enterprise configuration and
the CLI itself remain part of the trusted host; the text session is not an OS sandbox.
Before the planner starts, the runner asks the pinned model for a one-word reply in a
fresh no-tool session. A CLI that cannot serve that model stops the run as
`model_unavailable` before any planner or subject cost; run a8036722 once died three
seconds into its planner for that reason.

Every trial must be answered by one model, the same one throughout the claim's trial
set. Subject sessions run with Claude Code's model substitution and refusal fallback
switched off (`CLAUDE_CODE_NO_MODEL_FALLBACK` and `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK`,
undocumented switches present in CLI 2.1.268), and Python still reads each stream
rather than trusting the switches. A `<synthetic>` message is a notice the CLI writes,
not a model. A trial another model answered is not the pinned model's evidence: after a
safety refusal it is `subject_refused`, naming the model that answered; otherwise it is
`subject_model_changed`. A refusal the pinned model then answered itself counts, with
the refusal recorded on the trial. Run 3dc02567 showed all three: Opus 5 refused an
R-group question, Opus 4.8 answered two trials in its place, and Opus 5 answered the
third itself.

No reference answer, candidate, evaluator file, verifier conversation or arbitrary
planner instruction is included in subject input. Subject input is the frozen
case input, the answer-format line Python writes from the case's answer type, and the
pinned skill. A process deadline and output ceiling are
enforced; timeout/cancellation terminates the process tree. A trial that reaches its
deadline is `claude_timeout`, and its record names the case, the trial and the
`subject_timeout_seconds` it reached. That limit is this verifier's setting, not a
property of the skill, and the report says so. An interrupted trial
request is retained and is never silently replayed. Restarting verification
creates a new run and discloses a new evidence sample.

One disclosed retry is the exception. When `write_report_card` is called, Python
re-runs once, in full, each claim whose execution a subject-trial fault stopped: a
safety refusal, a model switch, a CLI failure or timeout, or a container failure. The
retry uses the same frozen plan, model and inputs. A wrong answer is never retried,
because it is evidence; neither is a security fault or a failure of Python's own checks.
The first attempt's record and receipts stay in the report beside the retry's. A claim
is not retried, and the report says why, when its plan settled no execution grade (the
documentary step after it needs the planner), when the subject-call budget cannot
cover it, or when less time remains before the attempt deadline than one minute per
trial plus five for the report. A claim the re-run does not clear, or that is not
re-run, then receives the fallback documentary assessment described under
"Independent documentary path".

## Reading replies

Every reply scored by an installed comparison method is read in two steps.

**Python's reader** finds the reply's answer line and compares it with the expected
answer by the case's answer type, under the rules `qualify_local_candidate` in
`tool-contracts.md` owns. A reply it passes is a pass, and nothing overturns that.

**The AI reader** reads every other trial of a counted case, one Python's reader
failed or could not read, once all of the claim's trials have run. Each reading is a
fresh no-tool session on the pinned model, two minutes long, four at a time. It sees
the case's question, the answer-format line, the answer type, the expected answer and
the reply. It never sees the claim, the skill, the design, the grade, any other trial
or Python's verdict. Its reply has a fixed schema, enforced like the critique's: it
says whether the answer the reply commits to `matches` the expected answer, `differs`
from it, or is `no_single_answer` (several answers, a hedge, a refusal or none), and
gives that answer copied from the reply, with a reason. It never judges whether the
expected answer is right, and it cannot change it.

An accepted reading decides the trial: `matches` is `pass`, `differs` is `fail` and
`no_single_answer` is `invalid`. Python refuses a reading, and the trial keeps Python's
verdict, when:
- the copied answer is not in the reply;
- another model answered;
- or Python's reader settles the copied answer the other way. A `matches` whose copied
  answer Python reads as a different number or option is refused, and so is a
  `differs` whose copied answer Python's reader passes.

A reader session that fails also leaves Python's verdict. No reading is ever retried,
because reading again until the answer changes is verdict shopping. A synthetic run has
no reader, since its status is withheld anyway. The claim-only answers under
`select_local_candidate` are read the same way, except `UNDETERMINED` and the reserved
`none of these`, which say what they mean.

**What a reading changes.** The expected answers and the comparison rule are fixed
before any trial runs. A reading only establishes what a reply says, so it never moves
the grade; "AI-involvement disclosure" in `evidence-rubric.md` owns that rule. Every
reading is disclosed:
- each AI-read trial's score receipt and report row carry the reading, the copied
  answer, the reason and Python's own verdict;
- the result's `reading_summary` counts the counted trials the AI reader read and
  changed, and gives the status and accuracy Python's reader alone would give;
- a reading that changed a counted trial makes `ai_involvement.verdict` a sentence
  saying so, and adds `trials_decided_by_ai_reader` to the execution limits.

## Authentication and storage

Subscription mode accepts `CLAUDE_CODE_OAUTH_TOKEN`, generated by the user's
Claude Code subscription login/setup-token flow. API mode accepts
`ANTHROPIC_API_KEY` and uses bare mode. Credentials are inherited only into the
appropriate process environment, never arguments or saved configuration.
Each process receives an allowlisted environment and isolated configuration.
Authentication requires user setup; the verifier does not extract saved secrets.

`.verifier/candidates/` holds immutable qualified configurations and private
reference evidence. `.verifier/subject-runs/` holds sanitized execution receipts;
temporary executable workspaces are removed after each process. On Windows a child
process can hold a file briefly after its parent exits, so removal is retried for a
bounded time. Removal also uses the extended-length path form: Claude Code saves a large
tool result deeper than Windows' 260-character path limit, and without that form the file
is invisible and its directory stays. A directory that still cannot be removed is logged as
`temporary_cleanup_incomplete` with its path, and never turns a completed run into a
failed one. Each verification then starts by removing this verifier's own
`sci-verifier-*` temporary directories older than a day, logged as
`stale_temporary_swept`; nothing younger is touched, so a run in progress is never swept.
Configured candidate bundles are fetched by exact digest, requalified and cached
under `.verifier/catalog-cache/` for offline reuse. They contain candidates and
their referenced objects only. Imported review assertions never confer scientific
approval. Operator settings pin independently trusted reviews separately.

`scripts/local_catalog.py` lists, exports, imports, proposes, revises and reads the
review of candidate bundles. The order is: the agent prepares and checks, the agent
opens a draft pull request, a person reviews it there, the agent addresses the
comments, and the person accepts by merging.

Export records the agent's own `redistribution` assessment naming the licence and
source of every included reference. That is a prepared statement for a reviewer to
judge, not a sign-off, and no human authorization is required to create a bundle.
Exports exclude subject outputs, logs and operator settings. `publish` needs the
exact bundle digest and repository and opens one draft GitHub PR whose branch is
derived from the proposal identity. Publishing the same unchanged file again pushes
nothing; publishing a changed file commits a revision onto the same branch and pull
request. It never merges, never promotes, never overwrites a branch it did not
create and never reruns subjects. A durable receipt with remote reconciliation makes
retries independent of runs. `review` reads the pull request state, reviews and
comments so the agent can address them; it writes nothing.

`release` prepares a versioned catalog inventory from an exact qualified bundle plus
one prepared assessment per candidate, each carrying a propose-for-catalog or
propose-retirement proposal, provenance, scope, coverage, uncertainty, redistribution
assessment and an explicit `scientific_approval: not_conferred`. Every candidate is
requalified in disposable storage before a release can exist. These records give a
reviewer something specific to review; they confer no approval and no claim grade.
Release envelopes pin the embedded bundle, catalog ID/version, runtime version
range and optional predecessor digest. Updates require increasing versions and
retain prior candidate IDs, with explicit retirement instead of silent removal.
Configured releases are verified and requalified before run creation; their
immutable receipts and retirement set are pinned to that run. Retired candidates
are excluded from new selection, including cached copies. Active runs keep their
original inventory. Conflicting configured versions of the same catalog fail
before execution. Exact cached releases support offline use. The same opt-in
draft publication path accepts prepared releases under content-addressed
`catalog/releases/`; maintainers review and merge them before distribution.
Consumers deliberately choose the exact release file URL (prefer a GitHub commit
pin) and SHA256. Automatic upgrades, merging and scientific approval are excluded
from this maintenance interface.

## Acceptance

Every public verification attempt now requires an automatic diagnostic workflow
log, allocated before source/preflight checks under `.verifier/attempts/<id>/`.
It records observable stage/tool/process activity and errors, with a run ID once
one exists. Structured event files are durable; readable JSONL/Markdown timelines
are projections. The scientific journal remains authoritative for state and
results. Logs never provide expected answers to the subject, persist credentials,
or claim to capture private model reasoning. Failures return the attempt/log
location when storage is available; inability to record required events stops
execution rather than silently claiming a complete log. Live Claude streams and
internal tool operations must both be captured, including partial failed runs.
Logging never delays reading a process's output: the pipe readers only read, and the
thread waiting for the process logs its stream, so a slow log costs time, never output.
A write reads back only event files it has not verified or whose size or modification
time has changed, and those must still verify. In run d416f79d every write re-read
every earlier event, a write took 0.94 s by the 2,100th, and readers that logged as they
read left two finished claim-only answers unread.
A run the runner closes early records who stopped it and why, in the categories of
`artifact-contracts.md`: `cancelled` only for the operator's cancellation, `timeout`
for the attempt deadline, and otherwise `agent_unavailable` with the planner's own
last reported termination reason. Every such stop used to be recorded as the
operator's cancellation; run 7f88fbef's planner had in fact hit the subscription
session limit (HTTP 429).
The public stdio connection processes cancellation notifications while a request
is running and permits one active verification per connection. Cancellation or
connection closure stops the managed process tree and preserves partial evidence;
cleanup/reporting may continue briefly. A total attempt deadline covers setup and
catalog qualification as well as the planner. Clients supplying a progress token
receive bounded stage notifications, without subject text or credentials.

Fixtures must cover empty lookup/discovery, qualification and offline reuse,
rejected provenance/controls, unknown license metadata, hidden-answer exclusion,
explicit invocation failure, isolated configuration, both authentication modes,
secret absence, timeouts, partial/interrupted execution, stale tokens, immutable
recovery, zero claims and mixed outcomes. Fixtures prove implementation behavior;
only a real Claude Code run can establish live CLI acceptance. Missing executable,
credentials or usage is reported as unavailable, never simulated as live success.

Implementation references checked 2026-09-11: [CLI flags](https://code.claude.com/docs/en/cli-reference),
[programmatic execution](https://code.claude.com/docs/en/headless),
[skills](https://code.claude.com/docs/en/skills), and
[environment variables](https://code.claude.com/docs/en/env-vars).
