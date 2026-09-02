# Artifact Contracts

This reference defines what the verifier retains and returns. Field-level JSON Schemas will be implemented with the Python tools; these Markdown contracts are the reviewed source for their intended meaning.

## Common requirements

Every persisted artifact contains:

- `schema_version`
- A Python-assigned stable ID where the artifact is reusable or referenced elsewhere.
- `created_at`
- The run or parent artifact ID that produced it.
- Content or source digests needed to reproduce the decision.
- Tool and implementation versions involved in deterministic operations.
- Verifier-agent provider, model, and response identifiers for semantic decisions, without storing hidden chain-of-thought.

Artifacts are append-only within a completed run. A revision creates a new version or event rather than silently changing the evidence behind a published result.

## Run record

Target path: `.verifier/runs/<run-id>/run.json`

Contains:

- Run ID and lifecycle status.
- Submitted source path, name, and digest.
- Start and completion time.
- Verifier `SKILL.md` and authoritative `workflow.md` versions or digests supplied at bootstrap or resumption.
- A context manifest recording stage references and tool definitions supplied to the verifier agent, their trust classification, versions or digests, and the state that authorized them.
- Requested minimum or target grade when provided.
- Step, retry, cost, and execution limits.
- Available and unavailable Python tools.
- Current run and per-claim workflow states, with the committed artifact that authorized each state.
- Accepted state-transition history and rejected invalid-transition attempts.
- Artifact IDs produced by the run.
- Tool-call events, structured results, and operational errors.
- Final completion or termination reason.

The transcript stores tool requests and results required for audit. It must not attempt to persist private model reasoning.

## Claim manifest

Target path: `.verifier/runs/<run-id>/claim-manifest.json`

Contains one entry per atomic scientific claim:

- `claim_id`
- `statement`
- `scope`
- `expected_behavior`
- `source_quote`
- `report_note`

The manifest also records source and extraction provenance. Python validates exact source-quote presence, rejects duplicates, and assigns IDs after the verifier agent proposes the claims.

## Routing artifact

Target path: `.verifier/runs/<run-id>/routing.json`

Contains one route per accepted claim:

- `claim_id`
- `claim_type_id`
- `claim_type_source`: `existing` or `created`
- Claim-type index revision and digest.
- `route_status`: `evaluator_found` or `evaluator_not_found`
- Matching evaluator IDs.
- `report_note`

An evaluator match records capability only. It is not evidence that an evaluator ran or that a claim passed.

## Evaluation plan

Target path: `.verifier/runs/<run-id>/plans/<claim-id>.json`

Contains:

- Plan ID, claim ID, and claim-type ID.
- `plan_kind`: `registered` or `target`.
- Requested or target grade and current planned grade.
- Evaluator ID and version, or the target evaluator specification.
- Required resource roles and selection criteria.
- Expected inputs, outputs, oracle, tolerances, metrics, and decision rules.
- Case-construction method and coverage expectations.
- Execution method, environment requirements, and budget.
- Known limitations, exclusions, AI involvement, and report notes.
- Plan revision history and downgrade reasons.

A plan is not executable until its audit artifact passes and all referenced assets are locked by digest.

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

Reusable metadata belongs under `registry/bundles/`; a run references the registered bundle ID and version.

A bundle connects:

- Compatible claim-type IDs.
- Evaluator ID and version.
- Resource IDs and accepted versions.
- Case-generation recipe or immutable cases.
- Expected answers or oracle method.
- Tolerances, metrics, and decision criteria.
- Supported grade ceiling.
- Validated scope, exclusions, coverage, and known limitations.
- Validation and provenance records.

Input rows, expected answers, and split membership must remain separable so the submitted skill cannot read its expected outputs during execution.

## Evaluator registration

Reusable metadata belongs in `registry/evaluators.json`; implementation code will belong under `evaluators/` when created.

Contains:

- Evaluator ID, name, version, and implementation entry point.
- Supported claim-type IDs.
- Supported grade ceiling.
- Required bundle and resource roles.
- Input and output contracts.
- Metrics, tolerances, and deterministic decision behavior.
- Execution environment and dependency lock reference.
- Validated scope, exclusions, and known limitations.
- Registration status and provenance.

`provisional` means available for continued construction but not eligible for a scientific verdict. `validated` means its prerequisites and audit requirements are satisfied for its stated scope and grade ceiling.

## Plan audit

Target path: `.verifier/runs/<run-id>/audits/<claim-id>.json`

Contains:

- Plan and asset versions audited.
- Required objective checks and their Python results.
- Bounded semantic assessment where needed.
- Evidence independence and AI-involvement assessment.
- Coverage, fairness, leakage, governance, provenance, and budget findings.
- `audit_status`: `pass` or `fail`.
- Required repairs, grade ceiling, and unresolved risks.

A failed or stale audit cannot authorize evaluator execution.

## Claim result

Target path: `.verifier/runs/<run-id>/results/<claim-id>.json`

Contains:

- Claim, plan, audit, evaluator, bundle, and resource references.
- `status`: `pass`, `fail`, or `inconclusive`.
- `evidence_grade`: A, B, C, D, or U.
- Requested, planned, and achieved grade.
- Metrics, tolerances, decision outputs, and raw-output references.
- Coverage including tested cases, included scope, and excluded scope.
- AI involvement in orchestration, evidence generation, and verdict.
- Warnings, downgrade reasons, operational errors, and report notes.

The result status and evidence grade are independent. A high-grade failure is strong evidence against the claim; a low-grade pass does not establish broad scientific accuracy.

## Report card

Target paths:

- `.verifier/runs/<run-id>/report-card.json`
- `.verifier/runs/<run-id>/report-card.md`

The JSON file is authoritative. The Markdown file is its readable rendering.

The report card contains:

- Run and source provenance.
- One complete result or unresolved outcome per accepted claim.
- Coverage and exclusions.
- Requested versus achieved grades.
- Evaluator, bundle, resource, and version references.
- AI-involvement disclosure.
- Warnings, limitations, provisional assets, review recommendations, and missing-tool notices.
- A list of returned artifacts and retained reusable assets.

Do not manufacture an overall grade from claim grades. The summary may count claim outcomes but must preserve claim-level meaning.
