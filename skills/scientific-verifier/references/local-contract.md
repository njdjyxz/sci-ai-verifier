# Local profile: implementation 0.7.0

## Computational execution and operator settings

The public action accepts an operator-selected `--config` JSON file. Settings
are validated and pinned into the subject identity. The planner cannot change
them. A pinned, already installed Linux Docker image enables computational
skills; absent configuration produces an operational limitation for those
skills. The verifier never installs dependencies during a subject trial.

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

## Negotiated evidence grade, plan audit and deterministic grade policy

Selection freezes source, subject/configuration, candidate, trial count, tolerances
and the `evidence-strength-v1` policy and writes a deterministic audit before
execution. The grade is settled during that selection and requires no human review.

The planner proposes `target_grade` A, B or C with an explicit justification.
Python computes an **evidence ceiling** from facts it recorded itself. Only that
ceiling, or a grade the last critique of the same design supported, may be proposed;
both overclaiming and aiming low are refused before any session is spent:

- **A** needs every expected answer quoted token-exactly from reference bytes Python
  itself retrieved over public HTTPS, scored by an installed comparison method, with
  at least three distinct cases and at least three trials of this model subject.
- **B** allows an operator-imported pinned dataset, or a generated Python evaluator
  whose controls all pass, under the same case and trial minimums. A planner-authored
  scorer cannot reach A, because direct validation excludes AI judgment in scoring.
- **C** covers any reproducible comparison meeting the case minimum, including a
  single trial, a substring rather than token-exact quote, and a candidate reused
  offline whose reference origin was never recorded.
- Failed controls or fewer than three cases support no execution grade.

A fresh no-tool session then receives the claim, the evidence design, the reference
provenance, the justification, Python's ceiling, the concerns earlier reviewers raised
about earlier versions of this design, and the fixed critique rubric. It never sees the
planning conversation, any subject answer, or any earlier reviewer's grade: objections
carry forward so a revision can be checked, grades do not, because a reviewer shown a
previous verdict would anchor on it. That separation is imperfect and is not claimed to
be complete: an objection such as "three cases cannot support direct validation" implies
a grade it does not state. Withholding the letter reduces anchoring; it does not remove
the signal. It returns the strongest grade the evidence
actually supports. The settled ceiling is the weakest of the proposal, Python's ceiling
and that critique.

When the critique supports less, the planner may strengthen the design and propose the
new ceiling, which earns another round, or accept the grade that design was critiqued
at, which settles immediately without another session. Repeating a proposal on a design
already critiqued is refused and consumes neither a session nor a round, so the budget
of one round per rubric grade bounds real revisions rather than repetition. Accepting a
critique that supported no grade settles the plan ungraded: it still executes and
produces comparison evidence, and the claim continues to the documentary path. An
unavailable critique is an operational limitation.

The installed policy then requires every planned trial and case to be scored. Missing
observations are operational. Invalid observations remain counted and prevent an
A/B/C grade. Scored-status agreement must be unanimous within each case for a grade;
unanimous failure is as eligible as unanimous success. The achieved grade is the
settled ceiling, or none when any of those conditions fails. The verdict is pass only
if all scored trials pass, fail if at least one fails and none is invalid, and
inconclusive if any is invalid. No eligible grade grants no scientific verdict and
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
limitations and fixed rubric only. It has no tools or planning history. Its final
JSON must contain a status, supported rubric findings and exact citations to the
pinned packet.

A reply whose *shape* is unusable — unparseable JSON, wrong keys, a findings list of
the wrong length — is retried at most once against an identical packet in a second
fresh session, and both attempts are recorded. A reply that parses but whose citations
do not quote the pinned packet is never retried: that is a judgement the assessor made
about the evidence, and re-rolling it until the answer is acceptable is grade shopping.
Only shape is retried, the packet may not change between attempts, and the first valid
assessment is the one that counts regardless of the status it carries. A second invalid
reply, or a missing assessment, is an operational failure.

A completed assessment against the installed rubric is grade D with the assessor's
status. Grade D is documentary consistency only; execution accuracy remains
unverified, and AI judgment is primary and disclosed. U/inconclusive is a separate
no-evidence path. Both require the claim's catalog lookup, evidence Python actually
retrieved for this claim, and no qualified candidate left unexecuted. Runtime
failures never establish U. Synthetic fixture runs stay ungraded.

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

The local implementation supports text and computational skills, pinned resources,
exact/numeric comparisons and qualified generated Python evaluators.
The planner extracts source-grounded claims, searches for independent primary
references with WebSearch, and proposes exact or numeric known-answer cases.
Python retrieves public HTTPS reference bytes itself; agent-authored quotes or
search summaries alone cannot qualify a candidate. Reference quotes and expected
values must occur in retrieved material. At least three distinct cases, positive
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

## Legal operations

The `Local profile` matrix in workflow.md and `Local profile tools` in
tool-contracts.md define the same legality. Every internal mutation uses the
existing run ID, state token, step/repair budgets and journal. The planner must
lookup before discovering. References and candidates are immutable objects;
selection pins the exact candidate before any subject observation. A local
candidate can be reused offline by digest, including its reference evidence.

## Planner context delivery

The pinned contracts reach the planner in its instruction turn, together with the
authorized source path and the current state token, because a tool reply large enough
for the host to spill to a file is unreadable to a session that has no file-read tool.
`get_verifier_context` therefore returns only a bounded header and serves each pinned
document or committed artifact as a separately requested section. The header is
checked against an inline budget and the run fails closed if it ever exceeds it,
rather than emitting a reply the planner might never see.

## Subject boundary

Each case starts a fresh Claude Code process in a temporary workspace outside the
controller project. A generated local plugin contains a recognized `submitted`
skill, its original instruction body and supporting files. The wrapper
replaces execution-affecting frontmatter; original bytes and the transformation
digest remain in the receipt. Explicit Skill-tool invocation and a successful
matching tool result are required. A prompt mentioning the skill is insufficient.
Dynamic skill shell interpolation and nested Claude configuration are unsupported.
Dependencies must already exist in the pinned image. No trial installs packages.

Text sessions expose Skill and a bounded private submitted-file reader. Computational sessions
expose Skill and the private container/resource/app tools described above. Host
shell, unrestricted reads, delegation and unrelated MCP tools are unavailable.
The controller has WebSearch
and the exact internal verifier MCP tools, with no file or shell tools. Separate
configuration directories outside the subject workspace, disabled hooks/memory,
explicit system prompts, restricted mode, all-path CLAUDE.md exclusions and a
fresh empty repository root exclude unrelated local customizations.
Claude Code v2.1.248 or later is required. Managed enterprise configuration and
the CLI itself remain part of the trusted host; the text session is not an OS sandbox.

No reference answer, candidate, evaluator file, verifier conversation or arbitrary
planner instruction is included in subject input. Subject input is the frozen
case input plus the pinned skill. A process deadline and output ceiling are
enforced; timeout/cancellation terminates the process tree. An interrupted trial
request is retained and is never silently replayed. Restarting verification
creates a new run and discloses a new evidence sample.

## Authentication and storage

Subscription mode accepts `CLAUDE_CODE_OAUTH_TOKEN`, generated by the user's
Claude Code subscription login/setup-token flow. API mode accepts
`ANTHROPIC_API_KEY` and uses bare mode. Credentials are inherited only into the
appropriate process environment, never arguments or saved configuration.
Each process receives an allowlisted environment and isolated configuration.
Authentication requires user setup; the verifier does not extract saved secrets.

`.verifier/candidates/` holds immutable qualified configurations and private
reference evidence. `.verifier/subject-runs/` holds sanitized execution receipts;
temporary executable workspaces are removed after each process.
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
