# Python Tool Contracts

This file names the complete intended Python tool surface for the verifier. No active Python implementation exists in Stage 1. Later stages may implement these tools without changing their reviewed purpose; interface changes require a documentation update first.

## Planned runtime files

| Planned file | Responsibility |
|---|---|
| `src/sci_ai_verifier/agent.py` | Start the bounded verifier-agent session, assemble source-labeled context with explicit trust classes, reconstruct committed workflow state, declare the state-eligible tools, reserve finalization capacity, maintain messages, enforce step, retry, illegal-transition, cost, and execution limits, handle agent-side termination, and detect completion. Implements `runtime-contract.md`. |
| `src/sci_ai_verifier/tools.py` | Publish approved tool definitions, reject illegal state transitions, dispatch eligible tool calls, and convert expected exceptions into structured results. |
| `src/sci_ai_verifier/storage.py` | Perform atomic artifact writes, content hashing, run-workspace management, managed-store access, registry locking, operational-outcome persistence, and runner-owned finalization. Reads the reviewed registry under `registry/` and writes only to the runtime registry under `.verifier/registry/`; it has no write path to the repository. |
| `src/sci_ai_verifier/ingest.py` | Snapshot submitted skills under the reviewed exclusion policy and load their top-level instructions as untrusted UTF-8 data. |
| `src/sci_ai_verifier/claims.py` | Validate and commit claim manifests and assign claim IDs. |
| `src/sci_ai_verifier/routing.py` | Manage claim types and perform exact evaluator-registry lookup. |
| `src/sci_ai_verifier/planning.py` | Validate and persist registered and target evaluation plans. |
| `src/sci_ai_verifier/resources.py` | Search, inspect, materialize, validate, register, and lock scientific resources. |
| `src/sci_ai_verifier/evaluation.py` | Resolve approved generic harnesses, build and validate cases and bundles, and register reusable evaluator configurations without accepting arbitrary code. |
| `src/sci_ai_verifier/audit.py` | Validate plan prerequisites, persist bounded plan audits, and atomically promote passing provisional evaluator and bundle versions. |
| `src/sci_ai_verifier/execution.py` | Resolve approved subject runners, run the submitted skill under the audited subject-runner configuration for the audited trial count, apply the audited aggregation rule, run audited evaluators over the aggregated outcomes, and capture reproducible per-trial outputs, variance, and metrics. |
| `src/sci_ai_verifier/reporting.py` | Validate claim results, write machine-readable and human-readable report cards, and include the storage finalizer's recorded summary. |

These are planned boundaries, not permission for the verifier agent to call arbitrary functions inside the files. The runner declares the subset of approved tools allowed by the current state in `workflow.md`, and revalidates state and prerequisites when dispatching every request. Tool visibility alone is not authorization: the published tool surface may be wider than the legal set, and the dispatcher, not the published surface, is what enforces the workflow. `runtime-contract.md` covers the host-side reasons for keeping the published surface stable.

## Common result and transition protocol

Every tool returns exactly one status.

Successful operation or ordinary workflow outcome:

```json
{
  "status": "ok",
  "data": {
    "outcome": "tool_specific_mutually_exclusive_code",
    "committed_state": "authoritative_state_after_operation",
    "next_permitted_state": "authoritative_next_state",
    "next_legal_tools": []
  }
}
```

Correctable request or stale state:

```json
{
  "status": "retryable",
  "error": {
    "code": "stable_machine_readable_code",
    "message": "Short explanation",
    "details": {},
    "repair_fields": [],
    "refresh_required": false,
    "retries_remaining": 1,
    "illegal_transitions_remaining": 3,
    "committed_state": "unchanged_state",
    "next_legal_tools": []
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
    "details": {},
    "scope": "claim_or_run",
    "operational_outcome_id": "python_assigned_id_or_null_only_for_persistence_failure",
    "committed_state": "terminal_state",
    "next_legal_tools": []
  }
}
```

`data` appears only with `ok`. `error` appears only with `retryable` or `fatal`. Every `ok` tool defines mutually exclusive outcome codes. When several findings apply, Python returns the outcome with the earliest repair precedence defined by that tool; the agent does not choose among overlapping transitions.

Empty searches, unsupported grades, inadequate bundles, failed audits, scientific failures, and missing evaluators are `ok` data because the verifier agent must route from them. A retryable result always states exactly what may be repaired or refreshed and how many attempts remain.

Retryable results come in two kinds, counted against two independent budgets:

- **Repair retries** decrement `retries_remaining`. The named tool was legal and ran far enough to reject the request's content: a missing field, a stale revision, a malformed constraint. Only the tool that returned the result may be retried against it.
- **Illegal transitions** decrement `illegal_transitions_remaining`. Nothing ran. The request named an undeclared tool, named a tool illegal in the committed state, or was a second workflow request in the same assistant turn. `repair_fields` is empty because there is nothing to repair; the correct response is to read `next_legal_tools` and issue a different request.

Keeping the budgets separate matters because the caller is a language model and misrouting is its characteristic failure, not a sign that the eventual correct call is also going to fail. A run that spent its repair budget on two wrong tool names would terminate claims that were never actually in trouble. Both budgets are bounded, so neither kind of mistake can loop; exhausting the first records `retry_limit` and exhausting the second records `illegal_transition_limit`, both claim-scoped where the state is claim-scoped.

Before returning `fatal`, the runner records a claim- or run-scoped operational-outcome artifact and includes its ID. Claim-scoped fatal results leave independent claims eligible to continue. Run-scoped fatal results stop scientific work and leave reporting as the only legal operation when reporting and reserved finalization capacity remain available. If the failure itself prevents all run-workspace persistence, the ID is null, `code` is `operational_outcome_persistence_failed`, the returned fatal response is the only available termination evidence, and reporting cannot be claimed complete.

The runner handles limits outside individual tool semantics. When a retry, step, cost, wall-clock, or execution limit is exhausted, it records operational outcomes for every affected unfinished claim. It reserves enough capacity to write the report and finalize the run. If the agent session has stopped because of a run-wide limit, cancellation, or expired resumption window, Python may invoke the deterministic `write_report_card` operation directly with committed result and outcome IDs; that invocation is recorded exactly like a tool call. Explicit cancellation uses this terminal path. An unexpected interruption remains resumable until the configured resumption window expires.

## Load and profile tools

### `load_submitted_skill`

Planned implementation: `ingest.py`

Purpose: create an immutable content-addressed snapshot of one submitted skill, then return its top-level instructions without interpreting or executing them.

Input: a path to a UTF-8 file or directory containing a top-level `SKILL.md`, plus the runner-selected snapshot-policy version and configured file-count and size limits.

Successful outcome: `source_snapshotted`.

Successful data: source-snapshot ID and digest, resolved original path as provenance, normalized included-file manifest, excluded paths with reason codes, snapshot-policy version, total size, top-level `SKILL.md` digest, and exact top-level content.

Side effects: writes the run-local source-snapshot manifest and an immutable managed-store payload. On resumption before claim commitment, the runner re-supplies the verified snapshot content instead of reading the live source.

Fatal conditions: missing, unreadable, empty, oversized, invalidly encoded, or unsafe source; a required file excluded by policy; a symlink escaping the submitted root; snapshot integrity or storage failure. These are run-scoped because no trustworthy source parent exists.

### `read_snapshot_file`

Planned implementation: `ingest.py` and `storage.py`

Purpose: return the exact verified content of one file already inside the committed source snapshot, so claims can be extracted from the parts of a submitted skill that are not its top-level `SKILL.md`.

Input: source-snapshot ID, source-snapshot digest, and one snapshot-relative path taken from the returned manifest. An optional byte range may be supplied for a large file.

Successful outcome: `snapshot_file_returned`.

Successful data: snapshot-relative path, file digest, encoding, size, returned byte range when partial, and exact content as untrusted data.

Side effects: none. The read is served from the immutable managed-store payload, never from the live source path. The runner records which manifest entries have been read so a resumed session can re-supply them without a second request.

Retryable conditions: a path that is not in the committed manifest, a path excluded by snapshot policy, an undecodable or non-text payload, or a byte range outside the file. A path that merely looks plausible is not in the manifest; there is no globbing, no directory listing beyond the manifest already returned, and no traversal.

Fatal conditions: manifest or payload digest mismatch, which is snapshot corruption rather than a missing file, and is run-scoped for the same reason `load_submitted_skill` failures are.

Returned content is untrusted data under the same rules as the top-level content. This tool reads; it never executes, renders, or resolves anything the file references.

### `commit_claim_manifest`

Planned implementation: `claims.py` and `storage.py`

Purpose: validate the verifier agent's candidate atomic claims, assign stable IDs, and persist the accepted manifest.

Input: source-snapshot ID, source-snapshot digest, and claims containing statement, scope, expected behavior, the snapshot-relative source path, an exact source quote from that file, and report note.

Successful outcomes: `claims_committed` or `no_scientific_claims`.

Successful data: manifest ID and accepted claims with Python-assigned claim IDs. The empty outcome contains an explicit zero count and permits reporting without routing.

Side effects: writes the run's claim manifest.

Retryable conditions: missing fields, non-atomic or duplicate submissions identified structurally, a source path not present in the committed manifest, or a source quote not present in the recorded content of the file the claim names. Quote validation is per-claim against the named file's digest, so a claim quoting a bundled reference document is validated exactly as strictly as one quoting the top-level `SKILL.md`.

Fatal conditions: source-snapshot ID or digest mismatch, storage failure, or corrupted run state.

## Routing tools

### `list_claim_types`

Planned implementation: `routing.py`

Purpose: return the complete controlled claim-type index for semantic comparison.

Input: empty object.

Successful outcome: `claim_type_index_loaded`.

Successful data: index revision, digest, and claim types with IDs, definitions, inputs, outputs, boundaries, `status`, `origin`, and provenance. `origin` is `reviewed` for entries committed to `registry/claim_types.json` by a human, or `runtime` for provisional entries written by an earlier run into `.verifier/registry/`. The returned index is the merge of both, and the revision covers the merge.

Side effects: none. A missing index on either side is treated as empty; an index missing on both sides is returned as revision zero with an empty list.

Fatal conditions: malformed or unsupported index schema.

### `commit_claim_type_assignments`

Planned implementation: `routing.py` and `storage.py`

Purpose: validate exactly one type assignment per accepted claim and persist necessary provisional types.

Input: manifest ID, observed index revision, and assignments. Each assignment supplies either one exact existing type ID or a complete proposed name, definition, inputs, outputs, and boundaries.

Successful outcome: `claim_routes_committed`.

Successful data: updated index revision and one accepted claim route per claim.

Side effects: may add content-addressed provisional types to the runtime index under `.verifier/registry/`, and writes run routing state. It never writes to `registry/` in the repository; promoting a provisional type to `reviewed` is a human action outside any run, described in `resource-policy.md`.

Retryable conditions: stale revision, unknown existing ID, incomplete proposal, missing claim, or duplicate assignment.

Fatal conditions: registry corruption or storage failure.

### `find_registered_evaluators`

Planned implementation: `routing.py`

Purpose: perform an exact evaluator-registry lookup for every accepted claim route and return approved generic harnesses that can implement unsupported target plans.

Input: accepted claim routes, scientific scope, and the current intended grade for each claim.

Successful outcome: `capabilities_resolved`.

Successful data: evaluator-registry revision and digest plus, for every claim, one mutually exclusive `capability_outcome`:

- `registered_evaluator_available`: one or more validated evaluator and bundle versions cover the current scope and intended grade.
- `generic_harness_available`: no validated evaluator covers the current need, but one or more approved generic harness IDs and versions can implement the target plan.
- `implementation_required`: neither a validated evaluator nor an approved harness can implement the claim. Python creates a claim-scoped operational outcome with this code.

The result also returns compatible lower-grade evaluator versions as fallback candidates, approved harness input/output/configuration contracts, supported grade ceilings, scope, and limitations. Provisional or retired evaluators are never returned as executable matches.

It additionally returns the **approved subject-runner catalog**: for each entry, its ID and version, the interface it drives, the subject model identities it may be configured with, the generation settings it accepts, its supported trial counts and aggregation rules, its isolation guarantees, and its status. A plan may name only a subject runner returned here. The catalog is returned with capability selection rather than through a separate tool because the choice of subject runner and the choice of evaluator constrain each other: an evaluator's input contract determines what the subject's output must look like.

Side effects: writes an append-only run-local capability-selection revision to `routing.json` but makes no registry changes. For each `implementation_required` claim, the runner also writes the claim-scoped operational-outcome artifact described by the common transition protocol.

Retryable conditions: missing or unknown route IDs.

Fatal conditions: malformed evaluator or harness registry. Python records an operational outcome for every affected unresolved claim.

## Planning tool

### `commit_evaluation_plan`

Planned implementation: `planning.py` and `storage.py`

Purpose: validate and persist one registered or target plan for a claim.

Input: claim and route IDs; immutable source-snapshot ID and digest; plan kind; requested, target, and planned grade; evaluator or target-evaluator specification; exact approved generic-harness ID and version for a target plan; required resource roles; oracle or evidence design; case method; metrics; tolerances; deterministic invalid-case, coverage, scoring, and verdict rules for grades A through C; documentary rubric and assessor boundary for grade D; the subject-runner configuration; execution requirements; budget; AI involvement; limitations; and report notes. A registered plan may reference either a validated evaluator returned by capability selection or the exact provisional evaluator just returned by `register_evaluator`; a provisional reference is legal only for the audit state.

The subject-runner configuration names one approved subject-runner ID and version from the catalog returned by capability selection, the exact subject model identity or deterministic entry point it drives, the generation settings that affect output, the trial count `n`, and the deterministic aggregation rule reducing a case's `n` trials to one per-case outcome. Python rejects a plan whose subject runner is absent, is not in the catalog, is configured outside the catalog entry's declared bounds, or whose aggregation rule is not total over `n` trials. An aggregation rule that is chosen or adjusted after execution is not a rule; that is the failure this field exists to prevent.

Successful outcomes:

- `resource_resolution_required`
- `registered_plan_audit_ready`
- `target_bundle_required`
- `capability_reselection_required`: this revision lowered the planned grade or materially changed scope, so the previously selected capability may no longer be the best fit. Every downgrade path re-enters capability selection through this outcome, which is what keeps the rule about preferring an existing lower-grade evaluator over rebuilding from being advice the agent can skip.

Successful data: plan ID, revision, current grade ceiling, unresolved requirements, preserved lower-grade evaluator candidates, accepted subject-runner configuration, next permitted state, and legal next tools.

Side effects: writes or revises the claim's run-local plan.

Retryable conditions: unsupported evaluator capability, missing plan fields, inconsistent grade requirements, or stale plan revision.

Ordinary outcomes: a plan may remain incomplete and list missing resources without being an error. A target plan that does not reference an approved harness is rejected rather than accepted as an unexecutable plan.

Fatal conditions: invalid parent artifact or storage failure.

## Resource tools

### `find_resources`

Planned implementation: `resources.py` plus approved provider adapters.

Purpose: search registered assets first and approved external sources second for the resource roles in an evaluation plan.

Input: plan ID, resource roles, scientific scope, schema needs, expected-answer needs, independence constraints, license or access constraints, and result limit.

Successful outcomes, calculated across every required resource role:

- `planned_grade_candidates_complete`: every role has at least one candidate suitable for the planned grade.
- `lower_grade_only`: the returned candidates can jointly support only the stated lower grade.
- `resource_unavailable`: scientifically suitable evidence exists, but access, license, retention, or authorization constraints prevent any usable candidate set. Python records a claim-scoped operational outcome.
- `no_acceptable_evidence`: the completed available search found no scientifically suitable candidate set supporting grades A through D; this is not used merely because suitable evidence was inaccessible.

Successful data: search-result ID and revision, candidates grouped by resource role with provenance, version, scope, access, license, expected-answer capability, uncertainties, provider failures, and the strongest grade supported jointly across all roles. Partial per-role success never produces `planned_grade_candidates_complete`.

Side effects: records search provenance in the run but does not download or register candidates. On `resource_unavailable`, the runner also writes a claim-scoped operational-outcome artifact.

Ordinary outcomes: an empty candidate list or no target-grade candidate.

Retryable conditions: caller-supplied plan ID or revision that does not match the committed plan, malformed role constraints, or an invalid result limit.

Fatal conditions: corrupted committed plan artifact or unavailable required search infrastructure. One provider failure is recorded without hiding results from other providers.

### `materialize_resources`

Planned implementation: `resources.py` and `storage.py`

Purpose: retrieve or open selected candidates, calculate immutable digests, inspect required metadata, store allowed payloads, and create resource records.

Input: plan ID, search-result ID and revision, selected candidate references, intended roles, expected versions, and access authorization already available to the runtime.

Successful outcomes, in repair precedence order:

Precedence is evaluated only over roles that are still unsatisfied. Outcomes 1 through 5 all require at least one required role to remain open; if every required role ends the call locked, the outcome is `all_roles_locked` regardless of what happened to individual candidates along the way. Without this guard, rejecting one redundant candidate in an otherwise complete call would return `candidate_rejected` and send the agent to look for a replacement that nothing needs.

1. `candidate_rejected`: a selected candidate is inaccessible, license-incompatible, changed, corrupted, schema-incompatible, or scientifically unsuitable; a role it was selected for is still open; and another untried candidate may be selected.
2. `additional_candidate_required`: one or more roles remain unsatisfied and the search result still contains an untried candidate.
3. `resource_unavailable`: scientifically suitable candidates are exhausted because of access, license, retention, authorization, changed-version, or payload-availability failures. Python records a claim-scoped operational outcome.
4. `no_acceptable_evidence`: all accessible candidates are exhausted for scientific-fit reasons and support no grade A through D.
5. `lower_grade_required`: all roles can be locked, but the materialized resources jointly support only the stated lower grade.
6. `all_roles_locked`: every required role is satisfied at the planned grade. Candidates rejected during the call are reported as rejection records on this outcome and never enter the lock.

Successful data: resource IDs, per-role validation status, immutable versions and digests, managed locations, restrictions, scientific-fit findings, rejection reasons, and strongest joint grade.

Side effects: may write content-addressed payloads to managed storage, add provisional or validated resource metadata, and update the run's resource lock for successfully accepted roles. `candidate_rejected` never adds that candidate to the resource lock or reusable registry; an unreferenced download remains only temporary cleanup material. On `resource_unavailable`, the runner also writes a claim-scoped operational-outcome artifact.

Retryable conditions: malformed candidate references, stale plan revision, or a request that omits required role assignments. Candidate-specific scientific, access, license, schema, version, or payload problems use the ordinary outcomes above so the agent can select an alternative.

Fatal conditions: an attempted path escape or other security violation, corrupted registry state, or storage failure that prevents safe continuation. Ordinary authorization denial, prohibited candidate license, and corrupted candidate payload are candidate rejections rather than claim-fatal errors.

## Evaluation-capability tools

### `build_evaluation_bundle`

Planned implementation: `evaluation.py` and `storage.py`

Purpose: reproducibly transform locked resources and a plan into isolated evaluator inputs, expected answers or oracle instructions, tolerances, metrics, and case metadata.

Input: plan ID, exact approved generic-harness ID and version, resource lock, deterministic transformation recipe, bounded harness configuration, split rules, exclusions, and case budget.

Successful outcomes:

- `bundle_candidate_built`: the locked resources and requested transformation produced a candidate.
- `resource_change_required`: the committed resource lock cannot satisfy the approved harness or plan; changing only the build request cannot solve the problem.

Successful data: run-local bundle candidate ID, harness identity, case counts, digests, transformation provenance, and detected construction warnings.

Side effects: writes run-local cases and expected-answer payloads to managed storage. It does not register the bundle as reusable.

Retryable conditions: malformed transformation requests, caller-supplied resource references that do not match the committed lock, or repairable invalid mappings, empty cases, duplicates, leakage, or missing expected answers. Scientific incompatibility of the committed resources uses `resource_change_required`.

Fatal conditions: unsafe transformation, unauthorized payload use, or storage failure.

### `validate_evaluation_bundle`

Planned implementation: `evaluation.py`

Purpose: perform objective checks on a candidate bundle and calculate its maximum supported grade and validated scope.

Input: candidate bundle ID and plan ID.

Successful outcomes, in repair precedence order:

1. `resource_change_required` when resource changes are necessary; rebuilding against the current lock cannot solve the problem.
2. `bundle_rebuild_required` when the current resources are usable but construction defects are repairable.
3. `no_supported_grade` when no repair using the approved inputs can support grades A through D.
4. `lower_grade_required` when the bundle is otherwise valid but has a lower grade ceiling than planned.
5. `bundle_adequate` when the exact bundle supports the planned grade and scope.

Python returns exactly one outcome even when multiple findings exist. Successful data includes objective check results, supported grade ceiling, coverage, exclusions, leakage and determinism findings, repairs needed, next permitted state, and legal next tools.

Side effects: writes a validation record.

Ordinary outcomes: an inadequate bundle or grade ceiling below the plan target.

Fatal conditions: missing or corrupted bundle artifacts.

### `register_evaluator`

Planned implementation: `evaluation.py` and `storage.py`

Purpose: register a validated reusable bundle and a bounded configuration of an approved generic harness as a provisional reusable evaluator capability.

Input: validated bundle ID, approved generic-harness ID and version, bounded configuration and digest, supported type IDs, grade ceiling, input and output contracts, environment lock, scope, exclusions, and limitations.

Successful outcomes:

- `provisional_evaluator_registered`: the bundle and configuration were registered as a new provisional capability.
- `capability_reselection_required`: an equivalent capability already exists, or the registry advanced while this bundle was being built. No registration occurs. This is an ordinary workflow outcome, not a caller error, because the correct response is a different transition rather than a corrected request: return to `find_registered_evaluators` and prefer the existing validated capability when one now fits.

Successful data: evaluator ID and version, bundle ID and version, `registration_status: provisional`, harness identity and configuration digest, and registry revisions. On `capability_reselection_required`, the matching existing capability's ID and version instead.

Side effects: writes provisional reusable evaluator and bundle metadata to the runtime registry under `.verifier/registry/`, never to `registry/` in the repository. Python resolves the implementation entry point from the approved harness catalog. The verifier agent cannot provide, generate, or inject implementation code.

Retryable conditions: incomplete registration or unmet validation prerequisite. Duplicate capability and stale registry are the `capability_reselection_required` outcome above rather than retries, because retrying the same registration cannot resolve either.

Fatal conditions: registry corruption, unsafe implementation reference, or storage failure.

## Audit tool

### `commit_plan_audit`

Planned implementation: `audit.py` and `storage.py`

Purpose: combine mandatory Python checks with a bounded semantic assessment, persist whether the exact plan and asset versions may execute, and atomically promote passing provisional evaluator and bundle versions.

Input: source-snapshot ID and digest; plan ID and revision; evaluator status and version; generic-harness and configuration versions; bundle, resource, subject-runner, and environment versions; objective check references; semantic findings for scope, fairness, and limitations; AI-involvement assessment; and the agent's proposed audit status.

The proposed status is advisory and is recorded, not obeyed. Python decides from its own checks and returns that decision as the outcome code; the artifact stores the proposal beside the decision so a reviewer can see where the agent's semantic reading and the objective checks diverged. Divergence is a finding to report, not a condition to repair, and Python never returns `retryable` merely because the proposal disagreed with the result.

Subject-runner checks are mandatory prerequisites, not semantic findings: a plan cannot pass audit if its subject-runner configuration is incomplete, names an entry outside the approved catalog, is configured beyond that entry's declared bounds, has a trial count or aggregation rule inconsistent with the claim and the planned grade, or fails the isolation requirement that the subject never sees expected answers, oracle instructions, or split membership.

Successful outcomes, in repair precedence order:

1. `audit_passed`: all prerequisites pass; Python atomically promotes the exact provisional evaluator and bundle versions to `validated` before returning.
2. `resource_change_required`: resources must change and all dependent bundle, evaluator, plan, and audit versions become stale.
3. `bundle_rebuild_required`: the resource lock remains usable but the bundle and dependent evaluator, plan, and audit must change.
4. `plan_revision_required`: only the plan and its audit must change.
5. `no_supported_grade`: no permissible repair supports grades A through D.
6. `lower_grade_required`: the exact assets are otherwise auditable only at the returned lower ceiling.

Python returns exactly one outcome, and that outcome is the decision: `audit_passed` is the passing audit and every other outcome is a failing one. Successful data includes audit ID, the derived `audit_status` of `pass` or `fail` for the artifact, the agent's recorded proposed status and whether it agreed, enforced grade ceiling, required repairs, unresolved risks, promotion records, next permitted state, and legal next tools.

Side effects: writes the plan audit. On `audit_passed`, atomically promotes the exact provisional evaluator and bundle versions. If either promotion fails, the audit is not committed as passing and the tool returns `fatal`.

Retryable conditions: caller-supplied references that do not match still-valid committed assets, missing required checks, unsupported proposed grade, or internally inconsistent findings. A trustworthy committed asset that actually requires replacement uses the applicable successful repair outcome rather than `retryable`.

Ordinary outcomes: failed audit.

Fatal conditions: corrupted prerequisites or storage failure.

## Execution and result tools

### `execute_evaluation_plan`

Planned implementation: `execution.py`

Purpose: run the immutable submitted-skill snapshot under the audited subject runner, aggregate its trials by the audited rule, and score the result with the exact audited evaluator, all in an isolated environment.

Input: source-snapshot ID and digest; plan ID; passing audit ID; exact validated evaluator, generic-harness configuration, bundle, resource, subject-runner, and environment versions; and execution budget covered by the audit.

Execution proceeds in two stages, both owned by Python. First the audited subject runner produces `n` trial outputs for each bundle case from the snapshot and the case input alone, with expected answers, oracle instructions, and split membership withheld. Then the audited aggregation rule reduces each case's trials to one per-case outcome and the evaluator scores those outcomes. Neither stage may be reconfigured at execution time; a request naming a subject-runner version other than the audited one is a caller error, not a variation.

Successful outcomes:

- `completed_deterministic_decision`: grades A through C; returns Python's authoritative `decision_status` from the audited invalid-case, coverage, tolerance, metric, and decision rules.
- `documentary_judgment_ready`: grade D; returns only the audited rubric, bounded evidence excerpts and citations, assessor boundary, and judgment packet the verifier agent or identified human may assess.
- `reaudit_required`: a committed asset is no longer eligible under the existing audit; Python invalidates the audit and returns the audit state without executing.
- `operational_failure`: execution retries are exhausted; Python records a claim-scoped operational outcome and returns its ID without a scientific status.

Successful data, when applicable: execution ID, authoritative decision status or judgment packet, decision-rule identity, raw-output references, metrics, case-level outcomes, invalid-case disposition, coverage disposition, duration, source-snapshot digest, subject-runner identity with its subject model and generation settings, trial count, aggregation-rule identity, per-trial output references, per-case trial agreement, environment digest, and operational errors.

Per-trial outputs and per-case agreement are returned and retained rather than collapsed into the aggregate. A claim that satisfied its oracle on every trial and a claim that satisfied it on a bare majority are different findings about the submitted skill, and only the recorded trial detail distinguishes them. Agreement statistics are reported in the claim result and bound the grade under `evidence-rubric.md`; they are not themselves a verdict.

Side effects: writes execution artifacts and referenced raw outputs only when execution begins. `reaudit_required` writes no execution artifact; `operational_failure` additionally causes the runner to write its operational-outcome artifact.

Retryable conditions: transient execution failure within runner limits or caller-supplied references that do not match the still-valid committed audit. The result identifies the exact committed references and remaining retries.

Ordinary outcomes: deterministic pass, fail, or inconclusive data; an audited documentary judgment packet; evaluator-reported invalid cases resolved by the audited rules; a required re-audit; or exhausted operational failure. None automatically determines an evidence grade.

Fatal conditions: source-snapshot integrity failure, unsafe environment, corrupted evaluator assets, or storage failure. A request budget above the audited allowance is retryable; exhaustion of the run's execution budget produces an operational outcome. Stale but trustworthy assets route to `reaudit_required` rather than fatal termination.

### `commit_claim_result`

Planned implementation: `reporting.py` and `storage.py`

Purpose: enforce result-kind invariants and the evidence-grade ceiling, then persist the scientific result for one claim.

Input uses exactly one form:

- `evaluated_result` for grades A through C: claim, route, plan, source snapshot, audit, execution, evaluator, bundle, resource, and subject-runner references; proposed grade; coverage; trial count, aggregation rule, and observed agreement; AI involvement; downgrade reasons; warnings; and report notes. Status is omitted or must exactly equal Python's authoritative execution status.
- `documentary_result` for grade D: the same applicable references plus the audited judgment packet, citations, rubric findings, assessor identity, the assessor's independence from the session that designed the plan and rubric, proposed status, and explicit AI or human involvement.
- `unverified_result` for grade U: claim, route, plan, source snapshot, attempted-evidence references, missing evidence, searches or checks performed, downgrade reasons, limitations, and explicit `not_applicable` stage markers. Status is omitted or `inconclusive`.

Successful outcome: `claim_result_committed`.

Successful data: immutable claim-result ID, result kind, Python-accepted status, accepted grade, and completeness findings.

Side effects: writes the claim-result artifact.

Retryable conditions: proposed grade above the evidence ceiling, a grade A-through-C status differing from the deterministic execution status, a grade-U status other than `inconclusive`, unsupported documentary judgment, a documentary result whose assessor is the session that designed the plan and rubric, missing provenance, missing subject-runner or trial disclosure on an evaluated result, or incomplete coverage disclosure.

Ordinary outcomes: pass, fail, or inconclusive at grades A through D as permitted by the rubric, and only inconclusive at grade U.

Fatal conditions: contradictory or corrupted evidence references or storage failure.

### `write_report_card`

Planned implementation: `reporting.py`

Purpose: account for every accepted claim and write the final machine-readable and human-readable run report.

Input: run ID, accepted claim-result IDs, Python-assigned operational-outcome IDs for claims without results, and any run-scoped operational-outcome IDs.

Successful outcomes: `run_completed` or `run_completed_with_cleanup_warnings`.

Successful data: report-card JSON and Markdown paths, returned artifact list, retained reusable asset list, warnings, finalization summary, and completion status.

Side effects: verifies complete result/outcome-ID accounting, prepares both report renderings from committed artifacts, runs the runner-owned finalizer without deleting report inputs, records its cleanup summary, atomically writes `report-card.json` and `report-card.md`, and marks the run complete. Cleanup failure is disclosed and never changes a scientific result.

Retryable conditions: missing claim, inconsistent result reference, incomplete warning disclosure, or stale run state.

Fatal conditions: corrupted run state or storage failure.

## Excluded capabilities

The verifier agent is never given arbitrary shell execution, arbitrary Python execution, direct registry editing, direct filesystem access, unrestricted network access, secret retrieval, evaluator-code generation or injection, executable configuration expressions, or permission to bypass audits and grade ceilings. A target evaluator must be a schema-validated declarative configuration of an approved generic harness returned by Python. If no harness fits, the runner records `implementation_required`; the agent does not improvise code.

The same limit applies to the subject side. The agent selects and configures an approved subject runner within its declared bounds; it does not supply a subject-runner implementation, an arbitrary model endpoint, a prompt wrapper of its own, or any instruction that reaches the subject outside the audited configuration. A subject runner that could be steered per case by the agent would let the orchestrator shape the evidence it is about to grade, which is the exact independence the evidence rubric is measuring.

`read_snapshot_file` is not an exception to the filesystem rule. It reads one recorded entry of one committed snapshot by manifest path, and reaches nothing else on disk.
