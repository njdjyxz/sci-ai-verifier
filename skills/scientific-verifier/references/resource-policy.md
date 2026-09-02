# Resource Storage and Reuse Policy

This policy separates per-run material from reusable scientific assets. It answers what to keep, what to return, and what to discard after verifying a submitted skill.

## Storage layers

### Shared registry

The Git repository stores small, reviewable metadata:

- `registry/claim_types.json`
- `registry/evaluators.json`
- `registry/resources/`
- `registry/bundles/`

Registry records describe reusable assets and point to immutable payloads or retrieval locations. Large datasets, generated cases, model weights, and raw evaluator output do not belong directly in Git.

### Managed store

`.verifier/store/` or a future company-approved object store holds immutable large payloads addressed by digest. Examples include downloaded datasets, generated case tables, expected-answer files, and large raw evaluator outputs.

One payload may be referenced by many resources, bundles, evaluators, and runs. Duplicate content is stored once.

### Run workspace

`.verifier/runs/<run-id>/` isolates one submitted skill's manifests, plans, locks, audits, results, report card, and necessary execution logs. A run may reference shared assets but does not copy them unless isolation or the execution environment requires it.

### Cache and scratch space

`.verifier/cache/` and run-local temporary directories hold recoverable downloads, indexes, decompressed files, conversions, and intermediate execution files. Their contents are never authoritative evidence.

## Resource record

Every reusable scientific resource records:

- Stable resource ID.
- Name and scientific role.
- Source URI, provider, citation, or acquisition method.
- Version, release date when known, and retrieval date.
- Immutable payload digest and size.
- Scientific domain, scope, units, schema, and relevant columns.
- Expected-answer or oracle capability.
- Independence relationship to the submitted skill and evaluator.
- License, attribution, redistribution, access, and retention restrictions.
- Managed payload or reproducible retrieval location.
- Validation status, limitations, and provenance.

A URL without a version or digest is not sufficient provenance for a published result.

## Search and reuse order

For each required resource role:

1. Search registered bundles that already satisfy the claim type and planned grade.
2. Search registered resources by scientific role, scope, schema, and grade suitability.
3. Reuse an exact registered version when compatible.
4. Search approved external sources only when no registered asset is adequate.
5. Materialize and validate only selected candidates.
6. Register reusable metadata after license, provenance, integrity, and scientific-fit checks pass.

Do not reuse a resource merely because its name is similar. Confirm scope, fields, units, expected-answer semantics, independence, license, and version compatibility.

## Promotion states

- `candidate`: discovered but not yet materialized or validated.
- `provisional`: integrity and minimum metadata are recorded; usable for continued construction but not sufficient by itself for a published scientific verdict.
- `validated`: approved for stated roles, scope, versions, and evidence-grade ceiling.
- `retired`: retained for reproducibility of older results but unavailable for new plans.

Automatic promotion is allowed only when the required deterministic checks and plan audit pass. Any semantic uncertainty is recorded as a limitation and may reduce the grade ceiling.

## Keep after a run

Keep the minimum information required to reproduce and audit a returned scientific conclusion:

- Source digest and claim manifest.
- Claim routing and index revision.
- Final evaluation plans and resource lock.
- Plan audits.
- Claim results, metrics, coverage, and decision outputs.
- Report-card JSON and Markdown.
- Tool-call events and operational errors needed for audit.
- Exact evaluator, bundle, resource, implementation, and environment versions.
- Reusable validated or provisional registry metadata.
- Managed payloads required by published results when retention and license permit.

Retention duration and storage location follow company policy. The verifier records the applied policy rather than inventing a duration.

## Return to the requester

Return:

- Human-readable report card.
- Machine-readable report-card JSON.
- Claim manifest.
- Claim-level result artifacts.
- A reproducibility manifest containing evaluator, bundle, resource, environment, and digest references.

Return full datasets, expected-answer files, raw outputs, or evaluator code only when license, access policy, size, and user authorization permit. Otherwise return identifiers and retrieval or audit references.

## Discard after completion

Discard material that is reproducible, redundant, unsafe, or unrelated to the final evidence:

- Temporary downloads already present in the managed store.
- Decompressed or converted working copies.
- Duplicate payloads.
- Failed verifier-agent drafts and superseded retry payloads, except structured error events needed for audit.
- Temporary evaluator inputs and outputs not referenced by a result.
- Search-result pages and unused candidate resources.
- Build artifacts, process logs, and caches not needed for reproducibility.
- Secrets, API keys, tokens, credentials, and signed temporary URLs.

Do not discard an artifact referenced by a published result until retention policy permits or the result is withdrawn.

## What never enters shared project code

Do not store per-skill claim manifests, plans, results, reports, downloaded datasets, or execution logs under `src/`, `skills/`, or evaluator implementation directories.

Only reusable definitions and implementation code enter the shared project. Run artifacts remain isolated under `.verifier/` or company-managed storage.

## Failure and cleanup

A failed or interrupted run still records its termination reason and any completed claim results. Uncommitted scratch data may be removed. Newly registered provisional assets remain only when their provenance and integrity records are complete; otherwise remove them from the registry and leave the immutable payload eligible for ordinary cache cleanup.
