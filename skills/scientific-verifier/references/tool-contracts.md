# Python Tool Contracts

This file names the complete intended Python tool surface for the verifier. No active Python implementation exists in Stage 1. Later stages may implement these tools without changing their reviewed purpose; interface changes require a documentation update first.

## Planned runtime files

| Planned file | Responsibility |
|---|---|
| `src/sci_ai_verifier/agent.py` | Start the bounded verifier-agent session, assemble source-labeled context with explicit trust classes, reconstruct committed workflow state, expose only state-eligible tools, maintain messages, enforce step, retry, cost, and execution limits, and detect completion. |
| `src/sci_ai_verifier/tools.py` | Publish approved tool definitions, reject illegal state transitions, dispatch eligible tool calls, and convert expected exceptions into structured results. |
| `src/sci_ai_verifier/storage.py` | Perform atomic artifact writes, content hashing, run-workspace management, managed-store access, and registry locking. |
| `src/sci_ai_verifier/ingest.py` | Load submitted skills as untrusted UTF-8 data. |
| `src/sci_ai_verifier/claims.py` | Validate and commit claim manifests and assign claim IDs. |
| `src/sci_ai_verifier/routing.py` | Manage claim types and perform exact evaluator-registry lookup. |
| `src/sci_ai_verifier/planning.py` | Validate and persist registered and target evaluation plans. |
| `src/sci_ai_verifier/resources.py` | Search, inspect, materialize, validate, register, and lock scientific resources. |
| `src/sci_ai_verifier/evaluation.py` | Build and validate cases and bundles and register reusable evaluators. |
| `src/sci_ai_verifier/audit.py` | Validate plan prerequisites and persist bounded plan audits. |
| `src/sci_ai_verifier/execution.py` | Run audited evaluators and capture reproducible outputs and metrics. |
| `src/sci_ai_verifier/reporting.py` | Validate claim results and write machine-readable and human-readable report cards. |

These are planned boundaries, not permission for the verifier agent to call arbitrary functions inside the files. The runner exposes only the subset of approved tools allowed by the current state in `workflow.md`. Python revalidates state and prerequisites when dispatching every request; tool visibility alone is not authorization.

## Common result protocol

Every tool returns exactly one status.

Successful operation or ordinary workflow outcome:

```json
{
  "status": "ok",
  "data": {}
}
```

Correctable request or stale state:

```json
{
  "status": "retryable",
  "error": {
    "code": "stable_machine_readable_code",
    "message": "Short explanation",
    "details": {}
  }
}
```

Run or claim cannot continue safely:

```json
{
  "status": "fatal",
  "error": {
    "code": "stable_machine_readable_code",
    "message": "Short explanation",
    "details": {}
  }
}
```

`data` appears only with `ok`. `error` appears only with `retryable` or `fatal`. Empty searches, unsupported grades, inadequate bundles, failed audits, scientific failures, and missing evaluators are `ok` data because the verifier agent must route from them. A tool requested outside its permitted workflow state returns `retryable` without changing committed state.

## Load and profile tools

### `load_submitted_skill`

Planned implementation: `ingest.py`

Purpose: read one submitted skill without interpreting or executing its instructions.

Input: a path to a UTF-8 file or directory containing a top-level `SKILL.md`.

Successful data: resolved path, source name, source digest, size, and content.

Side effects: none.

Fatal conditions: missing, unreadable, empty, oversized, or invalidly encoded source.

### `commit_claim_manifest`

Planned implementation: `claims.py` and `storage.py`

Purpose: validate the verifier agent's candidate atomic claims, assign stable IDs, and persist the accepted manifest.

Input: source digest and claims containing statement, scope, expected behavior, exact source quote, and report note.

Successful data: manifest ID and accepted claims with Python-assigned claim IDs.

Side effects: writes the run's claim manifest.

Retryable conditions: missing fields, non-atomic or duplicate submissions identified structurally, or a source quote not present in the submitted skill.

Fatal conditions: source digest mismatch, storage failure, or corrupted run state.

## Routing tools

### `list_claim_types`

Planned implementation: `routing.py`

Purpose: return the complete controlled claim-type index for semantic comparison.

Input: empty object.

Successful data: index revision, digest, and claim types with IDs, definitions, inputs, outputs, boundaries, status, and provenance.

Side effects: none. A missing index is returned as revision zero with an empty list.

Fatal conditions: malformed or unsupported index schema.

### `commit_claim_type_assignments`

Planned implementation: `routing.py` and `storage.py`

Purpose: validate exactly one type assignment per accepted claim and persist necessary provisional types.

Input: manifest ID, observed index revision, and assignments. Each assignment supplies either one exact existing type ID or a complete proposed name, definition, inputs, outputs, and boundaries.

Successful data: updated index revision and one accepted claim route per claim.

Side effects: may add content-addressed provisional types to the shared index and writes run routing state.

Retryable conditions: stale revision, unknown existing ID, incomplete proposal, missing claim, or duplicate assignment.

Fatal conditions: registry corruption or storage failure.

### `find_registered_evaluators`

Planned implementation: `routing.py`

Purpose: perform an exact evaluator-registry lookup for every accepted claim route.

Input: accepted claim routes.

Successful data: evaluator IDs, versions, supported grade ceilings, bundle references, and `evaluator_found` or `evaluator_not_found` for every claim.

Side effects: none.

Retryable conditions: missing or unknown route IDs.

Fatal conditions: malformed evaluator registry.

## Planning tool

### `commit_evaluation_plan`

Planned implementation: `planning.py` and `storage.py`

Purpose: validate and persist one registered or target plan for a claim.

Input: claim and route IDs; plan kind; requested, target, and planned grade; evaluator or target-evaluator specification; required resource roles; oracle or evidence design; case method; metrics; tolerances; decision rules; coverage expectations; execution requirements; budget; AI involvement; limitations; and report notes.

Successful data: plan ID, revision, current grade ceiling, unresolved requirements, and next permitted stage.

Side effects: writes or revises the claim's run-local plan.

Retryable conditions: unsupported evaluator capability, missing plan fields, inconsistent grade requirements, or stale plan revision.

Ordinary outcomes: a plan may remain incomplete and list missing resources without being an error.

Fatal conditions: invalid parent artifact or storage failure.

## Resource tools

### `find_resources`

Planned implementation: `resources.py` plus approved provider adapters.

Purpose: search registered assets first and approved external sources second for the resource roles in an evaluation plan.

Input: plan ID, resource roles, scientific scope, schema needs, expected-answer needs, independence constraints, license or access constraints, and result limit.

Successful data: ranked registered and external candidates with provenance, version, scope, access, license, expected-answer capability, and stated uncertainties.

Side effects: records search provenance in the run but does not download or register candidates.

Ordinary outcomes: an empty candidate list or no target-grade candidate.

Fatal conditions: invalid plan or unavailable required search infrastructure. One provider failure is recorded without hiding results from other providers.

### `materialize_resources`

Planned implementation: `resources.py` and `storage.py`

Purpose: retrieve or open selected candidates, calculate immutable digests, inspect required metadata, store allowed payloads, and create resource records.

Input: plan ID, selected candidate references, intended roles, expected versions, and access authorization already available to the runtime.

Successful data: resource IDs, validation status, immutable versions and digests, managed locations, restrictions, and scientific-fit findings.

Side effects: may write content-addressed payloads to managed storage, add provisional or validated resource metadata, and update the run's resource lock.

Retryable conditions: changed version, digest mismatch, schema mismatch, incomplete metadata, or an alternative candidate required.

Fatal conditions: unauthorized access, prohibited license or retention, corrupted payload, unsafe path, or storage failure.

## Evaluation-capability tools

### `build_evaluation_bundle`

Planned implementation: `evaluation.py` and `storage.py`

Purpose: reproducibly transform locked resources and a plan into isolated evaluator inputs, expected answers or oracle instructions, tolerances, metrics, and case metadata.

Input: plan ID, resource lock, deterministic transformation recipe, split rules, exclusions, and case budget.

Successful data: run-local bundle candidate ID, case counts, digests, transformation provenance, and detected construction warnings.

Side effects: writes run-local cases and expected-answer payloads to managed storage. It does not register the bundle as reusable.

Retryable conditions: invalid mapping, empty cases, duplicate or leaking cases, missing expected answers, or resource incompatibility.

Fatal conditions: unsafe transformation, unauthorized payload use, or storage failure.

### `validate_evaluation_bundle`

Planned implementation: `evaluation.py`

Purpose: perform objective checks on a candidate bundle and calculate its maximum supported grade and validated scope.

Input: candidate bundle ID and plan ID.

Successful data: validation status, objective check results, supported grade ceiling, coverage, exclusions, leakage findings, determinism findings, and repairs needed.

Side effects: writes a validation record.

Ordinary outcomes: an inadequate bundle or grade ceiling below the plan target.

Fatal conditions: missing or corrupted bundle artifacts.

### `register_evaluator`

Planned implementation: `evaluation.py` and `storage.py`

Purpose: register a validated reusable bundle and its evaluator capability for compatible claim types.

Input: validated bundle ID, evaluator implementation entry point and version, supported type IDs, grade ceiling, input and output contracts, environment lock, scope, exclusions, and limitations.

Successful data: evaluator ID and version, bundle ID and version, registration status, and registry revisions.

Side effects: writes reusable evaluator and bundle metadata. New code or payloads must already exist in approved locations; the verifier agent cannot insert arbitrary implementation code through this tool.

Retryable conditions: incomplete registration, duplicate capability, stale registry, or unmet validation prerequisite.

Fatal conditions: registry corruption, unsafe implementation reference, or storage failure.

## Audit tool

### `commit_plan_audit`

Planned implementation: `audit.py` and `storage.py`

Purpose: combine mandatory Python checks with a bounded semantic assessment and persist whether the exact plan and asset versions may execute.

Input: plan ID and revision; evaluator, bundle, and resource versions; objective check references; semantic findings for scope, fairness, and limitations; AI-involvement assessment; and proposed audit status.

Successful data: audit ID, `pass` or `fail`, enforced grade ceiling, required repairs, and unresolved risks.

Side effects: writes the plan audit.

Retryable conditions: stale assets, missing required checks, unsupported proposed grade, or internally inconsistent findings.

Ordinary outcomes: failed audit.

Fatal conditions: corrupted prerequisites or storage failure.

## Execution and result tools

### `execute_evaluation_plan`

Planned implementation: `execution.py`

Purpose: execute the exact audited evaluator against the locked bundle and submitted skill in an isolated environment.

Input: plan ID, passing audit ID, evaluator and bundle versions, execution budget, and approved environment reference.

Successful data: execution ID, completion status, raw-output references, metrics, case-level outcomes, coverage, duration, environment digest, and operational errors.

Side effects: writes execution artifacts and referenced raw outputs.

Retryable conditions: transient execution failure within runner limits.

Ordinary outcomes: completed scientific pass or fail data, evaluator-reported invalid cases, or exhausted operational failure. None automatically determines an evidence grade.

Fatal conditions: stale audit, version mismatch, unsafe environment, budget violation, or corrupted evaluator assets.

### `commit_claim_result`

Planned implementation: `reporting.py` and `storage.py`

Purpose: enforce the evidence-grade ceiling and persist the scientific result for one claim.

Input: claim, route, and plan references; audit, execution, evaluator, bundle, and resource references when produced by the valid path; proposed status and grade; coverage; AI involvement; downgrade reasons; warnings; and report notes. A pre-execution grade-U path marks stages that were not scientifically applicable instead of inventing their references.

Successful data: immutable claim-result ID, accepted status, accepted grade, and completeness findings.

Side effects: writes the claim-result artifact.

Retryable conditions: proposed grade above the evidence ceiling, unsupported status, missing provenance, or incomplete coverage disclosure.

Ordinary outcomes: pass, fail, or inconclusive at any supported grade, including U when no scientific conclusion is permitted.

Fatal conditions: contradictory or corrupted evidence references or storage failure.

### `write_report_card`

Planned implementation: `reporting.py`

Purpose: account for every accepted claim and write the final machine-readable and human-readable run report.

Input: run ID and accepted claim-result IDs, plus unresolved operational outcomes for claims without executable results.

Successful data: report-card JSON and Markdown paths, returned artifact list, retained reusable asset list, warnings, and completion status.

Side effects: writes `report-card.json`, renders `report-card.md`, and marks the run complete.

Retryable conditions: missing claim, inconsistent result reference, incomplete warning disclosure, or stale run state.

Fatal conditions: corrupted run state or storage failure.

## Excluded capabilities

The verifier agent is never given arbitrary shell execution, arbitrary Python execution, direct registry editing, unrestricted network access, secret retrieval, evaluator-code injection, or permission to bypass audits and grade ceilings.
