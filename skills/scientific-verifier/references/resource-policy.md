# Resource Storage and Reuse Policy

This policy separates per-run material from reusable scientific assets. It answers what to keep, what to return, and what to discard after verifying a submitted skill.

## Storage layers

### Shared registry

The registry has two layers with the same record shapes and different authority.

**Reviewed layer, in Git.** Small metadata a human has read and committed:

- `registry/claim_types.json`
- `registry/evaluators.json`
- `registry/resources/`
- `registry/bundles/`

**Runtime layer, not in Git.** The same four shapes under `.verifier/registry/`, written by runs:

- `.verifier/registry/claim_types.json`
- `.verifier/registry/evaluators.json`
- `.verifier/registry/resources/`
- `.verifier/registry/bundles/`

Runs read the merge of both layers and write only to the runtime layer. No tool has a write path into `registry/`. This is what keeps the reviewed layer reviewable: a file that an automated run can rewrite is not a file anyone is reviewing, and two runs on one checkout would otherwise race for the same bytes and produce commits nobody authored. Every returned record carries `origin` of `reviewed` or `runtime` so a lookup can prefer a reviewed definition over a prior run's proposal.

Promotion from runtime to reviewed is a human action taken outside any run: read the provisional record, satisfy yourself that its definition, scope, and provenance are right, and commit it to `registry/`. Nothing in the workflow performs this step or waits for it, and a run never depends on its own proposals being promoted.

`registry/evaluators.json` holds both approved generic-harness definitions and registered bounded evaluator configurations. Approved generic harnesses and approved subject runners exist only in the reviewed layer; a run may configure them but never define one. Registry records describe reusable assets and point to immutable payloads or retrieval locations. Large datasets, generated cases, model weights, and raw evaluator output do not belong directly in Git.

### Managed store

`.verifier/store/` or a future company-approved object store holds immutable payloads addressed by digest. Examples include submitted-skill snapshots, downloaded datasets, generated case tables, expected-answer files, and large raw evaluator outputs.

One payload may be referenced by many resources, bundles, evaluators, and runs. Duplicate content is stored once.

Submitted-skill snapshots use the same content-addressed integrity model. The snapshot policy excludes version-control data, caches, temporary outputs, `.verifier/`, environment directories, links outside the source root, and files matched by the reviewed secret-exclusion policy. It records every exclusion. Execution-time credentials come from approved credential providers and are never copied into the snapshot or run artifacts.

Text payloads are normalized to LF newlines before hashing, and the normalization is recorded with the digest. A snapshot taken from a Windows checkout and one taken from a Linux checkout of the same skill must produce the same digest, or content addressing, cross-run reuse, and exact source-quote validation all become platform-dependent. Binary payloads are hashed as-is and marked so no normalization is attempted on them.

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
- `provisional`: integrity and minimum metadata are recorded; usable for continued construction or plan audit but not sufficient by itself for execution or a published scientific verdict.
- `validated`: approved for stated roles, scope, versions, and evidence-grade ceiling.
- `retired`: retained for reproducibility of older results but unavailable for new plans.

Resource records may become intrinsically validated after their required deterministic integrity, provenance, license, schema, and scientific-fit checks pass. Their use in a particular verdict still requires a passing plan audit.

New evaluator and bundle versions are registered as provisional. A passing `commit_plan_audit` atomically promotes only the exact evaluator and bundle versions covered by that audit. A failed or stale audit never promotes them. Any semantic uncertainty is recorded as a limitation and may reduce the grade ceiling.

### Claim types

Claim types use the same four states, with one difference: no automated step promotes them. An audit validates a plan against a claim type; nothing in a run establishes that the type itself was well defined, so `validated` is reachable for a claim type only by human review and a commit to the reviewed layer.

- A type proposed during routing is written to the runtime layer as `provisional`.
- Lookups return reviewed and provisional types together with their `origin`, and reuse should prefer a reviewed type when both fit. Reusing a provisional type propagates whatever was wrong with the run that proposed it.
- A reviewer promotes a good provisional type to the reviewed layer, and retires one that is redundant with, or subsumed by, an existing type.
- Provisional types that no result depends on are eligible for cleanup under the finalization rules below.

Left unattended, a shared type index accumulates near-duplicate proposals until reuse stops meaning anything, so periodic review is part of operating this system rather than an optional tidy-up.

## Keep after a run

Keep the minimum information required to reproduce and audit a returned scientific conclusion:

- Submitted-skill snapshot manifest and immutable snapshot payload, subject to retention policy.
- Source digest and claim manifest.
- Claim routing and index revision.
- Final evaluation plans and resource lock.
- Plan audits.
- Claim results, metrics, coverage, and decision outputs.
- Report-card JSON and Markdown.
- Tool-call events and operational errors needed for audit.
- Exact evaluator, bundle, resource, implementation, and environment versions.
- Subject-runner identity, subject model and generation settings, trial count, aggregation rule, per-trial outputs, and observed agreement for every published result. These are what make a result reproducible; discarding them leaves a number no one can re-derive.
- Reusable validated or provisional registry metadata.
- Managed payloads required by published results when retention and license permit.
- Operational-outcome records and the finalization summary.

Retention duration and storage location follow company policy. The verifier records the applied policy rather than inventing a duration.

## Return to the requester

Return:

- Human-readable report card.
- Machine-readable report-card JSON.
- Claim manifest.
- Claim-level result artifacts.
- A reproducibility manifest containing source-snapshot, evaluator, harness configuration, bundle, resource, subject-runner, subject-model, environment, and digest references, plus the trial count and aggregation rule each result was produced under.

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

Do not store per-skill claim manifests, plans, results, reports, downloaded datasets, or execution logs under `src/`, `skills/`, `registry/`, or evaluator implementation directories.

Only reusable definitions and implementation code enter the shared project, and only through a human commit. Run artifacts and every record a run writes remain isolated under `.verifier/` or company-managed storage.

## Failure and cleanup

A runner-owned finalizer, not the verifier agent, enforces cleanup. `write_report_card` invokes it before marking a run complete. The runner also invokes it after fatal termination, explicit cancellation, or expiration of the configured resumption window.

An unexpected interruption is resumable rather than immediately terminal. The runner retains only the committed artifacts and scratch data required to resume, records the interruption, and applies the configured resumption window. When that window expires, it records an operational outcome for unfinished claims and finalizes the run.

Finalization:

1. Preserves every artifact and immutable payload required by a completed claim result or retention policy.
2. Removes temporary downloads, decompressed copies, unused search results, superseded drafts, unreferenced execution outputs, caches, and secrets.
3. Retains provisional assets in the runtime registry only when their provenance and integrity records are complete and something references them; otherwise removes their runtime registry records and leaves unreferenced payloads eligible for managed-store garbage collection. Provisional claim types that no committed result depends on are removed on the same rule, which is what keeps the shared index from growing without bound. Finalization never touches the reviewed layer.
4. Records every retained category, discarded category, cleanup failure, and applicable retention rule in the run's finalization summary.

A cleanup failure does not change a scientific result. It produces an operational warning or run-scoped operational outcome, and the report must disclose any material left behind.
