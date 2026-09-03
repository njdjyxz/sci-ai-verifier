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
- Append-only capability-selection revisions for this claim, as defined below.
- `report_note`

Type assignments are immutable. Each capability lookup operates on exactly one accepted claim and appends a selection revision; it never changes another claim's state. A selection contains:

- Stable selection ID, revision, claim ID, queried scope, and intended grade ceiling.
- `capability_outcome`: `registered_evaluator_available`, `generic_harness_available`, `lower_grade_available`, `subject_runner_unavailable`, or `implementation_required`.
- `resolved_grade` and `capability_kind` (`registered` or `target`) when a complete supported selection exists; otherwise explicit `not_applicable` values.
- Compatible evaluator or generic-harness IDs, versions, and digests for the resolved grade, plus approved compatible subject-runner identities for A through C; documentary D records `subject_runner: not_applicable`.
- Matching lower-grade alternatives and the reasons stronger grades were unavailable.
- Evaluator-registry and subject-runner-catalog revisions and digests used for the lookup.
- Operational-outcome ID for `subject_runner_unavailable` or `implementation_required`.

Python searches grades A through D at or below the intended ceiling for complete matches: evaluator-or-harness plus subject runner for A through C, approved documentary capability without a subject runner for D. It resolves the strongest compatible grade first and prefers a registered evaluator over a target harness at that grade. `lower_grade_available` records the selected lower grade and capability kind explicitly; the agent does not derive a next state from unselected fallback candidates. A later downgrade or scope change creates a fresh selection revision and preserves the prior lookup provenance.

An evaluator match records capability only. It is not evidence that an evaluator ran or that a claim passed.

## Evaluation plan

Target path: `.verifier/runs/<run-id>/plans/<claim-id>.json`

Contains:

- Plan ID, claim ID, and claim-type ID.
- Plan revision and the exact capability-selection ID and revision authorizing its scope, planned grade, evaluator or harness, and subject runner.
- `plan_kind`: `registered` or `target`.
- Requested or target grade and current planned grade.
- Evaluator ID and version, or the target evaluator specification.
- For a target plan, the exact approved generic-harness ID, version, and bounded configuration contract.
- Immutable source-snapshot ID and digest.
- Required resource roles and selection criteria.
- Resource-lock ID bound to this run, claim, plan ID, and semantic plan revision. Binding events record exact lock versions/digests and unresolved roles as materialization progresses; even an empty-role plan has an explicit complete empty lock.
- Expected inputs, outputs, oracle, tolerances, metrics, and decision rules.
- Deterministic invalid-case, coverage, scoring, and verdict rules for grades A through C, or the audited documentary rubric and assessor boundary for grade D.
- Case-construction method and coverage expectations.
- The subject-runner configuration described below.
- Execution method, environment requirements, and budget.
- Known limitations, exclusions, AI involvement, and report notes.
- Plan revision history and downgrade reasons.
- Audit repair requirements, invalidated resource roles, and excluded evaluator/bundle bindings when this revision repairs an earlier audit.
- Mutually exclusive current outcome code, next permitted state, and legal next tools.

Before a complete new plan is possible, a bounded `reselection_request` may be appended to the claim's plan history with its own request ID, prior plan revision, proposed grade/scope, authoritative trigger, reason, and invalidated execution authorization. It is not a new executable plan or semantic revision: unavailable evaluator, runner, rubric, and resource fields are not fabricated. Capability selection consumes this recorded target; the subsequent complete `plan_commit` creates the new revision and lock.

### Subject-runner configuration

For grades A through C, the subject runner turns a bundle case into an output for the evaluator to score, so its configuration is part of the plan and audit. Documentary D does not execute the subject and records runner, subject model, trial count, aggregation, and trial-grade policy as `not_applicable`; an absent runner catalog does not prevent a documentary plan. Execution-grade configuration contains:

- `subject_runner_id`, version, and digest, plus the reviewed catalog revision and digest from capability selection.
- `subject_model` identity and version when the runner drives a model, or the entry point and dependency lock when the skill exposes a deterministic non-model interface.
- Generation settings that affect output: reasoning effort, sampling parameters, and any supported seed.
- `trial_count`: how many independent times each case is run.
- `aggregation_rule`: the deterministic reduction from a case's individually scored trial verdicts and metrics to one per-case outcome, fixed before execution and identified by a stable rule ID. The evaluator scores each raw trial before this reduction; the subject runner never receives the oracle to perform aggregation.
- For grades A through C, `trial_grade_policy`: the audited policy ID, version, digest, bounded parameters, and total claim-specific eligibility rules over subject mode, counts, scored-trial agreement, and coverage. Rules select the strongest supported A-through-C ceiling or `no_supported_execution_grade`; they never raise the planned/audited ceiling and are fixed before execution. The latter result returns to planning to attempt D, not directly to a D/U result. Scientific constraints are defined in [Evidence Rubric](evidence-rubric.md); there are no universal numerical cutoffs beyond its explicit single-trial cap.
- Isolation guarantees: what the subject receives, and the confirmation that expected answers, oracle instructions, split membership, and other cases' results are not among them.

An A-through-C plan with absent/incomplete subject-runner configuration cannot authorize execution. `trial_count` of one is legitimate for a deterministic subject and is recorded with the reason. Documentary D's explicit `not_applicable` markers are not missing configuration.

A plan is not executable until its audit artifact passes and all referenced assets are locked by digest. Changing the subject model changes the plan.

## Resource lock

Target path: `.verifier/runs/<run-id>/resource-locks/<claim-id>/<plan-revision>.json`

Each lock belongs to exactly one run, claim, plan ID, and semantic plan revision. Its envelope records that binding and append-only lock versions or events; the lock ID is stable within that plan revision, and each committed version has its own digest and creation time. Materialization appends binding/state events without changing the semantic plan revision or creating another lock. A semantic change to scope, grade, resource requirements, rules, or configuration creates a new plan revision and lock. Audits, execution records, and results pin an exact committed lock version/digest, never a mutable "latest lock."

Each version contains the complete selected-resource set for that plan revision:

- Resource ID and immutable version or digest.
- Required role ID owned by this plan revision; identical role names on other claims do not confer ownership or satisfy this plan's requirements.
- Source and provenance.
- Scientific scope and relevant fields.
- Independence relationship to the submitted skill and evaluator.
- License, access, retention, and redistribution constraints.
- Managed payload location or reproducible retrieval reference.

The lock references payloads; it does not embed large datasets. A payload may be deduplicated in the managed store without sharing its plan authorization.

When a plan is revised, Python creates a new revision-bound lock. It may copy references from an earlier lock only after revalidating each exact resource's digest, role, scope, independence, governance, and compatibility against the new revision; the new lock records the source lock and revalidation findings. It never implicitly inherits a previous revision's or another claim's role coverage. Failed revalidation returns the new revision to resource resolution rather than retaining stale authorization.

An audit repair invalidates the affected plan's lock and asset bindings by appending an invalidation event; it does not modify globally reusable validated assets. `resource_change_required` returns to capability selection with committed `repair_requirements`, `invalidated_resource_roles`, and `excluded_binding_ids`. The lookup excludes the stale evaluator/bundle binding for this claim at every grade. It may select the originating approved harness for reconstruction or a different compatible registered evaluator/bundle pair, but it cannot silently reuse the excluded binding. The next plan receives a new revision and lock; affected roles must be materialized or explicitly revalidated before a fresh audit. The replacement selection, plan, lock, and audit retain predecessor references and the repair directive for traceability.

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

- `generic_harness`: approved reusable implementation code with a stable harness ID and version, deterministic or documentary mode, supported input/output contracts, bounded configuration schema, environment lock, supported metrics and decision behavior, grade ceiling, security-review provenance, scope, and status. An A-through-C harness also declares per-trial scoring/aggregation contracts and scientifically justified trial-grade-policy IDs, versions, digests, and allowed parameter bounds; a documentary harness declares its rubric/assessment response contract.
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

## Reviewed subject-runner catalog

Target path: `registry/subject_runners.json`. There is no runtime overlay and no workflow tool may write this file. Its root contains integer `schema_version` (currently `1`), nonnegative integer `revision`, and a `subject_runners` array. An empty array is a valid catalog with no installed subject runners, not a malformed registry.

Each reviewed entry contains:

- Stable `subject_runner_id`, immutable version, and content digest.
- `mode`: `model` or `deterministic`.
- Reviewed implementation entry point and implementation digest, environment reference and digest, and dependency-lock reference and digest.
- Supported input and output interface contracts, claim scope, and compatibility restrictions used by capability selection.
- For model mode, a model-identity/version allowlist and bounded generation-settings schema; deterministic mode marks these fields `not_applicable`.
- Minimum and maximum supported `trial_count`, plus any documented deterministic single-trial exemption.
- Supported evaluator-side aggregation-rule IDs; these declare compatibility and never authorize the subject runner to access expected answers.
- Isolation guarantees and allowed capabilities, including filesystem, network, credential-provider, time, and resource limits.
- Security-review provenance and `status`: `validated` or `retired`.

Configuration is bounded data only; the verifier agent cannot supply implementation paths, executable code, arbitrary network endpoints, or capabilities beyond the reviewed entry. Python resolves implementations from validated entries and pins both the entry and catalog digests. Retired entries remain available for reproducing old records but cannot authorize a new plan.

A valid catalog with no compatible validated runner returns claim-scoped `subject_runner_unavailable` only when an A-through-C evaluator/harness would otherwise fit and no documentary D capability fits. A fitting D capability is a normal match with no subject-runner requirement, including when the catalog is empty or absent. Absence of any suitable evaluator or harness returns `implementation_required` instead. Malformed registry structure, conflicting immutable entry identities, or failed catalog integrity is a fatal registry error, never ordinary runner unavailability.

## Plan audit

Target path: `.verifier/runs/<run-id>/audits/<claim-id>.json`

Contains:

- Plan and asset versions audited, including the subject-runner version and the subject model it drives.
- Exact capability-selection revision and resource-lock ID, version, digest, and run/claim/plan/revision binding.
- Required objective checks and their Python results.
- For A through C, subject-runner prerequisite checks: configuration completeness, catalog membership, bounds, trial count/aggregation rules, and isolation from expected answers. Documentary D checks its explicit unused-subject markers and mandatory documentary harness/rubric/assessor boundary instead.
- For grades A through C, trial-grade-policy identity, version, digest, input definitions, and objective checks that eligibility is total, uses deterministic strongest-grade-first precedence, and cannot exceed the planned/audited grade.
- Bounded semantic assessment where needed.
- Evidence independence and AI-involvement assessment.
- Coverage, fairness, leakage, governance, provenance, and budget findings.
- `audit_status`: `pass` or `fail`, derived from the returned outcome code.
- `proposed_audit_status`: what the verifier agent proposed, and whether it agreed with the decision.
- Required repairs, grade ceiling, and unresolved risks.
- For `resource_change_required`, `repair_requirements`, `invalidated_resource_roles`, and claim-local `excluded_binding_ids` consumed by capability selection; these are not global asset retirement records.
- Any atomic evaluator and bundle promotion performed by a passing audit.

`audit_status` and the outcome code are one decision recorded twice for different readers, not two judgments; Python derives the former from the latter. The agent's proposal is recorded next to them as evidence about the agent, not about the plan. A disagreement is a reportable finding rather than a defect to repair.

A failed or stale audit cannot authorize evaluator execution.

## Documentary assessment

Target path: `.verifier/runs/<run-id>/assessments/<assessment-id>.json`

For grade D, the runner completes an independent assessment during `execute_evaluation_plan`, before permitting `result_commit`. The artifact contains:

- Stable assessment ID and run, claim, plan revision, audit, execution, and source-snapshot references and digests.
- Audited documentary harness and rubric IDs, versions, and digests.
- Immutable judgment-packet ID and digest, bounded evidence excerpts, and citations supplied to the assessor.
- Assessor identity, type (`human` or `model_session`), and, where applicable, provider, model, and separate session/response identifiers.
- Planning-session identity and Python's independence check, including a context manifest confirming the model assessor received only the approved assessment instructions, audited rubric, and bounded evidence packet, not the planning conversation.
- Completed criterion findings, supporting citations, bounded judgment rationale without private chain-of-thought, and rubric-derived `status`: `pass`, `fail`, or `inconclusive`.
- Explicit AI or human judgment disclosure and relevant limitations.

The host supplies an approved separate assessor session or an identified independent human through its configured assessment adapter; the planning agent cannot serve as its own assessor or invent an assessor identity. Python validates identity, independence, rubric conformance, evidence references, and completeness before recording the assessment as completed and returning `documentary_assessment_ready`. `commit_claim_result` references this immutable completed artifact and copies its status; the planning agent may explain but cannot replace the judgment.

If no approved independent assessor is available, the runner records `assessor_unavailable` and terminates the claim operationally. It does not enter `result_commit`, fabricate a grade-D status, or substitute grade U for unavailable assessment infrastructure. Assessment acquisition/validation failure or an incomplete response cannot authorize a result. A completed, validated assessment whose scientific status is `fail` is a valid grade-D result and must not be classified as assessor failure.

## Operational outcome

Target path: `.verifier/runs/<run-id>/operational-outcomes/<outcome-id>.json`

The runner creates this artifact automatically whenever a claim or run cannot continue for an operational reason. It contains:

- Stable outcome ID and `scope`: `claim` or `run`.
- Claim ID when claim-scoped.
- Workflow state, attempted tool, and stable reason code.
- Category such as `tool_unavailable`, `implementation_required`, `subject_runner_unavailable`, `assessor_unavailable`, `resource_unavailable`, `retry_limit`, `illegal_transition_limit`, `agent_unavailable`, `step_limit`, `cost_limit`, `execution_limit`, `timeout`, `cancelled`, `fatal_tool_result`, or `corrupted_state`.
- For `agent_unavailable`, the model-side termination reason and any mitigation the runner attempted, since no tool ran and there is no tool result to inspect.
- Attempts used, applicable limits, structured errors, and committed artifact references.
- Confirmation that the outcome is terminal for the current run, whether a future run may reuse any completed parent artifacts, and the earliest safe restart state.
- User action that could make a future run possible, when known.
- Cleanup and retention status.

Operational outcomes are Python-authored terminal records, not verifier-agent prose. Claim-scoped outcomes allow independent claims to continue. A run-scoped outcome stops new scientific work. If reporting remains available, the runner reserves finalization capacity and declares `write_report_card` as the only legal tool; otherwise `run.json` and the outcome artifact are the authoritative incomplete-run record. If storage failure prevents both artifacts from being written, the runner returns `operational_outcome_persistence_failed` with no outcome ID and must not claim that reporting or durable audit completed.

## Claim result

Target path: `.verifier/runs/<run-id>/results/<claim-id>.json`

Every claim result contains the claim, route, plan, source-snapshot, applicable evidence references, requested/planned/achieved grades, coverage, AI involvement, warnings, and report notes. It uses one of these mutually exclusive forms:

- `evaluated_result`: evidence grade A through C; requires audit, execution, evaluator, bundle, and revision-bound resource-lock references. Python copies the deterministic execution status and strongest `achieved_grade_ceiling`, rejecting a different status or grade.
- `documentary_result`: evidence grade D; requires an audited documentary-rubric harness and a completed independent documentary-assessment artifact with judgment packet, citations, assessor identity, and disclosed AI or human judgment. Python copies the assessment's `pass`, `fail`, or `inconclusive` status and rejects a different one.
- `unverified_result`: evidence grade U; status is fixed to `inconclusive`, and attempted-evidence provenance plus explicit `not_applicable` markers replace stages that never ran.

Additional fields include:

- `result_kind`: `evaluated_result`, `documentary_result`, or `unverified_result`.
- `status`: `pass`, `fail`, or `inconclusive`, subject to the form rules above.
- `evidence_grade`: A, B, C, D, or U.
- Requested, planned, and achieved grade.
- Metrics, tolerances, decision outputs, and raw-output references.
- Coverage including tested cases, included scope, and excluded scope.
- For an evaluated result: the subject-runner identity and catalog provenance, subject model, generation settings, trial count, aggregation-rule identity, per-trial output and evaluator-score references, aggregated case outcomes, and observed per-case trial agreement.
- For an evaluated result: the exact audited `trial_grade_policy` ID, version, and digest (`grade_policy_ref`), measured inputs and matched branches, `grade_limit_reasons`, requested/attempted/obtained/evaluated/invalid/missing trial counts, and authoritative `achieved_grade_ceiling` copied from execution. The result cannot substitute an agent-estimated ceiling or different grade.
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
