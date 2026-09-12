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

## Scientific review, plan audit and deterministic grade policy

Selection freezes source, subject/configuration, candidate, trial count, tolerances
and the `all-trials-v1` policy and writes a deterministic audit before execution.
Operator-controlled `scientific_reviews` can authorize grades A/B/C for one exact
candidate fingerprint, source-content digest, execution-environment digest and
scope, with an explicit list of accepted observed model IDs. A review must name the independent reviewer,
date, provenance, scientific basis, coverage, uncertainty, independence and minimum
trial count. It explicitly lists the supported rubric grades; supporting A does
not automatically authorize B or C. The planner cannot create or alter reviews.
This is a personal trust boundary, not a claim that a signature service or the
software has verified the reviewer's credentials. Default reviews remain empty.

The installed policy requires every planned trial and case to be scored. Missing
observations are operational. Invalid observations remain counted and prevent an
A/B/C grade. Scored-status agreement must be unanimous within each case for a
grade; unanimous failure is as eligible as unanimous success. There must be at
least three distinct cases. A/B require at least three trials of this model-based
subject. C may use one if independently authorized. The review may require more.
The verdict is pass only if all scored trials pass, fail if at least one fails
and none is invalid, and inconclusive if any is invalid. Choose the strongest
explicitly supported grade meeting every predicate. No eligible branch grants no
scientific verdict and requests a separate documentary assessment; it never
silently invents a weaker grade. Synthetic observations never receive a grade.

Observed model identities must remain constant across trials of a claim. Changing
code, source, image, configuration, plan or candidate invalidates the bound audit.
Without independent scientific authorization, mechanically qualified evaluations
remain useful comparison evidence with no scientific status or grade.

## Independent documentary path

After an execution with no eligible A/B/C grade, the live local workflow enters
`local_documentary`. The planner either supplies bounded cited evidence for a
fresh assessor or records searches establishing no acceptable evidence. A new
Claude session, selected by the host, receives the exact claim, source quotes,
limitations and fixed rubric only. It has no tools or planning history. Its final
JSON must contain a status, supported rubric findings and exact citations to the
pinned packet. Invalid or missing assessments are operational failures.

An operator review bound to the exact installed rubric is needed for grade D.
Without it, retain the assessment and disclose that scientific authorization is
absent. Grade D is documentary consistency only; execution accuracy remains
unverified. U/inconclusive is a separate no-evidence path requiring catalog
lookup and an explicit search account. Runtime failures never establish U.
Legacy synthetic adapters retain their comparison-only terminal behavior.

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
Those remain planner assertions unless independently reviewed under the policy
above. Reports separate comparison outcomes from scientific status and grade.
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

`scripts/local_catalog.py` lists, exports, imports and explicitly publishes
candidate proposals. Export requires a written redistribution authorization for
all selected reference assets. It excludes subject outputs, logs, settings and
operator scientific approvals. Publish requires the exact reviewed bundle digest,
explicit repository and `--approve-publication`; it creates a draft GitHub PR,
never merges, promotes, overwrites an existing branch or reruns subjects. A durable
publication receipt and remote reconciliation make retries independent of runs.
Maintainers use `scripts/local_catalog.py release` to prepare a versioned full
catalog inventory from an exact qualified bundle and independent review records.
Each candidate has an approved-for-catalog or retired decision, reviewer,
provenance, scope, coverage, uncertainty and redistribution assessment. The
operator must explicitly authorize promotion. This gate records actual supplied
review evidence; it cannot authenticate a reviewer or confer a claim grade.
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
