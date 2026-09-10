# Stage 2: Claude Desktop integration

This is the implemented Stage 2 profile. The full workflow remains the specification for later stages. This profile explicitly narrows the host guarantees and stopping point for Claude Desktop **Chat**. The app owns the conversation; Python never runs a model API loop. A skill ZIP supplies instructions and a local MCP desktop extension supplies deterministic tools. A skill ZIP by itself cannot run the local verifier.

## Ownership and available operations

The operator installs the extension with a submission directory, a separate writable data directory, and a Python 3.11+ interpreter. Python accepts only sources inside that submission directory, writes only below `<data directory>/.verifier/`, and never executes submitted files or makes network requests. Stage 2 does not read or write the scientific registries.

Host controls are separate from scientific workflow tools:

- `start_verifier_run(source_path, model_label?)` creates a run and returns its bootstrap. `model_label` is optional caller-reported context, never a verified model identity.
- `get_verifier_context(run_id)` returns pinned instructions, validated state, and previously delivered snapshot ranges. Use this after conversation compaction or to recover a lost tool response.
- `resume_verifier_run(run_id)` verifies the journal and all referenced objects, records resumption, and returns the same bootstrap from saved instructions and source bytes.
- `cancel_verifier_run(run_id)` records an operational cancellation and finalization for an unfinished run. It never revises a completed checkpoint.

Only three workflow tools are implemented: `load_submitted_skill`, `read_snapshot_file`, and `commit_claim_manifest`. Every request includes `run_id` and the opaque `state_token` returned by the most recent response. Loading also supplies `source_path`, which must equal the authorized source; snapshot policy and limits come from the run, not the model. Reading and commitment include `snapshot_id` and `snapshot_digest`. Reading names `path` and optionally a half-open UTF-8 byte range `start`, `end`. Commitment supplies `claims` with exactly the six fields in the claim-manifest contract. The published JSON Schemas specify required fields, bounds, and reject additional properties.

## State and stop boundary

The Stage 2 state/tool matrix in [workflow.md](workflow.md#stage-2-profile) overrides the full-workflow matrix only for a run with `profile: stage2`.

Calls to an already closed run return a read-only `run_closed` rejection with no budget or journal mutation; host context retrieval remains available.

Both `claims_committed` and `no_scientific_claims` stop at `stage2_complete`, with `verification_complete: false` and no legal workflow tools. Accepted claims retain `routing` as their future state, but routing is unavailable in this profile. An empty manifest is a legitimate extraction result. Neither outcome produces a report card, evidence grade, or scientific verdict. Fatal errors and explicit cancellation end at `incomplete` with a run-scoped operational record. The Stage 2 finalizer retains committed audit material, removes its own temporary write files, and records that shared-store garbage collection is deferred. It does not delete user sources or other runs.

## Enforcement and app limitations

The dispatcher validates schemas, source authorization, file limits, snapshot/quote integrity, committed state, and independent repair/illegal-request budgets on every call. An OS file lock serializes writers. The random state token is replaced after every recorded workflow attempt; stale tokens are rejected before a workflow tool runs, using the illegal-transition budget. Two requests formed from the same state cannot both run. MCP does not expose an assistant-turn identity, so this is a concrete serialization guarantee, not a claim that Python can inspect Claude's turns. Host-control requests rejected before a run exists return a host-scoped validation error without creating run artifacts.

The default limits are 64 workflow attempts, 8 content repairs, 8 illegal transitions, 200 included files, 1 MiB per file, 8 MiB total normalized payload, 128 KiB per returned text range, 100 claims, and a 24-hour inactivity/resumption window. Zero remaining retries terminates the run. All attempts consume the workflow step limit. Reads and bootstrap restores cannot reset these budgets. Expiry is enforced on the next run access; no background scheduler is installed. Invalid/oversized protocol frames are rejected before dispatch. MCP requests are bounded to 1 MiB.

Claude Desktop controls other tools, context truncation, refusals, tokens, billing, and its model. This extension cannot disable the app's built-in tools or attest that an uploaded skill was loaded or followed. Tool-result trust labels do not become privileged system messages. Only supplied context, dispatcher actions, and committed artifacts are auditable here. Do not call this desktop prototype a fully isolated verifier host. Use a fresh Chat with the verifier skill and extension enabled; do not use unrelated tools for verifier work. App code execution may be required to enable uploaded skills, but is never a substitute for a verifier operation. A future restricted host is required for the stronger full-workflow isolation guarantees.

MCP does not expose the exact model/version, response IDs, stop reasons, or costs. Records set these unavailable fields to null and identify caller-provided labels separately. Scripted tests are explicitly labeled `scripted`; no Opus test is inferred. Live app acceptance must record the app version, visible model label, and any independently available exact identity, leaving unavailable values null. A stopped conversation without cancellation is resumable; the extension cannot claim to detect a model refusal or an app crash. Explicit resume records recovery; expiry records an operational outcome. No scientific outcome is inferred from silence.

## Bootstrap and persistence

The start operation pins the complete skill, workflow, Stage 2 contract, runtime contract, first-three-tool sections and common protocol, applicable artifact sections, snapshot resource policy, and machine-readable tool definitions by SHA-256. It returns ordered blocks labeled `verifier_instruction`, `committed_metadata`, `user_parameters`, or `untrusted_payload`. Instructions are copied once into the managed store and are reused on resume even if the installed extension is updated. Source content is returned separately and never interpolated into instructions. Previously delivered byte ranges are restored exactly; unread payloads are not silently supplied.

`events/00000001.json` and subsequent immutable events are the transaction journal. Each contains schema/implementation versions, UTC time, run and request IDs, event type, request/result, state before/after, artifact references, previous-event digest, and its own digest. Each event is atomically published after its referenced objects. It is the commit point. `run.json`, `source-snapshot.json`, and `claim-manifest.json` are readable projections repaired from the journal. A crash before event publication leaves unreferenced objects, not a committed transition; a crash afterwards replays the committed event. No hidden model reasoning is saved. Rejected input is logged as a digest and bounded diagnostic rather than arbitrary untrusted fields.

An altered/missing committed object or broken journal fails closed. If trusted run recovery or durable outcome persistence is impossible, return `fatal` with `operational_outcome_persistence_failed`, a null outcome ID, and no assertion that the run was durably finalized. SHA-256 detects accidental change; it is not protection against a local administrator rewriting both content and digests. This is a local-process boundary, not an operating-system sandbox against other programs concurrently changing filesystem objects. Multiple chats must use distinct run IDs. Context retrieval is a host control and does not advance workflow state or rotate the token.

## Snapshot policy v1

All symlinks, Windows junctions/reparse points, special files, and ambiguous Windows paths are rejected. Files are visited in sorted relative-path order. Exclude `.git`, `.hg`, `.svn`, `.verifier`, `.venv`, `venv`, `env`, `node_modules`, `__pycache__`, `.pytest_cache`, `tmp`, `temp`, `dist`, and `build`; exclude `.env*`, private-key/credential filenames, and recognized credential material. Record exclusion reasons without retaining secret bytes. An excluded or empty top-level skill is fatal. This conservative policy is not a complete secret detector; submit a dedicated sanitized skill folder. Required files that cannot be included must not be replaced with live files.

UTF-8 text without NUL is normalized from CRLF/CR to LF; undecodable known text files are fatal, other binary files are stored unchanged. Text classification depends on bytes and a fixed text-extension list, never the platform MIME registry. Snapshot identity hashes the sorted normalized file records and policy identity, excluding source location/time and the exclusion list. Claim IDs hash normalized claim fields and snapshot identity. Duplicate normalized statements or identical claim records are rejected; Python validates structural atomicity (single nonempty statement), not scientific meaning. Quote strings must occur verbatim in a previously delivered range of the named snapshot file. Markdown links are never followed automatically or fetched.

## Acceptance checklist

- Valid file/folder: stable LF-normalized snapshot; source provenance separate from identity.
- Invalid/missing/unsafe/oversized source: durable operational failure, no manifest.
- Reference-file claim: exact quote accepted only after that reference range is read.
- Zero claims: empty manifest and Stage 2 checkpoint, no scientific result/report.
- Illegal/stale-token request: no workflow side effect; only illegal budget decreases.
- Retryable legal request: no workflow transition; only repair budget decreases.
- Interruption: replay the journal, verify objects, restore trusted labels and read ranges.
- Corrupted object/journal, cancellation, expiry, exhausted limits: fail closed with the applicable operational outcome or explicit persistence-failure response.
- Conflicting source instructions: retain them as data; attempts to invoke other tools or read outside the authorized snapshot are rejected. Scripted tests establish dispatcher behavior; an app test is still needed to assess model adherence and claim quality.
- Packaged extension: initialize, list tools, bootstrap, and run all three workflow tools through stdio from an extracted package. Validate the package manifest separately from app installation.

## Stage 3 dependency: independently released catalog

Stage 3 will retrieve a reviewed catalog from this project's existing GitHub repository. A release manifest must identify catalog/schema version, minimum compatible runtime/skill interfaces, each asset's exact version/digest, and its reviewed provenance. Runs pin a verified manifest and evaluator/resource versions at start; updates never change an active run. Verify downloaded bytes before caching or use, reject incompatible manifests explicitly, and permit offline reuse only of a previously verified compatible cache. A missing cache/download is an operational availability result, not an empty successful search. Candidate run contributions stay local until user-authorized submission and maintainer review. New executable methods still require reviewed code. No catalog downloads or publication are implemented in Stage 2.

## Integration sources

Verified during implementation: [Claude custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills), [skill upload and enablement](https://support.claude.com/en/articles/12512180-use-skills-in-claude), [local desktop extensions](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop), [MCPB manifest](https://github.com/anthropics/mcpb/blob/main/MANIFEST.md), and the MCP [stdio](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports), [lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle), and [tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) specifications. App installation and UI behavior remain a live acceptance step.
