# Artifact Contracts

This reference defines what the verifier retains and returns. Field-level JSON Schemas will be implemented with the Python tools; these Markdown contracts are the reviewed source for their intended meaning.

## Common requirements

Every persisted artifact contains:

- `schema_version`, a positive integer. It is a number in every artifact and registry file, never a string, so versions compare by value rather than lexically.
- A Python-assigned stable ID where the artifact is reusable or referenced elsewhere.
- `created_at`
- The run or parent artifact ID that produced it.
- Content or source digests needed to reproduce the decision.
- Tool and implementation versions involved in deterministic operations.
- Verifier-agent provider, model, and response identifiers for semantic decisions, without storing hidden chain-of-thought.

The verifier agent's model identity is never the submitted skill's. Artifacts that record an execution record both, under distinct fields, and neither may be derived from the other.

All text payloads are stored and hashed with newlines normalized to LF, and the normalization is recorded with the digest. Without this, the same submitted skill checked out on two platforms produces two snapshot digests and two different exact-quote comparisons, and every content-addressed guarantee in this file becomes platform-dependent. `.gitattributes` enforces the same normalization for repository content.

Committed artifacts are append-only throughout a run. A revision creates a new version or event rather than silently changing evidence; completion makes the accepted versions immutable.

## Run record

Target path: `.verifier/runs/<run-id>/run.json`

Contains:

- Run ID and lifecycle status.
- Submitted source path and name as provenance, plus the immutable source-snapshot ID and digest actually analyzed and executed.
- Start and completion time.
- Verifier `SKILL.md`, authoritative `workflow.md`, and `runtime-contract.md` versions or digests in force for the run.
- The verifier agent's provider and model identity, recorded separately from any subject model used by a plan.
- A context manifest recording stage references and tool definitions supplied to the verifier agent, their trust classification, versions or digests, and the state that authorized them.
- Requested minimum or target grade when provided.
- Step, retry, illegal-transition, cost, and execution limits, with the two retry budgets recorded separately.
- Available and unavailable Python tools.
- Current run and per-claim workflow states, with the committed artifact that authorized each state.
- Accepted state-transition history and rejected invalid-transition attempts.
- Artifact IDs produced by the run.
- Operational-outcome IDs produced automatically by the runner.
- Tool-call events, structured results, and operational errors.
- Finalization status and cleanup summary.
- Final completion or termination reason.

The transcript stores tool requests and results required for audit. It must not attempt to persist private model reasoning.

## Submitted-skill snapshot

Target manifest path: `.verifier/runs/<run-id>/source-snapshot.json`

The manifest references an immutable content-addressed payload in `.verifier/store/` or approved managed storage and contains:

- Source-snapshot ID and digest.
- Original resolved path as provenance only.
- Normalized relative paths, file digests, sizes, and total size.
- Top-level `SKILL.md` path, digest, encoding, and exact content reference.
- Per-file encoding and newline-normalization status, so a quote comparison is reproducible on any platform.
- Snapshot-policy name and version.
- Excluded paths with machine-readable reasons.
- Symlink, secret-pattern, cache, file-count, and size-limit findings.
- Which manifest entries have been read through `read_snapshot_file` during the run, so a resumed session can be re-supplied without repeating the reads.
- Creation time and integrity-verification status.

The runner snapshots regular files without following links outside the submitted root. Version-control data, caches, temporary outputs, `.verifier/`, environment directories, and files matched by the reviewed secret-exclusion policy are not copied. Credentials required at execution time come from approved runtime credential providers, never from the snapshot. A required file that cannot be safely snapshotted prevents execution rather than allowing the live source to be substituted.

The original path may change after loading. Claim extraction, resumption, auditing, and execution always use the immutable snapshot and reverify its digest.

## Claim manifest

Target path: `.verifier/runs/<run-id>/claim-manifest.json`

Contains one entry per atomic scientific claim:

- `claim_id`
- `statement`
- `scope`
- `expected_behavior`
- `source_path`: the snapshot-relative file the claim was extracted from.
- `source_quote`
- `report_note`

The manifest also records the source-snapshot ID and digest plus extraction provenance. Python validates exact source-quote presence against the recorded content of `source_path`, rejects duplicates, and assigns IDs after the verifier agent proposes the claims.

Claims may come from any file in the snapshot, not only the top-level `SKILL.md`. In practice a skill's testable scientific statements are often in bundled reference documents while the top-level file only routes to them, so `source_path` is what makes a claim traceable rather than merely quoted.

## Routing artifact

Target path: `.verifier/runs/<run-id>/routing.json`

Contains one route per accepted claim:

- `claim_id`
- `claim_type_id`
- `claim_type_source`: `existing` or `created`
- Claim-type index revision and digest.
- `capability_outcome`: `registered_evaluator_available`, `generic_harness_available`, or `implementation_required`.
- Matching evaluator IDs and versions, including compatible lower-grade fallbacks.
- Approved generic-harness IDs and versions that can implement a target plan.
- Evaluator-registry revision and digest used for both searches.
- Operational-outcome ID when capability outcome is `implementation_required`.
- `report_note`

Type assignments are immutable. Capability searches append a selection revision containing the queried scope and intended grade, so a later grade downgrade can reconsider registered evaluators without overwriting prior lookup provenance.

An evaluator match records capability only. It is not evidence that an evaluator ran or that a claim passed.

## Evaluation plan

Target path: `.verifier/runs/<run-id>/plans/<claim-id>.json`

Contains:

- Plan ID, claim ID, and claim-type ID.
- `plan_kind`: `registered` or `target`.
- Requested or target grade and current planned grade.
- Evaluator ID and version, or the target evaluator specification.
- For a target plan, the exact approved generic-harness ID, version, and bounded configuration contract.
- Immutable source-snapshot ID and digest.
- Required resource roles and selection criteria.
- Expected inputs, outputs, oracle, tolerances, metrics, and decision rules.
- Deterministic invalid-case, coverage, scoring, and verdict rules for grades A through C, or the audited documentary rubric and assessor boundary for grade D.
- Case-construction method and coverage expectations.
- The subject-runner configuration described below.
- Execution method, environment requirements, and budget.
- Known limitations, exclusions, AI involvement, and report notes.
- Plan revision history and downgrade reasons.
- Mutually exclusive current outcome code, next permitted state, and legal next tools.

### Subject-runner configuration

The subject runner is what turns a bundle case into an output for the evaluator to score. For a skill that is a set of model instructions rather than an executable, this is the component that actually exercises the claim, so its configuration is part of the plan and part of the audit:

- `subject_runner_id` and version, from the approved catalog returned by capability selection.
- `subject_model` identity and version when the runner drives a model, or the entry point and dependency lock when the skill exposes a deterministic non-model interface.
- Generation settings that affect output: reasoning effort, sampling parameters, and any supported seed.
- `trial_count`: how many independent times each case is run.
- `aggregation_rule`: the deterministic reduction from a case's trials to one per-case outcome, fixed before execution and identified by a stable rule ID.
- Isolation guarantees: what the subject receives, and the confirmation that expected answers, oracle instructions, split membership, and other cases' results are not among them.

A plan whose subject-runner configuration is absent or incomplete is not a plan with a missing field; it is a plan whose results cannot be reproduced, because nothing records what produced them. `trial_count` of one is legitimate for a deterministic subject and is recorded with the reason.

A plan is not executable until its audit artifact passes and all referenced assets are locked by digest. Changing the subject model changes the plan.

## Resource lock

Target path: `.verifier/runs/<run-id>/resource-lock.json`

Contains every resource selected for the run:

- Resource ID and immutable version or digest.
- Role in the evaluation.
- Source and provenance.
- Scientific scope and relevant fields.
- Independence relationship to the submitted skill and evaluator.
- License, access, retention, and redistribution constraints.
- Managed payload location or reproducible retrieval reference.

The lock references payloads; it does not embed large datasets.

## Evaluation bundle

Reviewed bundle metadata belongs under `registry/bundles/`; provisional metadata written during a run belongs under `.verifier/registry/bundles/`. A run references the registered bundle ID and version and does not care which layer it came from, beyond the `origin` recorded with it.

A bundle connects:

- Compatible claim-type IDs.
- Evaluator ID and version, or the approved generic-harness ID and version used to construct a provisional evaluator.
- Resource IDs and accepted versions.
- Case-generation recipe or immutable cases.
- Expected answers or oracle method.
- Tolerances, metrics, and decision criteria.
- Supported grade ceiling.
- Validated scope, exclusions, coverage, and known limitations.
- Validation and provenance records.

Input rows, expected answers, and split membership must remain separable so the submitted skill cannot read its expected outputs during execution.

## Evaluator registration

Reviewed metadata belongs in `registry/evaluators.json` and is changed only by human commits; entries written during a run belong in `.verifier/registry/evaluators.json`. Implementation code will belong under `evaluators/` when created, and is never written by a run. Lookups read the merge of both layers; every record carries `origin` (`reviewed` or `runtime`) alongside its registration status.

The registry contains two reviewed record kinds:

- `generic_harness`: approved reusable implementation code with a stable harness ID and version, deterministic or documentary mode, supported input/output contracts, bounded configuration schema, environment lock, supported metrics and decision behavior, grade ceiling, security-review provenance, scope, and status.
- `registered_evaluator`: one immutable bounded configuration of a generic harness tied to compatible claim types and a validated bundle.

Harness configuration is declarative data only. Its reviewed schema may allow field mappings, metrics, tolerances, rubric criteria, and decision thresholds, but never source code, imports, shell commands, arbitrary expressions, unapproved network endpoints, or filesystem paths outside locked artifacts.

Contains:

- Evaluator ID, name, and version.
- Approved generic-harness ID and version, validated configuration digest, and reviewed harness implementation entry point.
- Supported claim-type IDs.
- Supported grade ceiling.
- Required bundle and resource roles.
- Input and output contracts.
- Metrics, tolerances, and deterministic decision behavior.
- Execution environment and dependency lock reference.
- Validated scope, exclusions, and known limitations.
- Registration status and provenance.

The verifier agent cannot supply an implementation entry point or arbitrary evaluator code. Python resolves the implementation only from the approved harness catalog.

`provisional` means available for plan audit but not eligible for execution or a scientific verdict. `validated` means the exact evaluator, bundle, configuration, and plan passed audit for the stated scope and grade ceiling. A passing `commit_plan_audit` atomically promotes the exact provisional evaluator and bundle versions; a failed audit leaves them provisional.

## Plan audit

Target path: `.verifier/runs/<run-id>/audits/<claim-id>.json`

Contains:

- Plan and asset versions audited, including the subject-runner version and the subject model it drives.
- Required objective checks and their Python results.
- Subject-runner prerequisite checks: configuration completeness, catalog membership, bounds, trial count and aggregation rule against the claim and planned grade, and isolation from expected answers.
- Bounded semantic assessment where needed.
- Evidence independence and AI-involvement assessment.
- Coverage, fairness, leakage, governance, provenance, and budget findings.
- `audit_status`: `pass` or `fail`, derived from the returned outcome code.
- `proposed_audit_status`: what the verifier agent proposed, and whether it agreed with the decision.
- Required repairs, grade ceiling, and unresolved risks.
- Any atomic evaluator and bundle promotion performed by a passing audit.

`audit_status` and the outcome code are one decision recorded twice for different readers, not two judgments; Python derives the former from the latter. The agent's proposal is recorded next to them as evidence about the agent, not about the plan. A disagreement is a reportable finding rather than a defect to repair.

A failed or stale audit cannot authorize evaluator execution.

## Operational outcome

Target path: `.verifier/runs/<run-id>/operational-outcomes/<outcome-id>.json`

The runner creates this artifact automatically whenever a claim or run cannot continue for an operational reason. It contains:

- Stable outcome ID and `scope`: `claim` or `run`.
- Claim ID when claim-scoped.
- Workflow state, attempted tool, and stable reason code.
- Category such as `tool_unavailable`, `implementation_required`, `resource_unavailable`, `retry_limit`, `illegal_transition_limit`, `agent_unavailable`, `step_limit`, `cost_limit`, `execution_limit`, `timeout`, `cancelled`, `fatal_tool_result`, or `corrupted_state`.
- For `agent_unavailable`, the model-side termination reason and any mitigation the runner attempted, since no tool ran and there is no tool result to inspect.
- Attempts used, applicable limits, structured errors, and committed artifact references.
- Confirmation that the outcome is terminal for the current run, whether a future run may reuse any completed parent artifacts, and the earliest safe restart state.
- User action that could make a future run possible, when known.
- Cleanup and retention status.

Operational outcomes are Python-authored terminal records, not verifier-agent prose. Claim-scoped outcomes allow independent claims to continue. A run-scoped outcome stops new scientific work. If reporting remains available, the runner reserves finalization capacity and declares `write_report_card` as the only legal tool; otherwise `run.json` and the outcome artifact are the authoritative incomplete-run record. If storage failure prevents both artifacts from being written, the runner returns `operational_outcome_persistence_failed` with no outcome ID and must not claim that reporting or durable audit completed.

## Claim result

Target path: `.verifier/runs/<run-id>/results/<claim-id>.json`

Every claim result contains the claim, route, plan, source-snapshot, applicable evidence references, requested/planned/achieved grades, coverage, AI involvement, warnings, and report notes. It uses one of these mutually exclusive forms:

- `evaluated_result`: evidence grade A through C; requires audit, execution, evaluator, bundle, and resource references. Python copies the deterministic execution status and rejects a different status.
- `documentary_result`: evidence grade D; requires an audited documentary-rubric harness, judgment packet, citations, assessor identity, and disclosed AI or human judgment. Status may be `pass`, `fail`, or `inconclusive` under the audited rubric.
- `unverified_result`: evidence grade U; status is fixed to `inconclusive`, and attempted-evidence provenance plus explicit `not_applicable` markers replace stages that never ran.

Additional fields include:

- `result_kind`: `evaluated_result`, `documentary_result`, or `unverified_result`.
- `status`: `pass`, `fail`, or `inconclusive`, subject to the form rules above.
- `evidence_grade`: A, B, C, D, or U.
- Requested, planned, and achieved grade.
- Metrics, tolerances, decision outputs, and raw-output references.
- Coverage including tested cases, included scope, and excluded scope.
- For an evaluated result: the subject-runner identity, subject model, generation settings, trial count, aggregation-rule identity, and observed per-case trial agreement.
- AI involvement in orchestration, evidence generation, and verdict.
- Warnings, downgrade reasons, operational errors, and report notes.

Trial agreement is reported, never silently folded into the status. A result that held on every trial and one that survived aggregation are different claims about the skill, and a reader who cannot tell them apart has been given a number without its uncertainty.

The result status and evidence grade are independent. A high-grade failure is strong evidence against the claim; a low-grade pass does not establish broad scientific accuracy.

## Report card

Target paths:

- `.verifier/runs/<run-id>/report-card.json`
- `.verifier/runs/<run-id>/report-card.md`

The JSON file is authoritative. The Markdown file is its readable rendering.

The report card contains:

- Run and source provenance.
- One complete result or unresolved outcome per accepted claim.
- Stable operational-outcome IDs rather than agent-authored operational summaries.
- Coverage and exclusions.
- Requested versus achieved grades.
- Evaluator, bundle, resource, and version references.
- Subject-runner identity, subject model, trial count, aggregation rule, and observed trial agreement for every evaluated claim.
- AI-involvement disclosure, distinguishing the verifier agent's orchestration from any model that produced the evidence being scored.
- Warnings, limitations, provisional assets, review recommendations, and missing-tool notices.
- A list of returned artifacts and retained reusable assets.
- Finalization and cleanup status, including anything retained because cleanup could not complete.

Do not manufacture an overall grade from claim grades. The summary may count claim outcomes but must preserve claim-level meaning.
