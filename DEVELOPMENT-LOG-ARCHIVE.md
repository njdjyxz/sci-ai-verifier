# Development log archive

Full text of every development entry from 2026-09-08 through the six-axis report card
work of 2026-09-21, moved here on 2026-09-21 when the active plan was condensed. Nothing
is edited; entries appear exactly as written, oldest first. `DEVELOPMENT-PLAN.md` carries
the current state, a condensed history of these entries, and the latest entry in full.

The reviewed workflow and contracts under `skills/scientific-verifier/references/` remain
authoritative over anything recorded here. Several entries below describe designs that
were later changed, rejected or superseded; read them as a record of how the project
arrived where it is, not as instructions.

---

## Codex: 2026-09-08

### Current stage and status

Stage 1 is substantially complete as a reviewed Markdown specification and provides a foundation for Stage 2. A focused contract update is now needed to reflect the approved Claude Code testing target and Stage 3 GitHub catalog distribution. The active Python runtime has not been implemented. Runtime behavior and scientific performance still require implementation and testing.

The current approved three-stage plan is:

1. **Stage 1 - Skill instructions and tool contracts.** Define the agent/Python responsibilities, workflow branches, tool interfaces, saved records, grading rules, and failure behavior in readable Markdown. Extend the contracts with Claude Code integration responsibilities and catalog update, compatibility, version-locking, and offline behavior before implementing those features.
2. **Stage 2 - Minimal working skill in Claude Code.** Use Claude Code's existing conversation and tool loop. Implement the Python tools and controlled dispatcher needed for submission loading, snapshot-file reading, claim-manifest creation, state validation, limits, persistence, and event logging. Test deterministic operations with scripted requests and fixtures, then test the skill in the user's own Claude Code installation. Record the actual configured Opus model identifier/version in test records.
3. **Stage 3 - Claim routing and shared evaluator lookup.** Add claim-type matching, evaluator discovery, and retrieval of a reviewed catalog from the existing GitHub repository. Release the catalog independently from the skill, check compatibility, cache verified assets, and pin the catalog and evaluator/resource versions for each run. Cover unavailable downloads and offline reuse explicitly. Seed a small reviewed evaluator collection and demonstrate submission-to-selection behavior against expected artifacts and relevant legacy test cases.

Approved change of direction: Stage 2 now targets Claude Code's existing loop, replacing the earlier proposal to build a separate Python loop around the model API. Python still validates workflow operations and owns the saved records. GitHub distribution extends the original Stage 3 lookup scope. The published contracts and README still describe the earlier host arrangement and must be reconciled before runtime implementation.

The catalog may grow through reviewed contributions from user runs. Runs save candidate configurations and resources locally; shared publication requires user-authorized submission and maintainer review. New executable checking methods still require reviewed implementation. Compatible catalog additions should not require reinstalling the skill; changes to required interfaces, checking code, or dependencies may require a runtime or skill update.

Evaluation planning, resource acquisition, subject execution, scientific assessment, and final grading follow these three stages. Their intended behavior is already described in the Stage 1 documents.

### What has been done

Prior work summarized for this first entry:

- Established the seven verifier specification documents: [SKILL.md](skills/scientific-verifier/SKILL.md), [workflow](skills/scientific-verifier/references/workflow.md), [tool contracts](skills/scientific-verifier/references/tool-contracts.md), [runtime contract](skills/scientific-verifier/references/runtime-contract.md), [artifact contracts](skills/scientific-verifier/references/artifact-contracts.md), [resource policy](skills/scientific-verifier/references/resource-policy.md), and [evidence rubric](skills/scientific-verifier/references/evidence-rubric.md).
- Preserved the previous implementation under `tmp/legacy_fixed_workflow/` and kept the active project focused on the new specification.
- Completed multiple review rounds and addressed nine workflow problems in commit `59a0b62`, including claim-local fallback, resource repair and lock ownership, trial grading, independent documentary assessment, and untrusted source handling.
- Recorded the user's decisions to use audited claim-specific trial thresholds and to allow documentary-only D without a subject runner, while still requiring an approved documentary capability and an independent assessor.
- Added the [review guide](https://github.com/njdjyxz/sci-ai-verifier/blob/f7293ecec224176688ea90058b068fc01eb8bacc/reviews/REVIEW-GUIDE.md), covering document purposes, loading stages, review order, and scenarios to check.
- Consolidated the branch histories into `main` and pushed the specification and review guide to GitHub through commit `5b9d66b`.
- Earlier validation covered document links, tool/transition consistency, JSON examples and registries, formatting, and scenario walkthroughs. The official skill validator could not run because PyYAML was unavailable; equivalent structural checks were used. These checks do not establish that the future runtime works.

Today's work: created this development log, then updated the same daily entry with the user's approval of the Claude Code-first Stage 2 and GitHub distribution in Stage 3. Updated the maintenance rules to permit one entry per agent per day, with additional same-day entries requiring explicit approval. Before creating the file, the local working tree was clean at `5b9d66b` and matched the locally recorded `origin/main`. This log remains a local addition; no commit or push is included in this entry. These updates record the approved plan; they do not implement the runtime or catalog distribution.

### Urgent next steps, if any

None requiring immediate action. Before implementing the dependent Stage 2 behavior, resolve and document:

- Which responsibilities Claude Code provides and which the Python dispatcher must enforce, including context delivery, tool access, state ownership, and limits. Skill instructions alone do not establish enforced restrictions on other tools or direct file access.
- How the limited prototype stops after claim-manifest creation, including an empty manifest, without claiming that a complete scientific verification run has finished.
- The host's behavior for interruption, resumption, cancellation, and fatal-error reporting, including any conflicting directions in the current contracts.
- The minimum event-log fields and acceptance checks needed to show what instructions were supplied, which tools ran, what they returned, and how committed state changed.

### Suggested next move

Proceed toward the small Stage 2 prototype in the user's Claude Code installation. First update the [documented Stage 2 boundary](README.md#next-implementation-stage) and affected contracts to match the approved host arrangement while retaining the first-three-tools scope. Use the prototype to test whether the instructions and tool interfaces can be followed in practice. Implement GitHub catalog distribution during Stage 3.

The proposed event log should be written by the Python execution layer and link to saved artifacts. It will support workflow checks and debugging. Assessing whether extracted claims are scientifically appropriate also requires expected examples and expert review; the log alone cannot establish that.

### Recommended next action

Prepare a short Stage 2 implementation checklist and reconcile the relevant contracts with the approved Claude Code arrangement before adding runtime code. Specify how the skill calls the controlled Python tools and which protections the test environment actually enforces. Include acceptance cases for a valid submission, an invalid source, claims in reference files, zero claims, an illegal tool request, a retryable request, interrupted execution, and source text containing instructions that conflict with verifier policy. Define the catalog distribution contract as a Stage 3 dependency without implementing it in Stage 2.

This preparation is finished when the Stage 2 integration boundary, scope, stopping point, saved records, event-log fields, and expected outcome for each acceptance case are explicit and consistent. Then implement and test the bootstrap support, dispatcher, and first three tools with scripted requests and fixtures, followed by a bounded test in Claude Code using the user's configured model.

## Codex: 2026-09-09

### Current stage and status

Stage 2's deterministic implementation and Claude Desktop installation packages are ready. Live installation and acceptance in the user's Claude app remain pending, so Stage 2 is not yet accepted as working in that app. Scientific claim quality has not been validated by a model or expert, and no scientific evaluation or grading is implemented.

Latest direction today: defer installation and live execution. Claude's code and contract review is the next step, with compatibility as the first priority. This replaces the earlier recommendation in this entry to install and run the packages immediately; the desktop target and Stage 2 scope remain unchanged.

Approved change of target today: the user clarified that they use the actual Claude app, not Claude Code CLI, and asked for everything to be ready to install there. This supersedes the September 8 Claude Code installation target. Stage 2 now uses **Claude Desktop Chat**, an uploaded skill ZIP, and a local Python MCP extension. The app owns the conversation; there is no separate model API loop. The first-three-workflow-tools boundary remains unchanged. Exact model/version and response IDs are unavailable through this MCP interface and are recorded as null; caller-reported labels are distinguished from verified identity. No Opus run has been claimed or simulated.

### What has been done

- First committed the previously local development plan as `9f74d70` (`Record approved Claude Code Stage 2 development plan`) and successfully pushed `main` to `origin/main`. At the initial implementation handoff, the new Stage 2 changes below were local and uncommitted. The user subsequently requested publication of the implementation and updated review plan to the remote; this entry accompanies that source commit. Installation and live execution remain deferred.
- Read the current repository instructions, development log, workflow/tool/runtime/artifact contracts, resource policy, evidence rubric, registries, and review context. Checked current primary documentation for Claude skill uploads, desktop extensions, MCPB packaging, and MCP stdio/tool interfaces.
- Before adding runtime code, reconciled the host boundary in the [Stage 2 contract](skills/scientific-verifier/references/stage2-contract.md), [workflow matrix](skills/scientific-verifier/references/workflow.md#stage-2-profile), and affected tool/skill/artifact/runtime documents. Updated [README.md](README.md), [CLAUDE.md](CLAUDE.md), and the historical review guide. Removed the superseded runtime document's direct-model-API settings claims.
- Implemented [bootstrap and recovery](src/sci_ai_verifier/agent.py), [strict input schemas and state-aware dispatch](src/sci_ai_verifier/tools.py), [content-addressed storage and atomic event journal](src/sci_ai_verifier/storage.py), [snapshot loading and reading](src/sci_ai_verifier/ingest.py), [claim-manifest validation](src/sci_ai_verifier/claims.py), and [stdio MCP transport](src/sci_ai_verifier/mcp.py). The active runtime uses the Python standard library only and does not import or modify the preserved legacy implementation.
- Enforced configured source boundaries, link/junction rejection, exclusions, LF normalization, file/read/request/claim limits, exact quotes from delivered source ranges, independent repair and illegal-transition budgets, and random state-token serialization. Both nonempty and empty manifests stop at `stage2_complete` with `verification_complete: false`. No result grade or report card is manufactured.
- Added pinned instruction/context receipts, immutable event records with state before/after, readable artifact projections, cancellation, access-time resumption expiry, snapshot integrity checks, and recovery for crashes before/after journal publication. Cleanup retains committed audit objects, removes run temporary writes, and explicitly defers shared-store garbage collection.
- Added the [desktop extension manifest](desktop/manifest.json), [reproducible builder](scripts/build_desktop.py), [installation guide](desktop/INSTALL.md), [pending app acceptance record](desktop/APP-ACCEPTANCE.md), and [three example submissions](examples/submissions/). Built the MCPB, skill ZIP, configuration example, installation notes, and SHA-256 checksums under gitignored `dist/`. These files are ready to select in the app; no app settings were changed and neither package was installed.
- Validation: `python -m unittest discover -s tests -v` ran **28 tests: 27 passed, 1 skipped**. Coverage includes reference-file and empty manifests, source mutation, exact/partial UTF-8 reads, malformed and unauthorized requests, independent budgets, concurrent stale tokens, corrupted objects/journals, simulated crash recovery, cancellation/expiry, exclusions/limits, and instruction-conflict dispatcher behavior. The extracted desktop package completed bootstrap and all three workflow tools through an actual stdio subprocess; archive reproducibility and skill ZIP structure passed. A physical Windows junction rejection test passed; the physical symlink test was skipped because this process lacks Windows symlink-creation privilege.
- Anthropic's `@anthropic-ai/mcpb` **2.1.2** validator accepted `desktop/manifest.json`. Active Markdown file links, Python syntax, registry JSON, legacy import isolation, and `git diff --check` passed. These checks do not establish live app installation, skill loading, scientific claim completeness, or full host isolation.
- Defined [Stage 3's catalog distribution dependency](skills/scientific-verifier/references/stage2-contract.md#stage-3-dependency-independently-released-catalog): independent catalog releases from the existing repository, compatibility checking, digest verification, pinned assets, explicit offline/cache outcomes, and reviewed contribution publication. No catalog retrieval, routing, evaluator lookup, or publication was implemented.

### Urgent next steps, if any

None requiring immediate installation or execution. Review the current implementation and its compatibility assumptions first. Live app acceptance remains a later prerequisite for calling Stage 2 validated in Claude Desktop. The MCP extension cannot enforce other app tools, inspect private model stop reasons, control model costs, or certify an exact model identity; the review must check that code and documentation consistently respect those limits.

### Suggested next move

Have Claude review the current Stage 2 code against the reviewed contracts and the focus areas below. Prioritize issues that could prevent compatibility, corrupt or misinterpret saved state, or overstate the prototype's guarantees. Keep installation, live app testing, and Stage 3 implementation deferred during this review.

### Recommended next action

Read the [Stage 2 contract](skills/scientific-verifier/references/stage2-contract.md), then review [the active runtime](src/sci_ai_verifier/), [desktop packaging](desktop/), and [tests](tests/), including uncommitted and untracked files. Produce a prioritized review with file/line references, a concrete failure scenario, supporting evidence, and the smallest appropriate correction for each finding. Separate demonstrated defects, compatibility assumptions requiring verification, and choices needing a user decision. The review is finished when the areas below have been addressed and remaining app-only checks are explicitly recorded as deferred. This planning update does not claim that the review has already occurred.

### Areas for Claude to prioritize in code review

These are review questions, not confirmed defects. Compatibility deserves the most attention because the implementation was exercised with scripted clients on Python 3.14, while its package advertises Python 3.11+ and several MCP protocol versions.

1. **Saved-run and upgrade compatibility.** Review [agent.py](src/sci_ai_verifier/agent.py), [storage.py](src/sci_ai_verifier/storage.py), and the version fields in [tools.py](src/sci_ai_verifier/tools.py). Can a new runtime safely resume a run created by an older runtime or artifact schema? Pinning old instructions does not by itself pin the Python behavior interpreting them. Check whether unsupported versions are explicitly rejected, what compatibility policy is needed, and how changed submission/data-directory settings affect authorization on resume. Identify any migration requirement before proposing a migration mechanism.

2. **MCP, desktop packaging, and Python compatibility.** Review [mcp.py](src/sci_ai_verifier/mcp.py), [the extension manifest](desktop/manifest.json), [the entry point](desktop/server.py), [the builder](scripts/build_desktop.py), and [pyproject.toml](pyproject.toml). Compare the supported protocol versions with their initialization, notification, tool-schema, result-envelope, and error requirements, especially differences involving `structuredContent`. Check Python 3.11 compatibility separately from the observed Python 3.14 test result. Check Windows paths with spaces/non-ASCII characters, interpreter selection, isolated Python startup, package-relative imports, and required instruction files. Distinguish the MCPB, uploaded skill, and optional Python-package installation paths; do not infer that testing one validates all of them. Validate external interface assumptions against primary documentation during review; app-specific behavior remains unverified until a later app test.

3. **Persistence, concurrency, and failure recovery.** Review [storage.py](src/sci_ai_verifier/storage.py) and [the dispatcher](src/sci_ai_verifier/tools.py). Inspect the precise journal commit point, object writes, projection repair, OS locks, token changes, and lost-response recovery. Cover concurrent processes as well as threads, corruption of different parent artifacts, missing journal tails, disk/permission failures, and interruption at each write boundary. A durable successful commit must not be reported as rolled back because a readable projection failed; an uncommitted operation must not appear complete.

4. **Source access and untrusted content.** Review [ingest.py](src/sci_ai_verifier/ingest.py), [claims.py](src/sci_ai_verifier/claims.py), and context assembly. Examine traversal, Windows junctions/reparse points, alternate path forms, filesystem changes during snapshotting, and limits applied before expensive reads. Check that secret exclusions, UTF-8/LF normalization, partial-read receipts, and exact quote checks match their documented scope. Confirm that resumed payloads remain untrusted and that local path validation is not described as an OS sandbox or proof of model adherence.

5. **State-machine and scientific-scope consistency.** Compare code with the [Stage 2 workflow matrix](skills/scientific-verifier/references/workflow.md#stage-2-profile) and [tool contracts](skills/scientific-verifier/references/tool-contracts.md). Check independent retry budgets, illegal/stale requests, closed runs, cancellation, expiry, and host-control errors. Both empty and nonempty manifests must stop at the extraction checkpoint without routing, grades, or scientific verdicts. Structural claim validation must not be presented as evidence of scientific atomicity, completeness, or correctness.

6. **Test independence and missing evidence.** Review [runtime tests](tests/test_stage2.py) and [package tests](tests/test_desktop_package.py) for assumptions shared with the implementation. A client written beside the server may repeat the same protocol mistake. Identify where an independent MCP client, a Python-version matrix, process-level concurrency checks, or stronger fault injection would add meaningful evidence. Keep the skipped physical symlink case and deferred desktop/model tests visible. Recommend targeted checks for actual risks rather than duplicating implementation details in tests.

This section and the revised next steps were added at the user's request after the implementation summary above. Only this development plan was edited for this follow-up; installation and execution were deferred, and no code-review findings or new runtime-test results are asserted.

## Claude: 2026-09-10

### Current stage and status

Stage 2's implementation was reviewed today against the reviewed contracts and the six priority areas Codex recorded on September 9. Codex then read the review, independently reproduced the main failures, adjusted several recommendations, and directed two bounded repair batches. **Both batches are implemented and tested, and this entry accompanies the commit that publishes them to `origin/main`.** They are published for review, not because they have been reviewed. Installation and live app testing remain deferred and unattempted.

The review found six reproduced defects and two contract-drift problems; all eight are repaired. Nothing found or changed affects scientific meaning: the runtime still produces no grade, verdict, or report card, and grade and status remain independent axes.

Superseded within this entry: the four choices listed under "Suggested next move" were open questions when the review was written. Codex decided all four and overrode two of my recommendations. Equivalent path spellings now **succeed** rather than becoming retryable errors, and the bootstrap keeps a **single complete JSON text result** rather than a short summary, because duplication was consistent with the 2025-06-18 compatibility guidance and shortening the text block would disadvantage older clients. Codex also noted correctly that the shell prohibition was not entirely lost from the pinned context: `SKILL.md` carries it too, so the missing `## Excluded capabilities` section weakened that boundary rather than removing it. The findings below are kept as written, describing the code as it was; the "Repairs applied today" section states what each one became.

Review scope and limits: read the Stage 2 contract, the workflow matrix, tool/runtime/artifact/resource contracts, all of `src/sci_ai_verifier/`, `desktop/`, `scripts/build_desktop.py`, `pyproject.toml`, both test modules, the fixtures, `README.md`, and the install/acceptance documents. All checks ran on Windows 11, Python 3.14.0, starting from a clean tree at `c6969e2`, where `python -m unittest discover -s tests` reproduced 28 tests, 27 passed, 1 skipped. Each finding was reproduced with a scratch script outside the repository before it was repaired; those scripts are not committed. Nothing was installed in Claude Desktop and no model behavior was observed, so claim quality is still unassessed.

### What has been done

**Reproduced defects, most important first.** These are demonstrated, not suspected.

1. **A cosmetically different source path fatally kills the run at the first workflow call.** [tools.py](src/sci_ai_verifier/tools.py) line 197 compares `arguments["source_path"]` to `state["source_path"]` as raw strings. Passing the same directory with forward slashes, a trailing separator, or a lowercase drive letter each returns fatal `source_not_authorized`, writes a terminal operational outcome, and moves the run to `incomplete`. Only the byte-identical string returned at bootstrap works. Claude commonly renders Windows paths with forward slashes, so this is a likely first-call failure in the app, and it is unrecoverable rather than retryable. Verified smallest correction: compare `no_links(arguments["source_path"])` with `Path(state["source_path"])`; that accepts all four spellings and still rejects a genuinely different directory, because `Path` equality on Windows is case-insensitive and `os.path.abspath` already normalizes separators.

2. **The bootstrap tool result is about 227 KB per call and carries its payload twice.** [mcp.py](src/sci_ai_verifier/mcp.py) lines 82-85 place the identical response in `content[0].text` (about 112 KB) and again in `structuredContent`. The pinned instruction set is 107 KB before framing, of which `workflow.md` alone is 50 KB and is pinned whole, including the later-stage matrices Stage 2 does not implement. `get_verifier_context`, the documented recovery path after compaction, measured 230 KB and can be called repeatedly. This is a plausible reason for the app to truncate or refuse the very first result.

3. **`get_verifier_context` is published as read-only but can end the run.** [tools.py](src/sci_ai_verifier/tools.py) line 63 sets `readOnlyHint: true` and its description says it does not advance workflow. In [agent.py](src/sci_ai_verifier/agent.py) the expiry check at line 160 runs before the context branch at line 163, so calling it on an expired run appends an `incomplete` journal event plus an operational outcome and returns fatal `resumption_expired`; every call also rewrites `run.json`. Reproduced both effects. An MCP client may treat a read-only tool as safe to auto-approve or retry.

4. **`persistence_failure()` is returned for conditions that are neither fatal nor persistence failures, and it asserts a state it never read.** [tools.py](src/sci_ai_verifier/tools.py) lines 80-87 hardcode `run_state: incomplete` and `committed_state: incomplete`. Two reproduced paths reach it wrongly. A syntactically invalid Windows `source_path`, such as a pasted path that still has its surrounding quotation marks, makes `no_links` in [storage.py](src/sci_ai_verifier/storage.py) raise a bare `OSError` (WinError 123) that only the `except OSError` at [agent.py](src/sci_ai_verifier/agent.py) line 42 catches; the caller is told a durable audit failed, when in fact no run was ever created. That contradicts the Stage 2 contract's rule that host-control requests rejected before a run exists return a host-scoped validation error. Separately, lock contention returns the same fatal after about 9.1 seconds, because `msvcrt.locking(LK_LOCK)` in [storage.py](src/sci_ai_verifier/storage.py) lines 71-76 raises `OSError` once its roughly ten-second retry expires; on POSIX `fcntl.flock` blocks indefinitely instead, so the two platforms fail differently. In both cases a healthy run is reported as incomplete.

5. **There is no compatibility gate on saved runs; this answers Codex's priority-1 question.** `Store.read` in [storage.py](src/sci_ai_verifier/storage.py) lines 115-147 validates journal linkage, filenames, `profile`, and `revision`, but never `schema_version` or `implementation_version`, and never checks that the committed state contains the keys the current code reads. A run whose committed state claims `schema_version: 99` and `implementation_version: 9.9.9` was silently resumed by 0.2.0. A run whose state is missing `read_receipts` or `limits` raised an uncaught `KeyError`, which the blanket handler at [mcp.py](src/sci_ai_verifier/mcp.py) line 108 converts into JSON-RPC `-32603`; the run is not failed closed, no operational outcome is written, and the model receives a transport error with no state. So unsupported versions are not rejected, there is no migration story, and the incompatibility that would need one currently crashes instead of failing closed. Deciding a supported `schema_version` set now, while no saved run needs migrating, is cheaper than deciding it later.

6. **A reparse point anywhere in a configured directory's ancestry crashes the server at startup.** `Runtime.__init__` in [agent.py](src/sci_ai_verifier/agent.py) lines 19-21 calls `no_links` on the workspace, submission, and instruction roots, and nothing catches it at [__main__.py](src/sci_ai_verifier/__main__.py) line 22. Reproduced with a junctioned data directory: raw Python traceback, exit code 1, and no message a user could act on inside the app. Windows Enterprise redirected or junctioned folders make this realistic; `C:/Users/All Users` on this machine is a reparse point. The check also rejects every reparse tag rather than only the name-surrogate tags that actually redirect, and `Fault("unsafe_path", ...)` never names the offending path, so the same failure inside a 200-file snapshot gives no way to find the file. A non-writable data directory fails the same way, through `OSError` from `Store.__init__`.

**Contract drift.** Both belong in the same commit as any related code change, per the repository rule about the two halves of one contract.

7. **`concurrent_request_rejected` is specified but not implemented.** [runtime-contract.md](skills/scientific-verifier/references/runtime-contract.md) line 23 requires that a serialized second request in one assistant turn be rejected with that stable code. The dispatcher returns `illegal_transition` instead. The budget accounting is correct: [tool-contracts.md](skills/scientific-verifier/references/tool-contracts.md) already assigns "a second workflow request in the same assistant turn" to the illegal-transitions budget. Only the code drifts, and the Stage 2 contract's own explanation that MCP exposes no assistant-turn identity is the reason it may be right to fold them. That reasoning is not currently written down as a decision, and the stable code appears nowhere in the code or in the Stage 2 contract.

8. **The bootstrap truncation drops the two sections Stage 2 most depends on.** [agent.py](src/sci_ai_verifier/agent.py) lines 102-107 cut `tool-contracts.md` at `## Routing tools`, which removes `## Excluded capabilities` at line 500, the only pinned text stating that the agent gets no shell, no arbitrary Python, and no direct filesystem access, and that `read_snapshot_file` is not an exception to that rule. It cuts `artifact-contracts.md` at `## Routing artifact`, which removes `## Operational outcome` at line 289, the contract for the only non-happy-path artifact Stage 2 writes and the section that defines the `operational_outcome_persistence_failed` code its results return. Since the extension cannot enforce the app's other tools, the excluded-capabilities text is the mitigation, and it is the part being cut while 50 KB of not-yet-implemented workflow is retained.

**Compatibility assumptions checked against primary documentation today.**

- **MCP protocol era.** The current MCP revision is `2026-07-28`, which removes the `initialize` handshake in favour of a per-request `_meta` protocol version and a mandatory `server/discover`; `2025-11-25` and earlier are now called legacy. [mcp.py](src/sci_ai_verifier/mcp.py) line 13 supports only `2025-06-18`, `2025-03-26`, and `2024-11-05`, so it is legacy-only. The spec's compatibility matrix says a modern-only client against a legacy server fails, while a dual-era client works. I ran the documented stdio probe against this server: `server/discover` returns `-32000`, which is not a recognized modern error, so a dual-era client should fall back to `initialize`, and the legacy handshake then lists all seven tools. The extension is therefore probably compatible with a dual-era Claude Desktop, but this is inference from the specification, not an app test, and the Stage 2 contract's integration sources still cite the 2025-06-18 revision as current.
- **Lifecycle strictness.** [mcp.py](src/sci_ai_verifier/mcp.py) lines 73-74 reject `tools/list` before `notifications/initialized` with `-32000`. That is stricter than the lifecycle specification requires. Claude Desktop is expected to send the notification; some clients and inspectors do not always.
- **MCPB manifest.** Manifest version 0.3 is current and `win32` is a valid platform. [manifest.json](desktop/manifest.json) sets `tools_generated: true` and declares no `tools` array. The specification treats `tools` as optional but recommends declaring it, and `tools_generated: true` signals that tools appear dynamically, which is the opposite of this project's fixed, reviewable tool array. Users installing the extension see no tool list beforehand.
- **Python version.** Still only exercised on 3.14. `pyproject.toml` and the manifest advertise 3.11 or newer. I did not run a 3.11 interpreter, so that claim remains unverified.
- **Pinned settings versus live configuration.** Limits, `source_root`, and `source_path` are pinned into run state at start, and `snapshot` in [ingest.py](src/sci_ai_verifier/ingest.py) line 54 authorizes against the saved root, so narrowing the operator's submission directory afterwards does not restrict a run already created. Separately, [tools.py](src/sci_ai_verifier/tools.py) line 34 hardcodes the byte-range maximum and the claims array bound to the default limits, so raising `max_file_bytes` or `max_claims` in configuration has no effect on what the published schema accepts. Both behaviors are defensible; neither is documented.

**Test evidence gaps.** No test covers lock contention, because the existing concurrency test finishes its first call before the second starts and so only exercises the token check. No test covers a saved run from another schema or implementation version, `get_verifier_context` on an expired run, or a cosmetically different `source_path` at load. The MCP client in the tests is written in this repository beside the server, so a shared protocol mistake would not be caught; an independent client would be real evidence. There is no Python 3.11 run and no non-ASCII path case, though the package test does use a directory with a space. The physical-symlink test is still skipped for lack of Windows symlink privilege. `test_source_instruction_cannot_change_tool_authority` shows only that this server rejects a request named `Bash`; it cannot say anything about the app's own tools, and its name reads stronger than what it demonstrates.

**What held up under review.** The Stage 2 legality table in [tools.py](src/sci_ai_verifier/tools.py) matches the [workflow matrix](skills/scientific-verifier/references/workflow.md#stage-2-profile) exactly. `verification_complete` is unconditionally false, terminal outcomes set `scientific_status` and `evidence_grade` to null, and no grade, verdict, or report card is produced anywhere. There is no write path to `registry/` and no import of the preserved legacy implementation. Objects are written before the event that references them, a projection failure cannot roll back a committed event, journal sequence gaps and digest breaks are detected, and secret-name, size, and traversal checks run before expensive reads. Duplicate JSON keys and non-finite numbers are rejected at the protocol boundary. All three fixtures snapshot and reach `stage2_complete`.

### Repairs applied today, after Codex's direction

Two batches, in the order Codex set. Everything below is implemented and passing, and is published in the commit this entry accompanies.

**Batch 1: correctness and saved-state protection.**

- *Finding 1.* `authorized_source` in [ingest.py](src/sci_ai_verifier/ingest.py) resolves the supplied path before comparing it, so any spelling of the authorized location loads normally. A path that resolves elsewhere is still fatal with an operational outcome; a path the OS cannot interpret is a correctable `invalid_path` that leaves the run in `created`.
- *Finding 4.* `no_links` in [storage.py](src/sci_ai_verifier/storage.py) turns an unusable path into a typed `invalid_path` instead of a bare `OSError`, and names the offending path in every unsafe-path message. The writer lock is now acquired without blocking on both platforms, retried for two seconds, and then reported as retryable `run_busy`; contention leaves revision, budgets, and token untouched. `persistence_failure` in [tools.py](src/sci_ai_verifier/tools.py) no longer asserts `incomplete` for a state it never read: it reports the state unknown and names the established cause in `details`.
- *Finding 5.* [storage.py](src/sci_ai_verifier/storage.py) declares `SCHEMA_VERSION`, the supported set, and the required state and limit fields, and `compatible()` rejects anything else as `incompatible_run_record` before the record is used. There is no automatic migration and the saved bytes are never rewritten. A missing field now fails closed instead of raising `KeyError` into a JSON-RPC `-32603`.
- *Finding 6.* [agent.py](src/sci_ai_verifier/agent.py) validates each operator directory and builds the pinned instructions during construction, raising `ConfigurationError` naming the setting and the remedy; [__main__.py](src/sci_ai_verifier/__main__.py) prints that one line and exits 2 with no traceback.

**Batch 2: context tool and interoperability.**

- *Finding 3.* No tool is published as read-only any more, and `get_verifier_context` now states in its own description that it repairs projections and can record expiry and end the run.
- *Findings 2 and 8.* `PINNED_CONTEXT` in [agent.py](src/sci_ai_verifier/agent.py) replaces truncation with a named Stage 2 selection, and bootstrap fails closed with `missing_instruction_section` if any named heading is absent. `## Excluded capabilities` and `## Operational outcome` are now pinned; later-stage workflow steps, routing, execution, report-card, and planned-runtime-file sections are not. Pinned instructions went from 107,190 to 77,152 bytes while gaining those two sections, and the assembled bootstrap result went from 227,421 to 84,516 bytes, because [mcp.py](src/sci_ai_verifier/mcp.py) now returns one complete JSON text block instead of repeating it as `structuredContent`. A test measures the assembled response so a contract edit that balloons it fails here rather than in the app.
- *Finding 7 and interoperability.* Stale tokens keep charging the illegal-transition budget, and the [Stage 2 contract](skills/scientific-verifier/references/stage2-contract.md) now states the exception explicitly: MCP exposes no assistant-turn identity, so `concurrent_request_rejected` is not emitted and a restricted host is expected to emit it. A new "MCP compatibility target" section records that Stage 2 is legacy-revision-only, that this is evidence of neither compatibility nor incompatibility, and that no second protocol implementation should be written before the acceptance record names a target. [manifest.json](desktop/manifest.json) declares all seven tools with `tools_generated: false` and still passes the official MCPB 0.3 validator.
- *Contracts changed in step with the code.* [SKILL.md](skills/scientific-verifier/SKILL.md) no longer promises the complete `workflow.md`; it describes a profile-named selection that must contain every reachable step. The Stage 2 contract gained the path-equivalence rule, the `run_busy` rule, the saved-run compatibility policy, the pinned-selection list with its rationale, the single-JSON-result rule, and seven new acceptance-checklist lines. [INSTALL.md](desktop/INSTALL.md) moves the data directory out of the checkout and states the reparse-point and startup-diagnostic behavior. [APP-ACCEPTANCE.md](desktop/APP-ACCEPTANCE.md) gained a compatibility-target table, because those are the questions scripted tests cannot answer.

**Tests.** 28 tests became 41: 39 pass, 2 skip. New coverage: equivalent and unusable path spellings; malformed paths at both the host and workflow boundary; a real second process holding the OS lock; unsupported schema version, missing state field, and missing limit key, each asserting the record is byte-identical afterwards; a drift guard tying the saved state shape to the compatibility constants; unusable configuration through both the API and the packaged server's stderr; pinned-section presence and absence plus the fail-closed path; measured bootstrap size; a non-ASCII and spaced source and data directory; a specification-derived wire-protocol conformance check; a 3.11 syntax floor check; and manifest-to-tool-array agreement. Every new test was run against `c6969e2` in a temporary worktree first and failed there, so none of them is a tautology. The two skips are the physical symlink case, which needs Windows symlink privilege, and the minimum-interpreter run, which is skipped with an explicit message because only Python 3.14 is installed here.

**Validation limits.** Everything was exercised on Windows 11 and Python 3.14 only. The packaged extension was rebuilt and completes the full stdio flow from an extracted archive, and the manifest was revalidated offline with the cached `@anthropic-ai/mcpb` 2.1.2. The wire-protocol test is still Python written in this repository: it encodes named specification requirements rather than `mcp.py`'s shape, which is better evidence than before but is not an independent client. No app installation, no model behavior, no claim-quality assessment.

### Observations recorded but deliberately not repaired

These were found during the review and judged below the bar for today's batches. They are written down so nobody spends time rediscovering them, and so a decision to leave them is a decision rather than an oversight. None is known to have occurred; each is reasoning from the code plus, where noted, a reproduction.

- **A deeply nested source directory raises `RecursionError`.** `walk` in [ingest.py](src/sci_ai_verifier/ingest.py) recurses per directory level, and Python's default limit is reached before the traversal cap of 2,000 entries. The result is an uncaught exception that [mcp.py](src/sci_ai_verifier/mcp.py) turns into JSON-RPC `-32603` rather than a fail-closed run. It needs a roughly 1,000-level-deep tree, which Windows path limits make unlikely, but the failure mode is the same class as the `KeyError` repaired today.
- **The reparse-point check is broader than symlinks and junctions.** `no_links` rejects every reparse tag, not only the name-surrogate tags that actually redirect. Cloud placeholders, deduplicated files, and similar non-redirecting tags are refused too. This machine's OneDrive folder is not tagged, so nothing was reproduced here, but a submission folder holding cloud-only files would fail. Narrowing the check would loosen a safety boundary, so it should be a deliberate decision, not a quiet fix.
- **A case-only filename collision is fatal for the whole run.** Two files differing only in case, possible on a case-sensitive filesystem, raise `unsafe_source`. That is intentional for cross-platform digest stability, but the run dies rather than reporting the pair.
- **Host-scoped errors carry a thinner envelope than the reviewed common protocol.** The retryable shape returned from `Runtime.call` omits `details`, `refresh_required`, and both budget counters, and uses `scope: "host"`, which is not one of the scopes [tool-contracts.md](skills/scientific-verifier/references/tool-contracts.md) defines. Defensible for a request made before a run exists; undocumented as a shape.
- **Finalization runs just before the event that commits it.** `terminate` and the manifest commit both call `finalize` and then `record`. Today `finalize` only deletes this run's temporary write files, so a failed `record` leaves nothing inconsistent. If finalization ever does more than that, the order must be reversed.
- **A transport-level retry of the same tool call costs illegal-transition budget.** There is no idempotency by request ID; a resent call arrives with a stale token. `get_verifier_context` recovers a lost response correctly, so this only matters if a client retries automatically.
- **`atomic_write` does not fsync the parent directory after the rename.** On a crash the safe direction dominates: a lost event means the transaction was never committed, and a lost object under a committed event is detected and fails closed. Worth one line if durability is ever claimed more strongly.
- **The bootstrap is still about 85 KB in a single tool result.** Much better than 227 KB, but app truncation remains untested. If the live test shows truncation, the next lever is the `Authoritative states and tool results` section of `workflow.md`, which is 7.9 KB and largely later-stage; it was kept so that the Stage 2 profile's reference to "the later-stage matrix below" does not dangle.

### A note on the Stage 2 contract document itself

The user asked what [stage2-contract.md](skills/scientific-verifier/references/stage2-contract.md) is for and whether it should stay one file. My answer, for the record: keep it. It is the only document describing what is actually built, it is mostly subtractive — it states where the general contracts are not true yet — and it is written to be deleted when a restricted host exists. The split is currently clean: `workflow.md` owns the state matrix and says which kinds of limit exist, this file owns the actual numbers, and `runtime-contract.md` section 6 points here rather than restating anything. No duplicated limit value appears in two documents.

Two parts of it sit there only because there was nowhere else. `Stage 3 dependency` describes Stage 3 and should move to its own file when Stage 3 begins. `Integration sources` is a list of URLs consulted while building, which is history rather than contract and would sit better in this log. One judgement call to confirm or reverse: I put the new `MCP compatibility target` section here rather than in `runtime-contract.md` section 6, because it describes what this prototype implements and section 6 already delegates exception detail here. The file grew from 12.5 KB to 18.1 KB today and is pinned into the model's context in full, which is justified while all of it is true but is worth watching.

### Before the next session

- Create the verifier data directory **outside this checkout** before installing. [INSTALL.md](desktop/INSTALL.md) now suggests `D:\Su Lab\verifier-runs`; it does not exist yet. Runs saved inside the repository sit beside the gitignored test workspaces and would be lost to ordinary cleanup.
- Rebuild before installing, because `dist/` is gitignored and its digests changed today. `python scripts/build_desktop.py` then copy the new SHA-256 values into [APP-ACCEPTANCE.md](desktop/APP-ACCEPTANCE.md).
- Two points in today's repairs are worth a reviewer's explicit agreement rather than a skim. `persistence_failure` now reports `run_state` and `committed_state` as null, which departs from the example envelope in the common protocol that always shows a state; the argument is that asserting `incomplete` for a state never read is worse than reporting it unknown. And the writer-lock bound is two seconds, chosen so a contended call returns quickly rather than blocking the conversation; a slow disk snapshotting 200 files could make a legitimate second call see `run_busy`, which is retryable and harmless but will look like contention in a log.

### Urgent next steps, if any

None. The four items that were blocking when this entry was first written are repaired: an equivalent path spelling loads, an unusable configured directory reports one actionable line, an incompatible saved record is rejected without being rewritten, and a healthy run is no longer reported as a durable persistence failure.

Two prerequisites remain for later work rather than for the next step. Adding a real independent MCP client to the test suite would mean a third-party dev dependency and network access during tests; that is a decision for the user, and until it is made the specification-derived check is the stand-in. Verifying the advertised Python 3.11 floor needs a 3.11 interpreter that is not installed on this machine; the floor is currently unverified and both `pyproject.toml` and the manifest still advertise it.

### Suggested next move

The four choices that were open when this entry was written have all been decided by Codex, and the decisions are recorded above and implemented. For the record: equivalent path spellings succeed rather than becoming retryable; the bootstrap pins a named Stage 2 selection and keeps one complete JSON text result; `concurrent_request_rejected` is documented as folded into `illegal_transition`; and unsupported `schema_version` values are rejected outright with no migration.

Review the repairs, which are already published. The changed set is [agent.py](src/sci_ai_verifier/agent.py), [storage.py](src/sci_ai_verifier/storage.py), [tools.py](src/sci_ai_verifier/tools.py), [ingest.py](src/sci_ai_verifier/ingest.py), [mcp.py](src/sci_ai_verifier/mcp.py), [__main__.py](src/sci_ai_verifier/__main__.py), both test modules, [SKILL.md](skills/scientific-verifier/SKILL.md), [the Stage 2 contract](skills/scientific-verifier/references/stage2-contract.md), [manifest.json](desktop/manifest.json), [INSTALL.md](desktop/INSTALL.md), [APP-ACCEPTANCE.md](desktop/APP-ACCEPTANCE.md), and this file. The contract halves changed together in each case, so a reviewer can read the code change and its governing paragraph side by side.

After the repairs are reviewed, the live Claude Desktop acceptance is the next real step, and its record is what establishes the MCP compatibility target. Keep Stage 3 deferred.

### Recommended next action

Review the two published repair batches, then run the live app acceptance against the three fixtures and fill in [APP-ACCEPTANCE.md](desktop/APP-ACCEPTANCE.md), including its new compatibility-target table. Do the two setup steps under "Before the next session" first.

The review is finished when a reader agrees that each of the eight findings is closed by a change whose contract half changed with it, that no new behavior was added beyond the eight, and that the two skipped tests are acceptable as recorded gaps rather than silent ones. The acceptance run is finished when all three fixtures reach their expected Stage 2 outcome in the app, the compatibility-target rows are filled from what the app actually did, and the saved event journals agree with the transcript. Do not add a second MCP protocol implementation, and do not add an independent-client dev dependency, until the record shows one is needed.

## Codex: 2026-09-10

### Current stage and status

Stage 2 retains its recorded app evidence and unresolved conversation-only follow-up. At the user's request to start Stage 3 and prepare the remaining project work, version 0.3.0 now implements claim routing, catalog release verification/cache activation, immutable catalog pins and per-claim evaluator selection. It stops at `stage3_complete` with scientific verification still pending. This supersedes the earlier same-day recommendation to prepare contracts only. The user selected **chemical formula and mass calculations** for the first complete scientific path; its candidate evaluator and review package are prepared, not registered as approved.

### What has been done

- Reproduced remaining compatibility failures: a boolean schema and unknown implementation were silently accepted; a list-valued schema and malformed timestamp raised internal exceptions. Strengthened [saved-state validation](src/sci_ai_verifier/storage.py) before interpretation, covering supported writers, strict schema types, required fields, counters, limits, timestamps, object/context/read references, and reachable Stage 2 states. Unsupported records remain untouched; the fatal response carries the precise cause and null durable state.
- Made malformed readable projections recover from the journal, while retaining the missing-journal-tail check. Non-object journal entries now fail closed. Preserved the distinction between a recoverable summary file and an authoritative event.
- Added a 64-level source-directory bound with a durable operational outcome, and enforced the existing global traversal budget for empty directories as well as files. Kept conservative reparse-point rejection and case-insensitive collision policy. Malformed paths, including an embedded NUL, return a correctable error; bad UTF-8 instruction files produce an actionable startup message.
- Distinguished lock contention from other lock I/O failures. Completed and documented host-error fields with null unavailable budgets. After contention, callers refresh context before rebuilding a workflow request because the other caller may have advanced the token. Confirmed that a two-second lock bound and null unknown state are appropriate for this desktop profile.
- Expanded regression coverage and corrected a misleading minimum-runtime check: it previously accepted 3.12/3.13 as evidence for a 3.11 floor and only bootstrapped. It now requires actual 3.11 and exercises all three tools through an extracted package when available.
- Validation: **47 tests on Python 3.14.0 and again on bundled 3.12.14; 45 passed, two skipped per interpreter.** The skips are the unavailable Python 3.11 interpreter and a physical symlink test requiring Windows privileges; the Windows junction test passes. Complete packaged stdio flow and reproducible archive checks pass. The official cached MCPB manifest validator passes. The assembled bootstrap fixture is 93,249 bytes, below the 120,000-byte regression ceiling; actual app truncation remains untested. Updated [the acceptance record](desktop/APP-ACCEPTANCE.md) without filling any live-test fields.
- Updated [the Stage 2 profile](skills/scientific-verifier/references/stage2-contract.md) and [common tool protocol](skills/scientific-verifier/references/tool-contracts.md) alongside behavior. No workflow legality, scientific meaning, registry content, or legacy implementation changed. Rebuilt installable packages; source changes are local and not committed or pushed in this repair round.
- At the user's request, expanded [the installation and testing guide](desktop/INSTALL.md) with a folder map, separate input/result folders, copyable fixture and resume/cancel prompts, expected artifacts, personal-submission instructions, limits, troubleshooting, and update behavior. Checked Anthropic's current installation and skill-upload documentation. The guide now recommends copying fixtures into `D:\Su Lab\verifier-submissions`, so personal skills can be added beside them without reinstalling. This replaces the earlier first-test setting pointing directly into repository examples. Documented the required path edits if using the older generated manual-config example. Rebuilt packages to include the guide; no folders were created outside the repository and no app setup was performed.
- Investigated the user's first app attempt after Claude reported no verifier tools. Read-only inspection found the installed scientific-verifier extension in Claude's Windows Store app data with `isEnabled: false`. Its three configured paths are correct and present; the installed `agent.py`, `mcp.py`, and `storage.py` match the repaired checkout. Updated [the acceptance record](desktop/APP-ACCEPTANCE.md) with the observed discovery failure. The next step is enabling the extension in Claude and retrying a fresh Chat. The app's separate Add folder permission is not required by this runtime, which reads through its configured submission root. No app settings were edited, no process was restarted, and no substitute verification record was created.
- Later today, verified the user's completed tests and replaced the earlier discovery-blocked status with actual results in [APP-ACCEPTANCE.md](desktop/APP-ACCEPTANCE.md). The extension is now enabled. Its installer hash matches the package used (`1fdc67adad4042279c54ec2fbd81d6e518f98b9b014e4cce0adc6deb543130f1`), and all 21 installed payload files match that archive. The user confirms the visible model label **Opus 5** and that resume occurred in a new Chat; exact model identity remains unavailable.
- Independently checked **four runs, 15 events, and 21 distinct committed objects**: event linkage/digests, token/state/budget consistency, immutable source bytes, prior delivery of exact quotes, claim/manifest identities, projections, finalization, and resume context. All mechanical checks pass, with claim counts 1/0/1/1 for reference/no-claims/conflict/resume. All runs stop at `stage2_complete` with `verification_complete: false`. The audit preserved all 52 managed-data files byte-for-byte and called no runtime controls. See [the machine-readable audit](https://github.com/njdjyxz/sci-ai-verifier/blob/f7293ecec224176688ea90058b068fc01eb8bacc/reviews/stage2-acceptance-2026-09-10.json) for run IDs, paths, event digests, and precise scope. No developer suite rerun or substitute model run was needed for this inspection.
- Recorded one extraction-fidelity follow-up: resumed run `125ceb03-30a0-446a-841c-84138ed0718b` adds an isotope-selection definition to `expected_behavior` that the fixture does not provide. The primary claim and quotation remain correct; this is a source-grounding observation, not a judgment of the definition's scientific truth or a resume/storage failure. Preserve the original manifest and tighten guidance before treating that extra definition as a submitted requirement. The conflict manifest's self-report that no outside tools were used is not independent evidence; the user is unsure how to identify such calls, and no matching local transcript was available. That one app-behavior check remains pending.
- Product direction clarified in the intervening discussion: the user wants one public **verify this skill** action, with claim extraction and other stages kept internal rather than offered as standalone features. The long prompts are development acceptance instructions. Restart-first recovery was discussed as a simplification; no resume/cancel function was removed and no public-interface redesign was implemented. The existing Stage 3 scope covers routing and catalog lookup only; evaluation planning/execution, assessment, and reporting require additional implementation phases before full verification is available.

- Implemented the dedicated [Stage 3 contract](skills/scientific-verifier/references/stage3-contract.md) with matching state/tool and artifact updates. New desktop runs use Stage 3; Stage 2 remains an explicit operator profile and older completed runs are never reopened. Tightened extraction guidance so absent behavior/scope stays `Not specified`, including isotope conventions; preserved all original app manifests.
- Added [catalog verification](src/sci_ai_verifier/catalog.py), [routing](src/sci_ai_verifier/routing.py) and the [release utility](scripts/catalog_release.py). Downloads use this project's fixed GitHub repository, exact commit and independently supplied manifest digest; assets/interfaces are verified before activation, offline caches require exact receipts, and active runs use immutable objects. No model-triggered downloads or runtime writes to reviewed registries exist. Initial `catalog/` mirrors the empty reviewed registries; it is local and unpublished.
- Added three routing tools, atomic complete-manifest assignment, run-local provisional types, strongest-grade lookup, registered preference, A-C interface pairing and D fallback without a runner. Missing implementations/runners produce distinct claim-local operational artifacts while other claims continue. Lookup results are bounded, carry exact version/resource pins and never produce a scientific verdict.
- Prepared [the chemical mass pilot](https://github.com/njdjyxz/sci-ai-verifier/blob/f7293ecec224176688ea90058b068fc01eb8bacc/reviews/CHEMICAL-MASS-PILOT.md), three provisional type definitions, two provisional capability descriptions, NIST isotope reference values, a narrow candidate formula parser and per-trial numeric scorer. Boundary, known-answer and deliberately wrong-observation tests pass. These helpers are not installed, approved or connected to a subject runner; no submitted skill has been evaluated by them.
- Added [the full-project completion checklist](https://github.com/njdjyxz/sci-ai-verifier/blob/a8d6045657c5a2a10fdfb4f9ec139f60b73e31f2/reviews/PROJECT-COMPLETION.md) and [0.3.0 installation guide](desktop/STAGE3-INSTALL.md), refreshed README and built the MCPB/skill ZIP. The single public action remains **verify this skill**; extraction and routing are internal steps. No installed app settings, original app data or legacy files were changed.
- Validation: the expanded suite contains **77 tests; 75 passed and two skipped** on Python 3.14 and bundled Python 3.12. The skips remain actual Python 3.11 availability and privileged symlink creation. Both extracted-package profiles and archive reproducibility pass. The new reader's compatibility validator also accepts the four original 0.2.0 app journal states through a read-only inspection; this is not a new live resume test. See [Stage 3 validation](https://github.com/njdjyxz/sci-ai-verifier/blob/f7293ecec224176688ea90058b068fc01eb8bacc/reviews/stage3-validation-2026-09-10.json) for precise evidence and limits.
- All Stage 3 source and documentation changes remain local, uncommitted and unpushed. Remote transport success is fixture-tested; no newly published GitHub catalog or live 0.3.0 app test is claimed. Maintainer/scientific review of the seed collection remains required before promotion.

### Contract organization and lifecycle

Claude's note recommends keeping **the Stage 2 profile itself as one file**; it does not recommend merging every contract. Retain separate workflow, tool, runtime, artifact, resource, and evidence documents because they answer different questions. Link shared rules instead of copying them. The Stage 2 contract is the active implementation profile, including scope, exceptions, limits, persistence, and compatibility; it is not a throwaway development file.

Clarification of Claude's proposed deletion condition: a restricted host alone does not make this contract disposable. Revise or replace it only when the next reviewed profile covers its still-applicable guarantees and explicitly handles existing saved runs. Stage 3 planning belongs in a dedicated reviewed catalog/routing contract once that work starts; move the existing dependency paragraph then. There is no benefit to a broad document merge during final Stage 2 repair.

### Urgent next steps, if any

No local routing implementation blocker. Before claiming a complete scientific verifier, review/promote the candidate chemical catalog, identify the actual submitted skill and approved subject invocation boundary, and implement planning, resource locks, audit, isolated execution, independent assessment where required, and reporting. The reviewed registries currently contain no evaluator or subject runner. The initial catalog is not published, and 0.3.0 has not been installed/tested live.

Preserve the earlier limitations: instruction-conflict Chat tool activity remains uninspected; exact model identity is unavailable; cancellation/personal submissions were not tested live; Python 3.11 and an independent MCP client remain unverified. No automatic retransmission idempotency or full power-loss durability is claimed.

### Suggested next move

Review the [chemical mass pilot](https://github.com/njdjyxz/sci-ai-verifier/blob/f7293ecec224176688ea90058b068fc01eb8bacc/reviews/CHEMICAL-MASS-PILOT.md) and [completion checklist](https://github.com/njdjyxz/sci-ai-verifier/blob/a8d6045657c5a2a10fdfb4f9ec139f60b73e31f2/reviews/PROJECT-COMPLETION.md), then connect the first scientifically reviewed evaluator to a controlled subject runner through the existing plan/audit contracts. Keep Stage 3 acceptance separate from scientific performance. The earlier suggestion to rerun Stage 2 fixtures remains superseded by their recorded evidence.

### Recommended next action

Review the concrete Stage 3 implementation and candidate chemical scope/fixtures, then run the packaged 0.3.0 short-prompt acceptance in a fresh Claude Desktop Chat. Confirm exact catalog pins, source-grounded routing, per-claim operational outcomes, and resume preservation. In parallel with that human evidence, the next implementation boundary is `commit_evaluation_plan` plus revision-bound resource locks for the chosen chemical mass pilot. A complete scientific test begins only after the subject runner and reference/scoring policy are reviewed and auditable; a routing checkpoint is never a finished report.

## Codex: 2026-09-11

### Current stage and status

**Latest user direction:** retire `codex/general-skill-demo`, resume unfinished work,
audit this plan, and build the personal/local first version on `main`. This
supersedes today's earlier demo-first branch/publication recommendation.

Version 0.6.0 implements a bounded local engineering release: one public
**verify this skill** action; Claude Code's native planner/tool loop; fresh
restricted Claude Code subject sessions; local reference discovery, mechanical
candidate qualification and offline reuse; immutable observations and reports.
The implementation scope for this increment is plain text skills and installed
exact/numeric reference comparisons. These provisional methods produce comparison
outcomes, not scientific status or grades. Full scientific qualification, executable
methods, and GitHub contribution/release automation remain later work.

The approved design still requires temporary recognized skill loading and explicit
invocation, separation of candidate/subject/publication storage, configurable
subscription or API authentication, hidden-answer exclusion, exact version pins,
and honest unsupported outcomes. No live acceptance is claimed: this environment
has Python 3.14 but the initial check found no native Claude executable, and the
prior decision deferred model usage. Fixture evidence is not a live model run.

### What has been done

Earlier today, completed the bounded chemical workflow through reports and the
same-chat 0.5.0 demo, with 124 tests and historical package validation. Published
that implementation on `codex/general-skill-demo` at `d4f2119`, while main at
`72abc24` received only the roadmap. The subsequent uncommitted approved details
about temporary loading, storage separation and authentication were preserved
before integration. Those earlier implementation and app-acceptance records remain
historical evidence, not evidence for the new CLI runner.

Current work:

- Audited the code, contracts and branch differences in [the local v1 audit](https://github.com/njdjyxz/sci-ai-verifier/blob/a8d6045657c5a2a10fdfb4f9ec139f60b73e31f2/reviews/LOCAL-V1-AUDIT.md). Integrated the useful Stage 3, chemical and demo history onto main without losing the local plan revision. Final branch/commit disposition is recorded with validation below.
- Reconciled the [local contract](skills/scientific-verifier/references/local-contract.md), workflow/tool matrix, artifact/runtime/resource policies, skill, README and project instructions before and alongside implementation. Removed the obsolete human-only local candidate requirement.
- Added a public CLI and one-tool MCP interface, a run-bound private MCP server, and a native Claude Code adapter. Python validates and executes bounded operations; Claude Code retains the model/tool loop. The subject receives only its pinned skill and fixed input, with a recognized temporary plugin, explicit successful Skill invocation evidence, and separate requested versus observed model identity.
- Implemented isolated configuration outside subject-readable directories, a fresh repository boundary, CLAUDE.md exclusions, disabled hooks/memory/dynamic skill commands, restricted tool sets, allowlisted credential environments, process time/output limits, and cleanup. Subscription tokens and API keys are never copied into saved verifier configuration or passed as command arguments.
- Added public HTTPS reference retrieval, immutable quote-backed exact/numeric candidates, positive/negative/boundary controls, per-claim selection before execution, local reuse, raw request/observation receipts, interruption without replay, and JSON/Markdown reports. Mechanical qualification explicitly leaves scientific authority, applicability and representative coverage unresolved.
- Preserved historical saved-run compatibility and kept reviewed global registries, old app evidence and legacy source intact. Added [local setup instructions](LOCAL-INSTALL.md), a checkout launcher, and an isolated synthetic fixture that cannot seed a live candidate pool.

Final automated validation: **151 tests, 149 passed, 2 skipped, 0 failures** on
Python 3.14 (49.300 seconds). The skipped checks are an actual Python 3.11
interpreter and physical symlink creation privileges; Python 3.11 syntax and
Windows junction rejection pass. Real child-process deadline, output-ceiling and
descendant cleanup tests pass, as do public-to-private MCP subprocess acceptance,
lost planner-response recovery, offline candidate reuse and historical packages.

Built the editable local source package (`dist/scientific-verifier-local-0.6.0.zip`)
and ran its extracted synthetic fixture. This exposed a Windows long-path issue;
short stable claim-directory names fixed it, and the extracted run now completes.
The final saved fixture has 9 journal events, 24 verified objects and 3 passing
reference comparisons, with null scientific grade. Reports now show fixed inputs,
expected values, actual outputs, references and outcomes directly. Syntax,
active-document links and formatting checks pass. Exact evidence is in
[local validation](https://github.com/njdjyxz/sci-ai-verifier/blob/f7293ecec224176688ea90058b068fc01eb8bacc/reviews/local-validation-2026-09-11.json).

Committed the validated integration on main as `a8d6045`, with both prior main
`72abc24` and demo `d4f2119` as merge parents. Removed the local demo branch after
confirming its history is reachable from main. The official cached MCPB 2.1.2
manifest validator also passes. After automatic approval review initially required
explicit publication authorization, the user approved publishing and remote demo
deletion. Pushed `a8d6045` to `origin/main`, deleted the remote demo branch with
an exact-tip lease, and verified that main points to the integration and the demo
branch is absent remotely. Both local and remote demo branches are now retired;
their complete history remains reachable from main. This documentation update
records the completed publication. Generated local archives remain gitignored.
No live model, scientific registry approval, GitHub evaluator contribution or
scientific grade has been produced.

After the user requested a beginner-friendly desktop setup guide, rewrote
[LOCAL-INSTALL.md](LOCAL-INSTALL.md) around the Code tab, a one-time Windows
installation, an encrypted desktop environment entry for the subscription token,
and a copyable personal MCP registration command with a credential placeholder.
Clarified that this implementation requires the standalone native CLI as its
execution dependency while allowing the desktop app as the everyday interface.
Added expected results, first-use/report instructions, troubleshooting, and a
separate optional PowerShell path; updated the README entry point. Checked the
current official desktop/setup/MCP documentation against the local adapter.
The prior publication log is committed locally as `c3c0cd0` and is not pushed;
these guide refinements are local and uncommitted. Live desktop/model acceptance
remains unperformed. No account settings, credentials or installed apps were
changed during this documentation revision.
Documentation validation: all 8 PowerShell blocks parse, 126 local Markdown links
resolve, and whitespace checks pass. The read-only setup check still returns
`claude_unavailable`. Rebuilt the local source ZIP with the revised guide and
checked archive integrity and packaged source/document bytes; runtime code is
unchanged, so the previous automated test results remain the implementation
evidence rather than a new live acceptance claim.

### Urgent next steps, if any

No additional scientific catalog authoring is required to start local discovery.
Live use requires a native Claude Code installation with the supported restricted
mode and a user-supplied subscription token or API key with available usage.
Credentials remain user setup; do not retrieve them from saved account files.
The native CLI's actual invocation/tool boundary still needs live acceptance.

### Suggested next move

Run a short personal text skill through the local public action when Claude usage
is available. Inspect explicit pinned-skill invocation, actual model/session IDs,
reference provenance, hidden-answer exclusion, interruption and the final report.
Then qualify a narrowly defined scientific method independently and connect its
approved grading policy. Expand subject tools only with an enforced execution
boundary suitable for the submitted code.

Keep the approved broader contribution lifecycle as a subsequent increment:
lookup, discover missing material, build a local candidate, qualify against
independent reference/negative/boundary evidence, prepare an authorized GitHub
contribution, and register an immutable version only after its policy checks pass.
Unknown or non-redistributable licenses allow no automatic public resource copy;
publication failure must retain local evidence for retry without rerunning subjects.

### Recommended next action

Install/configure the native Claude Code dependency and perform the first live
local acceptance when eligible usage is available. Branch integration, publication
and demo retirement are complete. Live acceptance
is finished only after a real submitted skill is invoked in a fresh Claude Code
session and the saved report/receipts are independently inspected. It is not
established by the deterministic fixture or a successful package build.

## Codex: 2026-09-11 19:32 PDT

### Current stage and status

**User-authorized additional same-day entry.** The user explicitly approved a new
log entry, removal of the narrow goal files, and publication of these changes to
the existing GitHub remote. This is the permitted exception to the one-entry-per-day
rule. It supersedes the earlier text-only, chemical-only and demo completion
boundaries; it does not rewrite their historical test evidence.

**Completion target:** finish the personal/local scientific verifier on `main`,
using the user's installed Claude Code CLI, the desktop app's Code tab and Claude
subscription. The public action remains **verify this skill**. Claude owns the
planner/tool loop; local Python owns execution boundaries, state, evidence and
reproducible scoring. An Anthropic API key is optional. A hosted multiuser service,
accounts, subscriptions for customers and server deployment are a separate project.
Local operation still uses hosted Claude inference and the user's eligible usage.

The project is **incomplete**. Version 0.6.0 supplies a functioning engineering
foundation, not the complete requested local product. Source snapshots, journals,
local discovery, exact/numeric comparisons, process limits and reports exist.
The older chemical profile also supplies reusable planning, resource locks,
bundle validation, audits, repeated-trial scoring and grade-policy machinery.
Those parts must be integrated and extended through the actual local public entry;
a feature in an old profile or a passing replay fixture is not local completion.

This entry is the single project completion roadmap. Runtime contracts continue
to describe only implemented, enforceable behavior until code and contract changes
land together. Do not remove truthful limitations, issue unsupported grades, or
call a milestone the finished project because its narrower tests pass.

### What has been done

- Removed `reviews/LOCAL-V1-AUDIT.md` and `reviews/PROJECT-COMPLETION.md`, which
  presented narrow releases as completion boundaries. Their history remains in Git.
- Updated README, project instructions and the setup guide to point to this roadmap.
  Retained the current local runtime contract as implementation documentation, with
  its reduced scope clearly identified as unfinished work. Updated the Stage 3
  roadmap reference. Historical log links point to the preserved old revisions.
- Preserved the earlier beginner-friendly Windows guide changes and the pending
  publication-validation log commit `c3c0cd0` for inclusion in the requested push.
- Audited the remaining work against the full workflow, evidence rubric, local
  adapter, candidate code and older scientific profile. No missing runtime
  capability is implemented by this documentation change.
- Validation and publication for this change are recorded below after the checks.

### Remaining implementation and integration work

Every item below is required to close the full local roadmap. Check individual
acceptance criteria with saved evidence; do not use a single chemical example as
proof of general skill support. External applications and scientific domains need
explicit capability/coverage records, not an impossible promise of universal
support. Additional app adapters or new domain research discovered during actual
submissions must be recorded as remaining work rather than silently excluded.

1. **Unify the local workflow and its configuration.** Connect routing, registered
   evaluator lookup, planning, resource resolution, bundle qualification, audit,
   execution, assessment and reporting behind `verify_skill`. Reuse tested older
   modules instead of creating another parallel workflow. Reconcile tool/state and
   artifact contracts together; preserve old runs and explicit historical profiles.
   Provide explicit model/authentication, requested/minimum grade, execution/tool
   permissions, trial and resource limits, and data locations with usable defaults.
   **Acceptance:** new, reused, repaired, downgraded, empty-claim and mixed-outcome
   runs all reach the appropriate report through the public local entry, with no
   manual invocation of internal tools and no unsupported branch advertised as live.

2. **Execute real computational skills.** Support skill folders containing scripts,
   supporting text, structured data and binary assets; retain original source and
   transformation identities. Discover and provision declared dependencies with
   pinned versions. Run the recognized submitted skill in fresh sessions; collect
   generated files, actual commands/tools, model/session identity and raw outputs.
   Establish an enforceable Windows execution boundary for shell, filesystem,
   subprocess and network access; assess the available native/container/VM options
   before choosing one. Temporary directories and process-tree cleanup alone are
   insufficient confinement for arbitrary code. Keep expected answers, evaluator
   code and credentials outside subject-accessible execution and artifacts.
   **Acceptance:** real scripted skills produce traceable output artifacts; attempts
   to escape directories, read hidden answers/credentials, invoke undeclared tools,
   or outlive cancellation are rejected and recorded without corrupting other runs.

3. **Complete resource and external-tool handling.** Extend public text retrieval
   to local and downloaded datasets, supported structured/binary formats, archives,
   reference implementations and scientific resources. Validate extraction paths,
   file/size limits, schema, units, columns, provenance, versions, licensing and
   answer/input separation before use. Distinguish reference-acquisition access
   from the submitted skill's own network/app access. Add capability-driven local
   tools and external-app connections, with operator-configured credentials and
   permissions; record unavailable installations/services explicitly.
   **Acceptance:** evidence can be materialized and pinned from both local and
   remote sources, reused offline when permitted, and rejected with precise reasons
   when corrupted, incompatible, unauthorized or scientifically mismatched.

4. **Build and qualify missing evaluators.** Implement the approved lifecycle:
   lookup first, discover missing material, create a local candidate, qualify it,
   then reuse an immutable version. Extend beyond the two installed comparisons to
   generated/configured checking code, benchmark transforms and reference methods.
   Separate candidate generation, subject execution, reference answers and the
   qualification environment. Record source authority/applicability, independence,
   units, uncertainty, scope and coverage. Exercise positive, negative, boundary
   and held-out cases against independent references; include intentionally faulty
   evaluators to verify rejection. Source quotation and agent self-approval alone
   cannot establish scientific suitability. Preserve qualification failures.
   **Acceptance:** a missing method can be constructed, independently checked and
   reused without a manually authored seed; rejected candidates cannot acquire
   scoring authority or silently enter the reviewed registry.

5. **Complete planning, audit and repeated sampling.** Pin test design, versions,
   reference resources, case counts, trial counts, tolerances, metrics, aggregation
   and grade eligibility before observing subject answers. Replace the local
   one-trial constant with audited claim-specific policies. Apply scope/fairness,
   leakage, coverage and resource audits; invalidate affected downstream work on
   revision. Score each trial before aggregation and retain missing/invalid trials
   and their denominators. Implement legal repair, reselection and downgrade paths.
   **Acceptance:** recorded samples and policies reproduce decisions; stale plans,
   changed resources, biased selection and post-result threshold changes cannot
   authorize execution or improve a grade.

6. **Finish scientific assessment and reports.** Connect supported A/B/C evidence
   designs to deterministic checks of their eligibility and verdict rules. Implement
   an independent documentary assessment path for D, using an identified separate
   assessor session or provisioned assessor with a bounded evidence packet and
   rubric, excluding the planner conversation. Implement the no-acceptable-evidence
   U path and operational-failure distinctions. Record scientific qualification
   evidence for actual methods; synthetic approvals cannot establish it. Report
   scope, coverage, variance, uncertainty, requested/achieved grades, downgrades,
   AI involvement and limitations without inventing an overall skill grade.
   **Acceptance:** valid and invalid evidence designs exercise A/B/C/D/U and
   operational outcomes correctly; the planner cannot grade its own packet or
   override deterministic decisions. Real scientific results retain inspectable
   qualification evidence, not only a final letter.

7. **Finish local/shared evaluator lifecycle integration.** Connect the existing
   versioned GitHub catalog retrieval/cache code to the local public workflow.
   Support compatible updates, retired versions and exact version pins without
   altering active runs. Complete opt-in preparation/submission of qualified
   candidates, review/qualification gates, authorized promotion and catalog release
   handling for the existing repository. Separate personal evidence from publishable
   material; enforce license, attribution and secret/private-data exclusions.
   Publication failure must retain a retryable prepared submission without rerunning
   subject trials. Local verification must work without publishing anything.
   **Acceptance:** discovery-to-local-reuse and authorized contribution-to-versioned-
   retrieval both work; offline, rejected, conflicting and failed-publication paths
   preserve evidence. This lifecycle belongs to the local roadmap and does not
   require a hosted API product. This planning push does not authorize future
   publication of arbitrary user submissions or private resources.

8. **Record the complete observable workflow.** Add automatic per-attempt/per-run
   logs starting before preflight, with timestamps, stage start/end/duration,
   visible planner searches/tool calls, candidate choices, references, trial inputs
   and outputs or artifact links, process exits, errors, cancellation and completion.
   Preserve partial logs on failure; provide a readable timeline plus structured
   records and useful progress through the public interface. Derive state/results
   from authoritative records rather than a second conflicting state store. Redact
   credentials before persistence and keep logs outside subject-readable space.
   **Acceptance:** a setup failure, stalled search, failed test and interrupted run
   each leave enough evidence to identify where execution stopped. No access to
   private model reasoning or unrelated app activity is claimed.

9. **Harden lifecycle and recovery across the expanded path.** Carry budgets and
   deadlines through planner, downloads, dependencies, subject, evaluator and
   assessor processes; reserve capacity for reporting. Account for model usage
   without treating an estimate as a guaranteed bill. Enforce concurrency/state
   ordering, integrity validation and no replay of uncertain observations. Preserve
   completed evidence after lost responses; finalize scratch, retained resources
   and cleanup warnings on success/failure/cancellation. Provide restart-first
   behavior with clear saved-run outcomes, credential renewal and usage exhaustion.
   **Acceptance:** meaningful fault-injection tests cover network loss, crashes,
   corrupted data, disk/write failures, interruption, stale state and exhausted
   budgets without false completion, scientific failures invented from operational
   errors, secret leakage or surviving child processes.

10. **Complete installation, compatibility and live acceptance.** Make setup work
    from a clean checkout/package with resolved Python/CLI paths, subscription
    token setup, optional API mode, one desktop tool connection, dependency checks,
    repairable configuration and readable errors. Package the needed code/contracts
    and dependency information; preserve upgrades and uninstall/user-data choices.
    Reconcile guides and version labels with actual capabilities. Validate the
    stated minimum Python version and actual MCP/CLI/desktop behavior. Use a
    maintained corpus of real personal skills covering text, computation, generated
    artifacts, resource acquisition, candidate discovery/reuse and documentary
    assessment, including deliberately wrong and adversarial cases. Inspect saved
    reports, model/tool invocation and provenance independently after real runs.
    **Acceptance:** the packaged product passes the corpus through both CLI and
    desktop entry points, including cancellation/restart and missing-dependency
    cases. Tests of mocks, replay fixtures or an older app profile cannot substitute
    for live acceptance. Record remaining domain-specific unsupported capabilities
    and distinguish them from defects in the promised general workflow.

### Effort estimate and dependencies

This is a rough engineering-effort estimate for the remaining integrated project,
not a promise about chat duration, model throughput, token usage or calendar time.
It assumes reuse of the existing journal, workflow and scientific modules, access
to representative personal skills, and no new scientific research or bespoke
integration for an unlimited number of external applications.

| Workstream | Estimated hands-on engineering hours |
| --- | ---: |
| 1. Workflow/contracts/configuration integration | 6-10 |
| 2. Computational skill execution and isolation | 20-36 |
| 3. Resources, dependencies and tool/app connections | 12-24 |
| 4. Evaluator construction and qualification | 20-36 |
| 5. Planning, audit and repeated sampling | 10-16 |
| 6. Scientific assessment and reporting | 12-20 |
| 7. Catalog reuse, contribution and release integration | 12-20 |
| 8. Observable workflow logging | 6-10 |
| 9. Reliability, interruption and recovery | 10-18 |
| 10. Packaging, compatibility and live acceptance | 12-22 |
| **Base total** | **120-212** |

Allowing roughly 25% for integration and test-discovered rework gives a planning
range of **150-270 engineering hours**, approximately **4-7 full-time engineering
weeks** for one developer. Confidence is low-to-medium until the first real CLI
run and an executable-skill isolation prototype are tested. AI assistance may
accelerate implementation, but cannot eliminate model execution, validation or
scientific qualification. Work can continue across implementation/testing turns
in this project; the estimate is not a commitment to unattended future work.

The largest uncertainties are Windows confinement/dependency behavior, independent
scientific qualification, current CLI/desktop interoperability, and the actual
skills/apps in the acceptance corpus. Waiting for subscription resets, user login,
external review, installations or access is additional elapsed time. Re-estimate
at each tested milestone; do not reduce scope silently to meet the estimate.

### Urgent next steps, if any

The most recent preflight could not find a standalone Claude executable. Obtain
an actual native CLI/version check and user-controlled subscription sign-in before
live acceptance; never extract saved account credentials. Inventory the intended
personal skill corpus and installed scientific tools early, then choose and prove
the execution boundary. Unknown application requirements and scientific coverage
remain explicit estimation inputs, not reasons to replace the goal with another
narrow release. Contract/integration and logging work can proceed while these
inputs are resolved.

### Suggested next move

Implement in reviewable milestones that build toward the whole target: first
establish the live local entry and logging, then computational execution/resources,
then evaluator construction/audit/sampling/assessment, then catalog lifecycle and
final package acceptance. Bring fault tests and documentation forward with each
change. Early successful examples are checkpoints only; they do not mark the full
project complete or exempt the remaining checklist.

### Recommended next action

After this requested documentation publication, begin workstreams 1, 8 and the
initial acceptance checks from 10: map existing scientific modules into the local
entry, record a complete attempt timeline, and establish one real desktop/CLI
run. Use that evidence to finalize the execution boundary for workstreams 2-3.
This turn's authorized deliverable is the roadmap cleanup, new entry, estimate
and remote publication; it does not claim the listed implementation is done.
The user subsequently instructed continuation into implementation after this
publication. Continue against the complete checklist; update this same entry
with actual progress and validation rather than creating another reduced goal.
The user will perform live acceptance manually and asked for the installation
instructions to be updated accordingly. Implement and verify the code with
automated tests, provide a clear manual acceptance procedure, and leave live
CLI/desktop and scientific acceptance explicitly pending until the user's
results are inspected. Do not install apps, change sign-in settings or request
their token to perform those tests on the user's behalf.

### Validation and publication of this entry

Initial checks resolved all 213 local links across 30 Markdown files and passed
whitespace validation. A clean-terminal test run exposed an existing import-path
dependency in the three newer test modules; aligned their source-path setup with
the older tests so the documented command does not depend on inherited PYTHONPATH.
The corrected full command passes **151 tests: 149 passed, 2 skipped**, in
51.476 seconds. The skips are the unavailable Python 3.11 interpreter and
privileged physical-symlink creation. Runtime source is unchanged in this
publication; the test import repair makes the existing checks runnable from a
clean terminal. The rebuilt local package passes CRC/source checks and excludes
both deleted goal documents. These are automated checks, not live acceptance.
The user explicitly authorized pushing this
change set, including the prior guide refinements and pending log, to
`https://github.com/njdjyxz/sci-ai-verifier` on `main`. Report the final commit and
remote verification after publication. No runtime feature, credentials, account
settings, installations or shared scientific registry entries are changed here.

## Codex: 2026-09-12

### Current stage and status

Implementing the complete local roadmap on `main` as requested after the planning
publication `ec45894`. Version 0.7.0 connects computation, resources, evaluator
construction, repeated trials, scientific eligibility, independent documentary
assessment, catalog reuse and workflow logs. Implementation, documentation and
automated validation are ready for the user's manual acceptance. This entry
accompanies the 0.7.0 source publication; the final handoff records its commit
and remote verification.
The user will perform real CLI/desktop, Docker and app acceptance manually;
automated fixtures do not establish that acceptance or scientific validity.

### What has been done

- Added operator configuration, pinned Linux containers for scripts and binary
  artifacts, bounded resource import/download and trusted read-only app adapters.
  Text subjects use a private file reader; computational subjects use private
  container tools. Submitted code has no native host shell tool.
- Added generated Python evaluator controls, immutable test plans, repeated
  observations, per-trial scoring and A/B/C eligibility bound to independent
  reviews of exact source, environment, model and method pins. Added a separate
  documentary assessor and explicit unverified/operational outcomes. Default
  generated methods remain ungraded until real independent review exists.
- Added redacted, bounded observable workflow timelines, hash-chained events,
  partial reports, artifact receipts and interruption recovery. Private model
  reasoning and unrelated app activity are not recorded.
- Added exact-digest catalog import/export, offline reuse and retryable opt-in
  draft proposals. Completed reviewed release envelopes, explicit promotion,
  version/runtime compatibility, full inventories and retirement. New runs pin
  the chosen release and fresh requalification receipts; updates cannot alter an
  active run. No scientific contribution has been published.
- Added public MCP progress and cancellation while a request is running, one
  active request per connection, connection-close cleanup and a total attempt
  deadline. Tests exercise actual child processes and the private text reader's
  stdio transport; no Claude or Docker behavior is simulated as live acceptance.
- Updated [installation](LOCAL-INSTALL.md), [configuration](LOCAL-CONFIG.md),
  contracts and packaging. The install guide includes the user's manual acceptance
  procedure. No apps were installed, credentials changed or real model calls made.
- Final completed full suite: **189 tests, 187 passed and 2 skipped**, in 60.585
  seconds. The skips require Python 3.11 and physical symlink privilege. Tests
  include repeated trials, binary output/scorer/report integration, no-grade
  synthetic evidence, catalog qualification/release/retirement/offline/conflict
  paths, interrupted publication, isolated app working directories, malformed
  controls and cancellation, including the final catalog receipt preservation
  change. All **223 local links across 32 Markdown files** resolve. Python 3.11
  syntax parsing passes for 64 Python files; this does not replace testing with
  that interpreter. The 120-entry source ZIP passes CRC and normalized source-byte
  equality checks and excludes local evidence, credentials, caches and legacy tmp.
  From an extracted package, CLI help, catalog maintenance help and the complete
  synthetic verification fixture pass. Whitespace checks pass. The source ZIP
  and its SHA256 record are in gitignored `dist/`; publication contains source
  and the reproducible builder, not personal evidence.

### Urgent next steps, if any

None requiring user input for implementation. Live acceptance later requires the
user's installed native Claude CLI, Linux Docker engine and actual skills/apps.
Apps without the documented read-only adapter need a specific adapter; independent
scientific review must come from actual evidence and a qualified reviewer.

### Suggested next move

Publish the validated package/source and begin the user's manual acceptance
procedure. Preserve the ten-workstream roadmap and distinguish implemented
mechanisms from pending live acceptance and domain-specific integrations.

### Recommended next action

The user follows [the manual acceptance table](LOCAL-INSTALL.md#your-manual-acceptance-tests)
and supplies observed failures or report/log paths for inspection. Actual app
adapters, installed scientific dependencies and independent reviews must match
the user's real workload. Acceptance remains pending until those results are
inspected; no universal domain coverage or real scientific approval is claimed.

## Codex: 2026-09-14

### Current stage and status

Version 0.7.0 remains at manual acceptance. The user requested clearer upgrade
instructions. An explanatory question about text-only operation was mistakenly
expanded into alternative installation instructions. Following the user's
correction, the guide retains one Docker setup path and the requested upgrade
instructions.

The first user-run glycoengineering acceptance attempt completed its planner but
obtained zero subject observations because the internal tool server lacked model
credentials. A local credential-handoff correction is implemented; the user's
fresh desktop rerun is still needed to establish live subject/assessor execution.

### What has been done

- Expanded [upgrade instructions](LOCAL-INSTALL.md#updating-or-removing-the-connection):
  keep dependencies, project/settings and reports; disable obsolete verifier
  components; replace the connection only when its configuration changes; restart
  into a fresh local Code session.
- Removed the optional Docker discussion and alternative connection, doctor and
  verification commands. The guide consistently prepares Docker and passes its
  settings file. Retained the reminder that the configuration helper does not
  overwrite existing settings.
- Validation passed after the correction: 226 local links across 32 Markdown
  files, syntax parsing of all 10 PowerShell command blocks, whitespace checks,
  and CRC/source-byte checks for the rebuilt 120-entry local package. Live
  acceptance remains the user's tests.
- Inspected attempt `4bfdf075-cadc-46ef-b1f9-3df3b4322ae6`, run
  `6bd0d78d-0b5e-4364-bf93-161c485fd15e`: the credential-presence preflight passed
  and the planner completed a real 768.7-second session, but the subject and
  documentary assessor reported `authentication_required`. The original report
  and logs remain intact. This locates the failure after planner authentication;
  it does not establish that the user's subscription token was absent globally.
- Fixed the private MCP configuration to explicitly forward the selected model
  credential and configured app credentials through environment-variable
  references. On-disk configuration contains no credential values. Restricted
  execution and the subject's tool and environment restrictions remain enabled.
- Corrected the launcher regression test, which previously gave the private
  server the entire planner environment. It now models a safe baseline plus
  configured MCP environment expansion and probes a real child process. It
  reproduced the missing-credential failure before the fix and passes afterward
  for subscription/API modes, configured app credentials, unrelated-credential
  exclusion, secret-free artifacts and recovery without replay.
- Added separate troubleshooting guidance for missing credentials before the
  planner starts versus missing credentials in nested subject/assessor sessions.
  Unassigned scientific grades still require actual independent review. The two
  reported source-scope/citation gaps remain findings to assess on a live rerun;
  no submitted skill or scientific approval was changed to force acceptance.
- Full regression suite after the handoff fix: **189 tests, 187 passed and 2
  skipped**, in 67.228 seconds. The skips still require Python 3.11 and physical
  symlink privilege. The focused regression demonstrated the failure before the
  fix; these checks do not use live model credentials or establish live acceptance.

### Urgent next steps, if any

Restart Claude fully and repeat the user's glycoengineering test from the skill
directory with the corrected local source. Retain the existing connection,
token, Docker settings and failed report. Live nested-session authentication is
not proven by the offline regression check.

### Suggested next move

Confirm that the new run obtains real subject observations and completes the
independent documentary assessments. Address any remaining resource or execution
failure from its actual error before proceeding to the other four example skills.

### Recommended next action

Use the existing `verify_skill` connection in a fresh local Code session, submit
the complete glycoengineering folder, and inspect the new report/log paths.
Scientific grade authorization and source corrections are separate from repairing
the authentication handoff; neither should be invented during troubleshooting.

## Claude: 2026-09-15

### Current stage and status

Version 0.7.0 still awaits manual live acceptance. This session was a requested
repair and full code review of the working tree. Three design defects were fixed,
dead files were removed, and the review findings below are recorded with what was
changed for each. Nothing here establishes live or scientific acceptance.

The largest correction is conceptual. Grade assignment previously required an
operator to enter a human review record, so with the shipped empty defaults **every**
local run produced `evidence_grade: null`: the product could not deliver its own
output. The grade is now what the user designed it to be, an indicator of how
gold-standard the evidence is, settled by the runner's own recorded facts and an
independent critique. No human sign-off assigns a grade anywhere.

### What has been done

**1. The grade is negotiated, not authorized.**

- Rewrote [local_science.py](src/sci_ai_verifier/local_science.py) around
  `evidence_ceiling`, which derives the strongest supportable grade from facts Python
  recorded itself: whether each expected answer came from reference bytes Python
  retrieved over public HTTPS (`origin`, now stored on every reference record) or
  from an operator-pinned dataset, whether the scorer is an installed comparison
  method or planner-authored code, whether the expected value is a complete token of
  its quote rather than a substring, the distinct case count, and the trial count.
  Previously A, B and C were indistinguishable in code: `decide` simply picked the
  strongest letter a human review had listed, so the rubric's actual distinctions
  were documented and unenforced.
- `select_local_candidate` now takes `target_grade` and five justification fields and
  runs the loop the user specified: propose, critique, revise, settle.
  `documentary.critique` runs a fresh no-tool session that never saw the planning and
  may only lower the grade. Disagreement returns `local_grade_revision_required` with
  the objections and required revisions. Every round's audit is kept in
  `negotiation_refs`.
- Following the user's review of that first design, the negotiation was tightened in
  this same session. The user identified that a fresh critique sees nothing from
  earlier rounds, so the loop terminated on a counter without converging on anything:
  each round's reviewer could object on new grounds, and the final grade was whatever
  the last one happened to say.
  - **One proposal is legal per design.** `proposal_problem` requires the proposal to
    be the evidence ceiling, with one exception in the next point. Aiming below the
    ceiling is refused (`below_evidence_ceiling`) just like overclaiming, because
    understating the evidence misreports it equally. The user's stated reasons for
    proposing lower — no suitable evaluator for a stronger grade — are already what the
    ceiling computes, so nothing legitimate is lost. "The test bundle was too harsh" was
    deliberately **not** accepted as a reason: difficulty is not evidence strength, and
    discounting the grade because the skill failed a fair test would be fitting the
    grade to the answer. An A-grade failure is the strongest output this tool produces.
  - **Accepting settles immediately.** Proposing the grade this exact design was already
    critiqued at ends the negotiation with no second session, since re-running the same
    judgment on the same evidence buys nothing. The accepted value is clamped to the
    ceiling. A critique that supported no grade is accepted the same way: the plan still
    executes, produces ungraded comparison evidence, and continues to the documentary
    path.
  - **A round costs a real revision.** Re-proposing on a design already critiqued
    returns `local_design_unchanged` and spends neither a session nor a round. Only a
    changed candidate earns a new round, which is what makes a larger budget safe.
  - **Objections carry forward, grades do not.** Each new critique receives the concerns
    earlier reviewers raised about earlier versions of the design and a rubric criterion
    requiring it to say, for each, whether this version answers it. No earlier grade is
    supplied: a reviewer shown "the last one said C" has an easy answer available, which
    is the anchoring the fresh session exists to avoid. The objections come from Python's
    stored audits, so the planner cannot restate them. The separation is imperfect and
    the contract says so — an objection can imply a grade it does not name.
  - **One round per rubric grade.** `MAX_ROUNDS = len(GRADES)` is 5, per the user's
    instruction. The count is a policy choice bounded by session cost, not a derivation;
    what makes it safe is that rounds are spent only on real revisions. The installed
    policy is now `evidence-strength-v2` and the critique rubric
    `local-evidence-critique-v2`, both with new digests recorded in every audit.
  - On the last permitted round the critique's grade is settled rather than offered, and
    the settled grade always describes the plan that will execute, never a stronger
    design that was discarded.
- A planner-authored Python evaluator is capped at B, because the rubric's A row
  excludes AI judgment from scoring. This was not enforced before.
- Grade D no longer needs `documentary_review`: a completed independent assessment
  against the installed rubric **is** grade D with the assessor's status.
- Deleted the `scientific_reviews` and `documentary_review` settings, their
  validators and their fixtures. Synthetic fixture runs still receive no grade, and
  the verdict rules are unchanged, including unanimous failure being as eligible as
  unanimous success.

**2. Catalog contribution reviews after the pull request, not before it.**

The old order put the human first: export required a written redistribution
authorization, `publish` required `--approve-publication`, and a release could not
even be built without one `independent: true` human review record per candidate.
The PR was the *result* of review. There was also no way to address review comments:
`publish` returned early once a PR existed, and the branch name was derived from the
bundle digest, so a corrected bundle opened a *second* PR.

- Rewrote [catalog_publication.py](src/sci_ai_verifier/catalog_publication.py): the
  branch is derived from the proposal identity, republishing an unchanged file pushes
  nothing, and a changed file commits a revision onto the same branch and pull
  request. A branch the receipt did not create is still never overwritten, nothing
  merges, and the lost-reply reconciliation is retained.
- Added a read-only `review` command that returns the pull request state, reviews and
  inline comments so the agent can act on them.
- [catalog_release.py](src/sci_ai_verifier/catalog_release.py) now takes one prepared
  assessment per candidate carrying `propose_for_catalog` or `propose_retirement` and
  an explicit `scientific_approval: not_conferred`. Requalification still runs before
  a release can exist. Bundle and release schemas were bumped to 2, since their field
  sets changed; no version 1 bundle or release was ever published.

**3. Removed files that were outdated and unused.**

`tmp/legacy_fixed_workflow/` (15 files), `reviews/` (6 files), the superseded
`evaluators/chemical_mass/` helper and its test — that test only covered the dead
helper; [test_verification.py](tests/test_verification.py) already tests the same
expected values against the installed method. Untracked `dist/` build output was
cleared. Links into the removed paths became commit-pinned permalinks at `f7293ec`,
matching the precedent set on 2026-09-11. The Desktop install guides were kept: the
historical profiles still work and those are human guidance. Nothing else was
removed; the stage2/stage3/verification/demo profiles remain functional, as the user
chose.

**4. Code review findings.**

Misleading steps:

- SKILL.md announced "Version 0.6.0" while the runtime is 0.7.0 — corrected.
- `tests/test_desktop_package.py` hardcoded `0.6.0` in the artifact filename and in
  its `serverInfo` assertion, while the builder names files from the manifest version.
  **These five tests were passing against a stale 0.6.0 package left in the ignored
  `dist/` directory, not against current source.** They now read the built version,
  and the module puts `src` on its own path instead of depending on another test
  module having done it.
- `local_candidates.fetch_bytes` sent `User-Agent: scientific-verifier-local/0.6` —
  now derived from `__version__`.
- The planner prompt was one 700-character run-on sentence that was the only
  statement of step order and never mentioned seeking the strongest grade. It is now
  a numbered `PLANNER_PROMPT` constant.
- README pointed at the 2026-09-12 entry as "the current log".

Gates that were too wide:

- `record_local_limitation` accepted any planner-invented `code` string in any
  nonterminal state, so a planner could abandon every claim with one call each and
  still reach `write_report_card`. The code is now an enumerated set of planner
  causes, the record carries `asserted_by` so the report distinguishes an abandoned
  claim from an observed failure, and the tool is no longer legal in `local_ready`:
  a settled executable plan is ended by executing it.
- `record_local_unverified` (grade U) and `assess_local_documentary` (grade D) were
  reachable from `local_discovery` behind a single `list_local_candidates` call, so a
  planner could publish a U verdict or a documentary conclusion without retrieving
  one reference. Both now require evidence Python actually observed — a retrieved
  reference or a recorded qualification attempt — and both are refused while the
  claim still holds a qualified candidate it never executed
  (`stronger_evidence_available`).
- `execute` treated its plan audit as optional (`if work.get("audit_ref")` twice). If
  an audit were ever absent the trials ran and grading was skipped silently. It now
  fails closed.
- `documentary_step` applied its runtime/assessor-identity check to
  `record_local_unverified`, which does not use an assessor, while the evidence gate
  it actually needed was missing. The check now applies only to the assessment path.
- An illegal local claim transition was raised inside `local.operate` as a retryable
  fault, so it decremented `retries_remaining` instead of
  `illegal_transitions_remaining`. The check is now in the dispatcher next to the
  equivalent verification-profile check.
- The `exact` comparison method's only negative control was the expected value with a
  suffix appended, which tests that `==` works and nothing else. It now also probes a
  prefix and a truncation.

Claude-standards problems in the Codex-authored code:

- `tools.py` decided dispatch with `name in WORKFLOW_TOOLS[6:]`, a positional slice of
  a tuple. Inserting a tool in the wrong position would have silently rerouted it.
  Replaced with a named `PLAN_TOOLS`.
- `scientific.implementation_bytes` — a generic runtime-integrity primitive — lived in
  the chemical-pilot module and was imported from there by the local profile. Moved to
  [storage.py](src/sci_ai_verifier/storage.py).
- The two independent-session paths duplicated their process plumbing; factored into
  `documentary.isolated_answer`.
- `common.validate` had no `enum` support, so an enumerated argument could only be
  checked by hand inside each operation. Added, and the published tool schemas now
  carry the enumerations the planner must satisfy.
- Not fixed, and recorded here deliberately: six modules
  (`local_science`, `local_evaluators`, `local_resources`, `documentary`,
  `local_catalog`, `catalog_publication`) are written without spaces after commas
  while `common`, `agent`, `tools`, `claims` follow PEP 8, and several files mix both
  styles line by line. Validators are single `if` statements with up to twenty `or`
  clauses reporting one generic message for twenty distinct causes, so an operator
  cannot tell which field was wrong. Function-local imports are used as the default
  style rather than to break real cycles. Blanket
  `except (KeyError, TypeError, ValueError, ...)` blocks turn our own programming
  errors into user-facing "invalid input" faults. Files touched this session were
  normalized; a repository-wide reformat is a separate change and would bury this
  diff.

Found by reviewing this session's own diff, and fixed in it:

- The documentary gate first consulted the whole local catalog, so one claim's
  qualified candidate would have blocked the documentary path for every unrelated
  claim, including claims that can never be executed. Scoped to candidates qualified
  for that claim; whether a catalog candidate from another scope applies stays a
  planner judgment.
- The critique rubric permits `D`, and `weaker("A", "D")` returns `D`, so a critique
  answering D would have stamped a documentary grade onto a comparison record
  produced by actually executing the subject. A critique naming D or none now settles
  at no execution grade, which routes the claim to the documentary path where D is
  established.
- An over-proposal was raised as a retryable fault, which spends the run's shared
  eight-retry repair budget. Over-proposing is expected during negotiation, so it is
  now the ordinary outcome `local_grade_above_evidence_ceiling`, which reports the
  ceiling and its limiting reasons and leaves the claim in discovery.
- Deleting the two settings keys broke every settings file already written by
  `configure_local.py`, with a message that named nothing. The fault now names the
  unsupported keys and says those two were removed, and the upgrade guide documents
  the one-line edit.
- A revision pushed after a reviewer's merge deleted the head branch patched a ref
  that no longer existed and failed identically on every retry. An absent ref that
  this receipt created is now recreated.
- `decide()` returned `evidence_ceiling` holding the *settled* grade while the plan
  audit's field of the same name holds the *mechanical* ceiling. Renamed to
  `settled_ceiling` so one field name does not carry two meanings across records.
- Found while reviewing the tightened negotiation: accepting a critique that supported
  no grade was blocked by the final-round guard, leaving the claim stuck in discovery
  with no legal move at all. A critique naming a grade *stronger* than the ceiling made
  the design permanently unselectable, because the only acceptable proposal was one the
  ceiling then refused. Both fixed and covered by tests.
- `scripts/local_catalog.py` caught only `Fault`, `OSError` and `ValueError`, so an
  unexpected GitHub response shape printed a traceback instead of an unavailable
  status.

**5. Validation.**

- Full suite: **212 tests, 210 passed, 2 skipped**, in 83 seconds. The skips still
  require Python 3.11 and physical symlink privilege. New coverage: evidence ceilings
  per rubric row, a proposal above the ceiling refused before a critique runs, the
  critique lowering a grade and the planner settling at what it supports, round
  exhaustion, a critique supporting no grade, an unavailable critique as an
  operational limitation, grade D with no operator review, and each narrowed gate.
  A retrieved oracle with an agreeing critique reaches grade A with no human step,
  and a deliberately wrong skill earns the same grade with a failing verdict. The
  tightened negotiation adds: a below-ceiling proposal refused, accepting a critique
  with no second session, arguing on an unchanged design spending neither session nor
  round, a changed design earning a round whose packet carries the prior objections and
  no prior grade, a critique above the ceiling still capped, and one round per grade.
  Publication coverage now includes opening without a sign-off, lost-reply
  reconciliation, revising the same PR, recreating a branch the reviewer deleted,
  refusing a foreign branch, and reading review comments.
- `python scripts/run_local_fixture.py` completes and its report shows the proposal,
  the ceiling, the limiting reason and no grade for a synthetic subject.
- 196 local Markdown links across 30 files resolve, including anchors.
- **These are fixture and offline checks. No live Claude Code session, container, app
  adapter or real scientific source was exercised, and no grade produced by this code
  has been observed on a live run.**

**6. Cleared the previous live-test data, at the user's request, for a fresh start.**

Deleted from the ignored `.verifier/` workspace: the attempt logs, run journals and
reports, subject-run receipts, the content-addressed object store, and all seven
candidates saved by earlier live runs -- the glycoengineering SNFG, IgG1 Fc Asn297,
N-glycosylation sequon and afucosylated FcgammaRIIIA candidates, plus the bacterial
translation-table and Bakta flag ones. Also removed accumulated fixture, package-check
and scratch output from earlier development sessions.

Two consequences to record. The 2026-09-14 entry above cites attempt
`4bfdf075-cadc-46ef-b1f9-3df3b4322ae6` and run `6bd0d78d-0b5e-4364-bf93-161c485fd15e`
as the evidence locating that authentication failure; **those artifacts no longer exist
and that finding is now unverifiable from this workspace.** The finding itself stands as
recorded, but it cannot be re-inspected. Second, the grade policy and critique rubric
digests changed in this session anyway, so no candidate from those runs could have been
reused under an audit bound to the new policy; clearing them costs nothing that was
still usable.

Kept deliberately: the five prepared example skill folders under
`.verifier/example-downloads/prepared/`, which are test inputs rather than output, and
`.verifier/local-settings.json`, with the two removed review keys dropped from it so it
loads against the current configuration. Its pinned image ID, Docker path and
`trial_count: 3` are unchanged, so grades A and B remain reachable on the next run.

### Urgent next steps, if any

The credential-handoff fix from 2026-09-14 is still unverified live, and the grade
negotiation adds one more live dependency: the critique session. A verification now
starts a fresh session per selection round, so a repeat of the glycoengineering test
exercises planner, critic, subject and assessor authentication together. If the
critique cannot authenticate, claims will terminate with `critic_unavailable` rather
than silently going ungraded.

### Suggested next move

Rerun the user's glycoengineering test from a fresh local Code session and read the
plan audit in the report: the proposed grade, the evidence ceiling with its limiting
reasons, the critique's findings and objections, and the settled grade. That is the
first real evidence about whether the negotiation produces honest grades rather than
either overclaiming or defaulting to C. Set `trial_count` to at least 3 for A or B to
be reachable at all.

### Recommended next action

Verify one skill whose claims have a genuine public numeric reference, and check three
things in the report: that a claim whose answers were retrieved by Python and scored
by the installed numeric method can actually reach A, that the critique's objections
are specific to the claim rather than generic caution, and that no claim carries a
grade while its limiting reasons say the evidence does not support one. It is finished
when the report shows a settled grade with a recorded critique for every executed
claim, or an operational limitation naming what failed.

## Claude: 2026-09-16

### Current stage and status

The first live run on the new branch reached real Claude Code and **failed before
snapshotting the source**. Run `7e74f094-ac19-4f41-999b-4b100e5e0643` closed as
`incomplete` with `completion_reason: source_not_authorized`: zero claims, zero
subject calls, no report. Two host-boundary defects caused it. Both are now fixed
with tests that fail against the old behavior. Live acceptance remains pending and
the rerun has not happened yet.

### What has been done

**1. An oversized context reply is invisible to the planner.**

`get_verifier_context` returned every pinned contract in one reply. Measured at
53 KB from the code and reported as 56.3 KB in the run; the CLI wrote it to a file
and returned a preview:

> Output too large (56.3KB). Full output saved to: ...\sci-verifier-controller-...

The planner session has WebSearch and the internal tools only, with no file-read
tool by design, so it could not open that file. The two values it cannot work
without were at the **end** of the reply, after `context_blocks`, because
`canonical` sorts keys alphabetically. It improvised: sent a deliberately invalid
state token to make the server echo the real one back, spending 1 of 8 illegal
transitions, then guessed `source_path: "SKILL.md"`.

- `get_verifier_context` now returns a bounded header for the local profile:
  committed state, token, `authorized_parameters.source_path`, an `instructions`
  index of identity/digest/bytes, `fetchable_sections` and `omitted_sections`.
  Measured **2,235 bytes** against an 8,000-byte budget, versus 53 KB before. The
  header is checked against the budget and the run fails closed rather than emitting
  a reply the planner may never see.
- A new optional `section` argument serves one pinned document or committed artifact
  at a time, sliced to the run's read limit with `bytes_total` and a `truncated` flag.
  A closed run answers section requests too, so a committed report stays readable.
- The launcher now delivers the pinned contracts, the authorized path and the token
  in the planner's **prompt**, which is not subject to the tool-reply limit. The
  happy path needs no extra round trips, and the contracts arrive once instead of
  three times: the failed run called `get_verifier_context` three times and spent
  $0.22 on text it could not use.

**2. A repairable argument was refused fatally.**

`load_submitted_skill`'s `source_path` only *confirms* the path the operator
authorized -- `snapshot` reads `state["source_path"]` regardless, so a wrong value
selects nothing. Yet a mismatch raised `fatal=True`, which terminates the run, and
`load_submitted_skill` is legal only in `created`. The refusal message contains the
correct path, so the planner learned the answer at the exact moment it could no
longer use it.

A mismatch is now repairable **in the local profile only**: the refusal keeps
`repair_fields: ["source_path"]`, the run stays in `created`, and the existing repair
budget bounds retries. The historical Desktop profiles keep the fatal behavior their
pinned contracts describe, and their two Stage 2 tests still assert it unchanged --
their caller sees the whole reply and has no blind spot. A path outside the authorized
root stays fatal in every profile.

**3. Verification.**

- Full suite: **215 tests, 213 passed, 2 skipped**. Three new tests: no bootstrap
  reply exceeds the inline budget and every pinned document is separately fetchable;
  the prompt carries the authorized path, the token and the contract text; a wrong
  `source_path` is retryable and the run is still usable with the correct one.
- Both fixes were reverted temporarily to confirm the new tests fail against the old
  behavior. They did. A reproducer that does not reproduce is worthless.
- Contract halves updated together per the project rule: the local matrix and
  bootstrap prose in `workflow.md`, `load_submitted_skill` and
  `get_verifier_context` in `tool-contracts.md`, plus the new context-delivery
  sections in `local-contract.md` and `runtime-contract.md`.
- **Checked, not assumed:** the spill threshold is not configurable. The installed
  CLI (v2.1.268) recognizes 105 environment variables; the only output-size ones are
  `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `MAX_MCP_OUTPUT_TOKENS` (default 25,000 tokens),
  `MAX_THINKING_TOKENS` and `CLAUDE_CODE_MAX_CONTEXT_TOKENS`. The message we hit comes
  from the separate byte-based persist path, whose threshold is read from a
  server-side feature gate. Raising `MAX_MCP_OUTPUT_TOKENS` would not have helped:
  56 KB is roughly 14k tokens, already well under its default.

**4. Why fixtures missed this.**

Every test calls the runtime in-process and reads the returned dictionary. Nothing
crossed the CLI's tool-reply boundary, so no fixture could have caught either defect.
The manual live acceptance found both on its first real attempt, which is what it is
for. The new budget assertion closes the gap for the size defect specifically.

### Urgent next steps, if any

Rerun the glycoengineering test. The two defects that stopped the previous attempt are
fixed, but the run never reached authentication for the nested subject and assessor
sessions, so the 2026-09-14 credential handoff and the grade critique added on
2026-09-15 are both still unproven live.

### Suggested next move

Expect the rerun to fail somewhere new; that is progress, not regression. The run now
gets past bootstrap, so the next boundary is the first real subject trial and then the
first critique session. Read the plan audit in the report for the proposed grade, the
evidence ceiling with its limiting reasons and the critique's findings.

### Recommended next action

Restart Claude fully, start a fresh local Code session, and verify the glycoengineering
folder at `D:\Su Lab\verifier-submissions\examples\glycoengineering`. It is finished
when the report shows a settled grade with a recorded critique for every executed claim,
or an operational limitation naming exactly what failed.
## Claude: 2026-09-16 (live acceptance rerun)

### Current stage and status

The rerun happened and **completed end to end**. Run
`76ce4af1-17f7-4d96-bfb0-22726d94c96b` closed as `completed` with
`completion_reason: local_report_complete`: five claims extracted, four settled at
evidence grade **A** with `scientific_status: pass`, one closed as an operational
limitation with no grade, 66 of 66 scored trials passed, and a full report written.
It ran against `main` at `316deec`, started 2026-09-15T23:40:54Z, finished
2026-09-16T00:29:14Z, about 48 minutes, recorded cost $10.40, observed subject model
`claude-opus-5`.

This is the first live run that carried a claim the whole way from snapshot to
settled grade to executed trials to report. It does not establish that the verifier
works. It establishes that it worked once, on one skill, in one domain, against one
subject model, and only along the A-grade branch. **Live acceptance is now partial,
not complete.** The section on what this run did not exercise is the part that
matters for the next session.

### What has been done

**1. The run completed and the numbers reconcile.**

Subject: the glycoengineering skill at `D:\Su Lab\verifier-submissions\examples\glycoengineering`,
two files, 19,568 bytes, snapshot `0020ed03…`, integrity verified, both files read in full.

| Claim | Oracle | Cases | Trials | Passed | Grade |
| --- | --- | --- | --- | --- | --- |
| Sequon rule N-X-[S/T] | UniProtKB CARBOHYD annotations | 8 | 24 | 24 | A |
| SNFG symbol assignments | NCBI SNFG Table 1 | 6 | 18 | 18 | A |
| Oxford notation codes | none obtainable | — | — | — | none |
| Afucosylation and FcgammaRIIIA | Shields 2002 via Europe PMC | 4 | 12 | 12 | A |
| EPO N-glycosylation sites | Europe PMC glycoproteomics abstracts | 4 | 12 | 12 | A |

22 distinct cases, 66 planned trials, 66 attempted, 66 evaluated, 0 invalid, 0 missing,
`agreement: 1.0` on every case. `overall_scientific_grade` is `null`, as it must be.
41 hash-chained events, `illegal_transitions_remaining: 7` of 8, finalization complete.
66 of 128 permitted subject calls and 40 workflow steps used.

**2. Both defects from the previous entry are fixed live.**

The bounded `get_verifier_context` header and the repairable `source_path` were the
two host-boundary defects that closed run `7e74f094` as `source_not_authorized`. This
run got past bootstrap without incident, committed a five-claim manifest, and never
spent an illegal transition on context recovery. Both fixes are confirmed across the
CLI tool-reply boundary, which no fixture can reach.

**3. The nested sessions authenticated and ran.**

The 2026-09-14 credential handoff and the 2026-09-15 grade critique were both listed
as unproven live. Both are now proven. 66 subject sessions ran in containers, each a
fresh session with a fresh workspace, and four critique sessions ran with their tool
lists emptied, at roughly $0.27 each. No boundary violation was raised.

**4. The grade ceiling refused a design, and the planner rebuilt rather than settled.**

The first SNFG candidate qualified mechanically with `qualification_problems: []`. Its
expected value `Fuc` occurs in the quoted source only inside `Fuc4NAc`, so
`token_exact` failed and `evidence_ceiling` returned C with
`expected_value_not_token_exact_in_source`. The proposal of A was refused as
`above_evidence_ceiling`, which spends no critique round, and the planner rebuilt the
bundle from standalone Table 1 cells and reached A. Its own words in the audit:
"A is the ceiling this revised design can reach … not settling for the C the previous
version was capped at." Both candidates are retained. This is the two-layer check
working as designed: qualification accepts a substring, the ceiling requires a whole
token, and the stricter one caught what the first let through.

**5. The independent critique produced findings the mechanical checks cannot.**

All four critiques supported the proposed grade and none lowered one. All four
nevertheless filed objections, ten in total, which are recorded against the results
rather than resolved away. The most valuable was on the afucosylation bundle:

> "Case 3 leaks its own answer: the prompt identifies C1q by definition, so it can be
> answered correctly with no knowledge of the paper's negative result. It therefore does
> not function as the stated negative-discrimination case."

That case had passed every control probe. No mechanical check available to this profile
could have found it. The sequon critique separately re-indexed all six shown protein
sequences residue by residue and confirmed every expected value before endorsing the
grade.

**6. The refusal path worked.**

The Oxford-notation claim recorded `required_resource_unavailable` after four failed
retrievals, with `evidence_grade: null` and `scientific_status: null`. It also recorded
an unresolved scientific question it explicitly declined to score, about whether the
codes the skill labels "Oxford Notation" are actually the IgG glycan short code. A
fifth grade was available to invent and was not invented.

### What this run did not exercise

This is the honest boundary. The following are still **unproven live**:

- **Grades B, C, D and U.** Every graded claim in this run settled at A. The B path
  (pinned dataset, or a control-tested generated evaluator), the C path and the
  documentary D path have never executed live.
- **`qualify_local_evaluator`.** No generated Python evaluator was built or
  control-tested in a container. All four bundles used installed comparisons.
- **`assess_local_documentary`.** `documentary_assessment` is `null` on all five
  claims. The independent assessor session has never started live, so its boundary and
  its citation validation remain fixture-only.
- **`load_local_resource`, `fetch_local_asset`, `record_local_unverified`.** Never
  called in this run.
- **The revise-after-critique loop.** Every audit shows `critique_rounds: 1` with the
  critique supporting the proposal. A critique that lowers a grade, and the revision
  round that follows it, have never run live. Only the mechanical ceiling refusal was
  exercised, and that spends no round.
- **More than one subject model, domain and skill.** One skill of two files, one
  domain, `claude-opus-5` only. A grade earned against one model is evidence about
  that model.

### Urgent next steps, if any

**Test more skills before claiming this works.** One completed run on one skill is a
demonstration that the path is traversable, not evidence that the design is sound. The
next runs should be chosen to force the branches above rather than to repeat the A
path: a skill whose claims have no token-exact oracle, so the design settles at C; a
skill that needs a generated evaluator, so `qualify_local_evaluator` runs; and a claim
with no executable oracle at all, so the documentary assessor starts for the first
time.

### Suggested next move

Expect the first B, C or D run to fail somewhere new, the same way the first A run did.
The assessor path is the largest untested surface: it has a container boundary, a
packet size cap and machine-checked citations, none of which has met a live session.
Read the plan audit and the claim result the same way as before, and treat a critique
that lowers a grade as the success condition for that run rather than a setback.

### Recommended next action

Pick a second skill from the sci-ai-enabler catalog whose claims are not answerable
from a token-exact database row, and run it. It is finished when the report shows either
a settled grade below A with a recorded critique, or a documentary assessment, or an
operational limitation naming exactly what failed.

## Claude: 2026-09-18 (report card redesign: six independent axes)

### Current stage and status

Two live runs of `D:\Su Lab\verifier-submissions\examples\sar-analysis` happened on
2026-09-17/18. The second one **completed with a real graded result**, and in doing so
it exercised exactly the branches the 2026-09-16 entry asked for: a claim that settled
below A, a documentary assessment, and two operational limitations naming what failed.
That entry predicted "the assessor path is the largest untested surface" and that the
first non-A run would "fail somewhere new." Both happened.

Live acceptance is still **partial**. The A-grade branch now has two skills behind it
(glycoengineering, sar-analysis). The B branch has never produced a settled grade, the
C branch and `qualify_local_evaluator` remain untouched, and the documentary assessor
has now run twice live: once to completion, once rejected.

The substance of this entry is not the runs. It is a **proposed redesign of the report
card** into six independent axes, arrived at by reading what the second run actually
produced and finding that it discards its most useful finding. Nothing here is
implemented. The operator will request the fix separately.

### What has been done

**1. Run one was blocked by a stopped Docker daemon and its artifacts were removed.**

Run `769b0722-4aa3-4ff5-af7f-255cc057c2c5` extracted five claims and negotiated one to
a settled ceiling of A that the independent critique upheld, then failed every subject
observation with `sandbox_image_unavailable`: 18 planned, 1 attempted, **0 obtained**.
The four remaining claims routed to the documentary path and all returned grade D
`inconclusive`. Cost $6.05 over about 16 minutes for zero execution evidence.

Cause: Docker Desktop was not running. `docker info` failed with
`npipe:////./pipe/dockerDesktopLinuxEngine`. The pinned image was present and intact;
only the daemon was down. Preflight records `live_execution_tested: false` and **does
not probe Docker**, so the fault surfaced about 13 minutes in at the first subject call
rather than at startup.

All artifacts of this run were deleted at operator request before the rerun, together
with 45 store blobs, 2 candidate records and its subject-run directory. Counts were
verified back to the pre-run baseline (runs 49, attempts 2431, store 299, candidates 5,
subject-runs 231). The run therefore exists only in this entry.

**2. Run two completed end to end with the sandbox available.**

Run `1bb3f07a-7903-4e6c-8bcb-1f8eab23ffc0`, attempt
`b51e3ef7-aca3-42a4-9150-4aafa59dd75d`. Finished 2026-09-18T05:56:52Z, 2,372 seconds
(about 40 minutes), recorded cost $10.21, 1,876 hash-chained events, 50 planner turns,
`SKILL.md` 23,276 bytes at snapshot `92be1811`.

| Claim | Oracle | Ceiling | Cases | Obt/Plan | Grade | Status |
| --- | --- | --- | --- | --- | --- | --- |
| pIC50 = -log10(IC50 in M) | Europe PMC primary abstracts | A | 4 | 12/12 | **A** | pass |
| rdFMCS `threshold` semantics | RDKit official rdFMCS docs | B | 4 | 5/12 | none | none |
| `DrawMoleculeACS1996` | RDKit rdMolDraw2D docs | B | 4 | 12/12 | D | inconclusive |
| `makeDummiesQueries` | RDKit AdjustQueryParameters Doxygen | B | 5 | 15/15 | none | none |

Totals: 51 planned, 44 attempted, 44 obtained, 43 evaluated, 0 invalid, 7 missing.
`overall_scientific_grade` is `null`, as it always is in the local profile
(`local.py:663` and `reporting.py:58` both hardcode it).

The pIC50 claim is the strongest result the local profile has produced: the oracle is
the authors' own published pIC50 values from three independent primary papers
(Hall 2007, Sharif 1996, Seabrook 1994), agreement 1.0 on all four cases, and
`ai_involvement.verdict: false` -- the verdict was mechanical, not judged.

**3. Both lost claims were on track for real grades.**

Both `rdFMCS threshold` and `makeDummiesQueries` settled at ceiling **B** with the
independent critique supporting B. Neither failed scientifically. They were lost to two
unrelated operational faults:

- **`subject_model_changed`** -- trial 5 of 12 returned
  `observed_model_ids: ['claude-opus-4-8', 'claude-opus-5']`. The configured model is
  the alias `"opus"`, which the CLI is free to resolve to a different version mid-run.
  `local.py:540` correctly refuses a mixed trial set rather than pooling across models.
- **`assessor_response_invalid`** -- the documentary assessor returned a reply that
  failed `validate_assessment` (`documentary.py:65`). The identical step succeeded nine
  minutes earlier for the ACS1996 claim (`assessor-2.json` at 05:47 ok,
  `assessor-1.json` at 05:56 rejected after 35s). There is no retry, so one malformed
  reply ends a claim permanently. The raw reply is not persisted, so the specific rule
  it broke is unknown.

**4. The test cases the planner could build are weak, and the cause is the sandbox.**

Three of four claims are assertions about RDKit runtime behavior, but the trial
container is bare `python:3.12-slim` with `allowed_subject_hosts: []`. RDKit can never
be installed or reached, so the only available oracle is documentation and the only
constructible test is verbatim recall. The two non-unanimous cases on
`makeDummiesQueries` are both of this kind:

```
dummy-c2  "Reproduce that description verbatim"
          trial 1  convert dummy atoms without isotope labels to any-atom queries   pass
          trial 2  convert dummies in the input structure into query atoms          fail
          trial 3  convert dummy atoms without isotope labels to any-atom queries   pass

dummy-c4  "Give the name ... without the RDKit namespace prefix"
          trial 1  MolOps::adjustQueryProperties    fail
          trial 2  adjustQueryProperties            pass
          trial 3  adjustQueryProperties            pass
```

Neither failure is a chemistry error. One is a paraphrase where a verbatim quote was
demanded; the other left on a namespace prefix the prompt said to strip. The run's own
critique had already flagged that these prompts leak the identifier being asked about
and test only the semantics half of the behavior. **The sandbox having no RDKit is the
root cause of the weak science in this run**; it is a resource-policy decision, not a
defect.

**5. Two substantive findings for the skill author, not scored against the skill.**

Both surfaced from retrieved RDKit documentation: `makeDummiesQueries` is documented as
defaulting to `true`, so the skill's explicit `= True` restates a default rather than
changing behavior; and the documented conversion applies only to dummy atoms *without
isotope labels*, which R-group decomposition dummies frequently carry.

### The proposed design: six independent axes

The current card welds independent facts together and, in the most informative case,
emits nothing. The `makeDummiesQueries` claim scored **13 passes and 2 fails across 15
trials against RDKit's own documentation** -- a genuine, reportable finding about
reliability -- and the report says `evidence_grade: null`, `scientific_status: null`.

The redesign replaces that with six fields that never overwrite one another.

| Field | Answers | Depends on |
| --- | --- | --- |
| `evidence_grade` | How good was the reference? | reference and test bundle only |
| `accuracy` | How often did output match expectation? | the reference |
| `consistency` | Did repeated trials agree with each other? | nothing external |
| `completeness` | How much of the plan actually ran? | execution |
| `scientific_status` | Does the claim hold? | the pre-committed rule |
| `fault` | What did *we* break? | the runner |

**Grade is narrowed to reference quality only.** A/B/C/D/U already sort roughly by what
kind of reference was available, so this is a clarification rather than a
redefinition. It may change for exactly two reasons: no adequate reference was found,
or the reviewer inspected the test bundle and found problems. It must **never** move for
a behavioral or an operational reason. Scan the nine illustrative cards below: grade
only ever reports the reference.

This also disentangles a second existing conflation. The rubric claims to keep AI
judgment separate as its own question, but the grade table encodes it in the letter
(A is "no AI judgment in scoring", D is "AI judgment is primary"). Narrowing the grade
forces AI involvement out into the field where the rubric already says it belongs.
Counting honestly, this makes **four** axes plus two qualifiers, not three.

**Consistency stops being a gate and becomes an input.** This is the whole repair, in
one line. Today `agreement < 1` sets `supported = False`, which nulls the grade, which
then nulls the status. Under the redesign consistency feeds the aggregation rule: a
unanimity rule makes a split case a `fail`, a majority rule may still allow `pass`.
Either way a verdict survives. Flakiness becomes a finding instead of a silence.

**Accuracy and consistency are not symmetric,** and the rubric should say so.
Consistency compares the skill to itself and is therefore valid even against a
worthless reference. Accuracy compares the skill to the reference and is meaningless
without a trustworthy one. The operator's position -- accepted -- is that a card showing
`grade U / accuracy 100% / consistency 100%` is honest and complete, because a human
reading all six columns draws the right conclusion, and emphasis is the UI's problem.
The one carve-out is machine consumers: anything that filters candidates or prepares
catalog contributions must read grade before accuracy, or it will promote a U-grade
100%.

**No composite score.** The goal is fault localization, not ranking: a reader should see
which stage broke without guessing. A blended number destroys exactly that, and the
axes are not commensurable anyway (one ordinal, two ratios over different denominators,
and a category). Named profiles or a lexicographic sort over
`(grade, accuracy, consistency)` would give comparability without averaging, but neither
should be built until something actually needs to rank.

### Status rubric

`status` is one of `pass`, `fail`, `inconclusive`, `null`, with a required reason when
`null`. Evaluate in order; first match wins.

| # | Condition | Status |
| --- | --- | --- |
| 1 | grade is `U` | `null` -- `no_reference_grade` |
| 2 | zero evaluable observations | `null` -- `not_executed` |
| 3 | observations not attributable to one subject | `null` -- `unattributable_observations` |
| 4 | coverage below the plan's audited minimum | `null` -- `incomplete_coverage` |
| 5 | pre-committed aggregation rule satisfied | `pass` |
| 6 | pre-committed aggregation rule violated | `fail` |
| 7 | rule indeterminate on this evidence | `inconclusive` |

Only `U` gates status, and the reason is definitional rather than qualitative: with no
reference there is no expected answer, so the question has no value -- not a weak one.
Grades A through D never touch status. A D-grade claim may `pass`; an A-grade claim may
`fail`.

`aggregation_rule`, one of `unanimity`, `majority` or `threshold(p)`, must appear on the
card. Without it `fail` is uninterpretable, since 13/15 is a `fail` under unanimity and
a `pass` under majority. The rubric already requires the rule be fixed before execution;
it simply is not recorded or parameterized today.

### Nine illustrative cards

| Card | Grade | Accuracy | Consistency | Complete | Status | Reads as |
| --- | --- | --- | --- | --- | --- | --- |
| clean | A | 15/15 | unanimous | 15/15 | pass | good reference, skill works |
| reliably wrong | A | 0/15 | unanimous | 15/15 | fail | strong refutation; grade stays A |
| blind spot | A | 9/15 | unanimous | 15/15 | fail | repeatable defect -- debuggable |
| flaky | A | 9/15 | split | 15/15 | fail | nondeterministic -- different fix |
| docs only | D | 15/15 | unanimous | 15/15 | pass | behaved, but never checked a number |
| no reference | U | 15/15 | unanimous | 15/15 | null | three green numbers meaning nothing |
| truncated | B | 4/4 | unanimous | 4/12 | null | our fault, not the skill's |
| never ran | B | not_obtained | not_obtained | 0/18 | null | infrastructure; reference reusable |
| documentary | D | not_applicable | not_applicable | n/a | inconclusive | this path never measures behavior |

The blind-spot and flaky cards carry **identical accuracy and identical status** and
require completely different fixes. Only the consistency column separates them; no
single number could. The never-ran and documentary cards both lack behavioral data, but
`not_obtained` and `not_applicable` mean opposite things and must be distinct values.

### Defects this exposes in the current implementation

1. **Grade and status are welded.** `local_science.py:196` is one boolean; any case
   below unanimity sets `grade = None`, and `:199` then discards an already-computed
   verdict via `verdict if grade else None`.
2. **No cascade.** `evidence-rubric.md:70` specifies "total eligibility predicates for
   A, B, and C" and `:76` requires resolving to the strongest eligible grade with no
   uncovered observation pattern. The code has no per-grade predicates -- it is
   `grade = ceiling if supported else None`. The contract already calls for the
   behavior the redesign wants.
3. **The aggregation rule is hardcoded and trial-level.** `"fail" if counts["fail"]
   else "pass"` bakes in unanimity over trials, where the rubric requires a rule chosen
   from the claim and applied to per-case outcomes.
4. **`trial_agreement_below_policy` sits in `grade_limit_reasons`,** alongside genuine
   reference weaknesses, so a reader cannot tell a wobbling skill from a bad reference.
5. **Preflight does not probe Docker,** so a stopped daemon costs a full run.
6. **The subject model is an alias.** The MCP registration in `LOCAL-INSTALL.md:139`
   passes no `--model`, so it defaults to `"opus"` and may resolve to another version
   mid-run. `serve-local` already accepts `--model`; pinning `claude-opus-5` is a
   one-flag change.
7. **The assessor has no retry.** One malformed reply ends a claim. Any retry must fire
   on reply *shape* only, never on `assessor_citation_invalid` and never because the
   verdict is unwelcome, or it becomes grade shopping. `local-contract.md:117` currently
   states outright that invalid assessments are operational failures, so that line is
   edited before any code.
8. **`deterministic` is a misleading name and a live trap for this refactor.**
   `local_science.py:97` defines it as *the comparison method is `exact` or `numeric`*,
   not as *the subject is deterministic*. The rubric's single-trial carve-out is about
   the **subject**. Anyone reading `deterministic` at `:121` as a statement about the
   subject would wrongly conclude `n = 1` is acceptable. Rename to
   `comparison_deterministic` before touching that block.
9. **`trial_count` may be set to 1 in a profile where it is never legitimate.**
   `local_config.py:49` bounds it at `(1,20)`. The rubric permits `n = 1` only for a
   deterministic subject with a fixed entry point, and the local profile's subject is
   always a fresh Claude Code session, so that carve-out is unreachable here. The cap
   itself works -- `trials < STRONG_TRIALS` adds `model_subject_trial_count_below_three`,
   which blocks A and B and drops the ceiling to C -- but the local lower bound should
   be raised to 3, since no reachable local path benefits from 1. Check the
   `"trial_count": 1` fallbacks at `agent.py:221` and `local.py:360` before changing it;
   they may serve synthetic or non-local paths.

### Open questions and resolutions

**The truncated card, resolved: keep the data, withhold the verdict, blame coverage.**
The first draft of this entry assigned the truncated card to rule 3
(`unattributable_observations`), which is wrong. What claim 1 actually collected was
three clean Opus 5 trials on case `mcs-thr-c1`, one clean trial on `mcs-thr-c2`, a
contaminated fifth trial, and nothing at all on the remaining two cases. Trials 1-4 are
perfectly attributable to a single model; nothing poisoned them.

The damage is to **coverage**, not attributability: one usable case against
`MINIMUM_CASES = 3`. So the card keeps `accuracy 4/4` and `completeness 4/12` and
withholds status under **rule 4, `incomplete_coverage`**. This satisfies the operator's
requirement that a runner bug must not destroy surviving evidence, while refusing a
verdict whose shape nobody audited: the reviewer approved a four-case design, and
publishing a conclusion from one case would substitute a much weaker test under a grade
justified for a stronger one.

Note that the surviving `mcs-thr-c2` sample is itself `n = 1`, so salvaging a verdict
here would mean mixing a three-trial case with a one-trial case in a single decision --
the exact defect the single-trial rule already forbids. That is the deeper reason to
withhold, and it links this question to the next one.

**Where the single-trial cap lives.** Today "a single sample caps the grade at C" sits
inside the grade. Once the grade is purely about the reference, that rule has no home
there. The likely answer is that accuracy and consistency are never reported as bare
ratios and `completeness` carries the denominator, but this needs writing down.

### Second design proposal: automatic dependency resolution

> **NOT APPROVED FOR IMPLEMENTATION. Do not build any part of this, and do not
> alter the sandbox network posture, until the operator explicitly asks for it by
> name.** It is recorded here as a design decision with its trust boundary and
> residual risk stated, so that the reasoning is not lost and so that nobody
> implements a weaker version of it by accident. It is strictly larger than every
> other item in this entry combined.

**The problem is scale, not this run.** The finding above -- that no RDKit in the
sandbox forces documentation-recall tests -- has an obvious fix at the scale of one
operator's desk: build an image with RDKit pre-installed and pin its digest, exactly as
`sandbox_image` is pinned today. That answer does not survive contact with the actual
goal. At a hundred skills a day nobody hand-curates a hundred environments, and a
published tool cannot ask its users to build images before verifying anything. Manual
curation is therefore rejected as the long-term answer while remaining the correct
short-term one.

**The reframe.** The agent does not need to make a *trust* decision in order to make a
*dependency* decision. Those two were conflated in the first pass at this question. If
the safety properties are structural and mechanically checkable, dependency selection can
be automated without any party -- human or model -- judging what is safe to install.

**Separate resolution from execution.** Two phases:

1. **Resolve.** Networked. Runs before any reference search, before any skill code
   executes, while no evidence exists. Deterministic Python -- not the model -- turns a
   dependency request into a fully hash-pinned lockfile and materializes a
   content-addressed layer.
2. **Execute.** `--network none`, unchanged from today (`sandbox.py:131`). The container
   receives the pre-materialized layer and reaches nothing. Reruns are byte-identical
   because the lockfile pins hashes.

Reproducibility survives because the lockfile digest folds into `environment_digest`,
which already hashes the whole of `settings` (`local_science.py:70`). The operator's
proposed gate -- that the dependency decision be made before looking for references -- is
satisfied structurally by this ordering rather than by a rule anyone has to enforce.

**Four mechanical gates replace the human reviewer.** None requires judgment:

1. **Wheels only** (`--only-binary :all:`). Most install-time supply-chain execution
   lives in `setup.py`; wheels run no install-time code.
2. **Hash-pinned** (`--require-hashes` against the generated lockfile). Anything that
   cannot be pinned fails closed.
3. **Index pinned** to PyPI or a configured mirror. No arbitrary URLs, no VCS
   references, no `--find-links` to unlisted hosts.
4. **Size and count caps,** the same shape as the existing `max_artifact_bytes` and
   `max_artifacts`.

**The gate that removes the typosquat risk: the model never names a package.** A
dependency resolves only if its name is *attested in the submitted skill's own snapshot
bytes*. `rdkit` is resolvable for the sar-analysis skill because `SKILL.md` -- authored
by the skill author, snapshotted and digested before anything ran -- contains
`rdkit.Chem.rdFMCS`. `rdkit-nightly` is not, because that string appears nowhere in the
submission. The failure mode worth fearing is a model confidently selecting a
plausible-looking wrong distribution name; under attestation the model is not the source
of the name at all, the submission is, and "does this string occur in the pinned
snapshot" is mechanically checkable. Paired with an import-name to PyPI-project mapping
table, the model's role on the trust-sensitive step drops to zero.

**Caching is what makes a hundred skills a day tractable.** Layers are cached by
lockfile digest. A hundred scientific skills do not need a hundred environments; they
need `rdkit`, `numpy`, `scipy`, `biopython` and `pandas` in a handful of combinations.
The first submission needing a stack resolves it and the rest hit the cache, so
resolution cost amortizes across a long run instead of being paid per skill.

**Shape for a published tool.** Two tiers, with the user configuring nothing: prebuilt
digest-pinned domain stacks (cheminformatics, bioinformatics, numerics) as the fast path
that most submissions hit, and the resolver as the fallback for the long tail.

**What it costs and what it gives up.** This is a resolver, a lockfile format, a layer
cache, an import-to-distribution mapping table and contract edits -- larger than
everything else in this entry put together. It also genuinely moves the trust boundary,
from "a human vetted each package" to "PyPI plus wheels-only plus hash-pinning is
trusted." That posture is defensible and is roughly what ordinary CI runs on, but it is
a real expansion of `resource-policy.md` and must be written there as an explicit
decision with its residual risk named, never introduced as an implementation detail.

The residual risk after all five gates is a compromised or malicious *popular* package.
Wheels-only removes install-time execution, but the dependency's code still runs during
trials. What contains that is the execution sandbox itself -- `--network none`, resource
caps, ephemeral container -- and none of it may be traded away to make dependency
resolution more convenient. That is the whole reason resolution and execution must be
separate phases rather than one networked container.

**Why this is worth doing eventually.** Independence is required from *the skill*, not
from the tool the skill describes. For a claim such as "`threshold=0.8` means 80% of
molecules," real RDKit behavior is a legitimate independent oracle: it is ground truth
for RDKit's own API and entirely independent of the `SKILL.md` text under test. The three
claims in this run that topped out at ceiling B on documentation could plausibly reach A
with an executable oracle. That is the difference between grading documentation recall
and grading behavior, across every computational skill this project will ever see.

### Urgent next steps, if any

Nothing is urgent, because nothing is implemented and the operator has deferred the fix.
When it starts, order matters: **contracts before behavior.** `evidence-rubric.md` gains
the axis separation and the status rubric, `artifact-contracts.md` gains the new card
fields, `local-contract.md:117` changes before any assessor retry exists, and only then
does `local_science.py` change. A change that lets operational success produce a
scientific `pass`, or an evidence grade imply a verdict, remains a bug however the tests
read.

The dependency proposal above is **not** part of that sequence and is not scheduled. The
short-term answer for any skill needing a computational tool remains an operator-built,
digest-pinned image. Nothing in the dependency section is a licence to open the container
network.

### Suggested next move

Pin the model first. It is one flag, it needs no contract edit, and it removes a fault
that can void any future run at any point. Then implement the cascade, because it is the
change that makes the other work visible: with it, both claims that vanished in this run
would have produced graded verdicts, and the `makeDummiesQueries` claim would never have
reached the assessor at all -- the malformed-reply fault would have stopped mattering on
its own.

Do not treat the redesign as licence to relax anything. The model-identity refusal, the
no-retry rule on subject trials, and the ban on choosing an aggregation rule after
seeing results are all working correctly and all protect against grade shopping.

### Recommended next action

Rerun `sar-analysis` with `--model claude-opus-5` pinned and nothing else changed, and
compare against run `1bb3f07a`. It is finished when either the `rdFMCS threshold` claim
reaches a settled B with executed trials, or a different fault appears and is named.
That single comparison establishes whether the model alias was the whole story on
claim 1 before any card redesign is written.

## Claude: 2026-09-21 (six-axis report card implemented)

### Current stage and status

The report-card redesign proposed on 2026-09-18 is **implemented**, contracts first, with
the automatic-dependency section of that entry deliberately untouched. The suite is green
at **251 tests, 2 skipped** (baseline before this work: 240). No live verification run was
made: Docker Desktop is stopped again on this machine, and the operator asked to be
consulted before any run is started.

The central defect is fixed. A claim that scores thirteen passes and two fails across
fifteen trials against a good reference now reports **grade A, status `fail`, consistency
`split`**. Before this change it reported nothing at all.

### What has been done

**1. Contracts, before any behaviour.**

`evidence-rubric.md` replaces its three separated questions with six and states the rule
that carries the whole design: the grade answers *how good was the reference* and nothing
else, and never moves for a behavioural or operational reason. The A/B/C eligibility
predicates are restated over reference and test-bundle facts only, all of which are known
before a trial runs. Observed trial outcomes are explicitly excluded from them. A new
**Status** section carries the ordered seven-row rubric and the requirement to record which
`aggregation_rule` produced a verdict.

The three consequences under *Subject non-determinism* were rewritten. Only the first still
touches the grade: a *planned* `n = 1` is a test-bundle fact and still caps at C. Observed
disagreement no longer lowers anything, and a changed subject model now withholds the
verdict while leaving the grade alone.

`artifact-contracts.md` gains `accuracy`, `consistency`, `completeness`, `aggregation_rule`,
`fault` and `status_withheld_reason`, and states that `grade_limit_reasons` and
`execution_limit_reasons` are separate lists that may not be merged.

`local-contract.md` replaces "Invalid or missing assessments are operational failures" with
the bounded retry rule: shape is retried once against an identical packet, citations are
never retried, and the first valid assessment counts whatever status it carries.

No tool was added or removed and no tool's legality changed, so the `workflow.md` matrix and
`tool-contracts.md` needed no edit.

**2. `decide()` no longer welds the axes together** (`local_science.py`).

`grade = ceiling if (ceiling and not synthetic) else None`. Model constancy, retained
invalid observations and per-case agreement are all gone from the grade gate. A new
`verdict_for()` implements the ordered status rubric and returns `(status, reason)`, so a
missing grade no longer silently erases a computed verdict. The record gained `accuracy`,
`consistency`, `completeness`, `aggregation_rule`, `fault`, `status_withheld_reason` and
`execution_limit_reasons`; `grade_limit_reasons` now carries reference facts only.

**3. The agreement-based cascade was deliberately *not* built, because the design retired
it.** The 2026-09-18 entry listed "no cascade" as defect 2, reasoning from a rubric whose
A/B/C predicates consumed agreement. Once the grade stops moving for behavioural reasons
there is nothing to cascade down from: `evidence_ceiling()` already selects A, B, C or None
from reference facts, and that *is* the cascade. Implementing an agreement-based one would
have put behaviour back into the grade and contradicted the design the operator confirmed.
Defect 2 is therefore closed as obsolete rather than fixed.

**4. Smaller fixes from the same entry.**

- `deterministic` renamed to `comparison_deterministic` (`local_science.py:97`) with a
  comment saying it describes the comparison, never the subject. This was flagged as a live
  trap for exactly this refactor.
- `trial_count` floor raised from 1 to 3 (`local_config.py`). The single-trial exemption
  applies to a deterministic subject with a fixed entry point, which this profile can never
  have. The internal `trial_count: 1` fallbacks at `agent.py:221` and `local.py:360` were
  left alone: they serve subjects that carry no settings, which are the synthetic and test
  paths, and those are ungraded anyway.
- The assessor retries once on unusable shape and never on citations (`documentary.py`),
  with both attempts recorded on the result.
- `verify` now probes the container engine before spending a planner session
  (`local_entry.py`). **Verified against the real failure:** with Docker Desktop stopped it
  raises `sandbox_image_unavailable` in about a second, where the 2026-09-18 run reached the
  same fault roughly thirteen minutes and $6.05 in.
- `LOCAL-INSTALL.md` pins `--model claude-opus-5` in the registration command, with the
  reason recorded next to it.

**5. The card renders the axes** (`local.py:axis_lines`). Limitation records now carry
`fault`, `not_obtained` behavioural axes and a withheld reason mapped from the fault code;
documentary records carry `not_applicable`, which is a different statement from
`not_obtained` and is rendered as such. Records written before the axes existed still
render, returning nothing rather than raising.

**6. Tests.** Four rewritten in `test_local_science.py` to assert the new contract where they
previously asserted the old one, plus new coverage for: disagreement producing a graded
`fail`, invalid observations producing `inconclusive` at full grade, a changed model
withholding only the verdict, `grade_limit_reasons` never carrying behavioural facts, every
axis being populated on a clean pass, the assessor retry accepting a good second reply,
a second bad shape failing, citations never being retried, and all five card shapes
rendering including a pre-redesign record.

### Decisions taken 2026-09-21

Two questions raised by the implementation were put to the operator and settled. Both
confirm the behaviour already built, so neither required a code change; what they change is
that these are now **decided, not deferred**, and the comments and tests say so.

**1. A truncated trial set discards the trials that completed. Decided: discard.** This
supersedes the 2026-09-18 note that a fault should salvage its clean prefix and report
`incomplete_coverage` against it. On claim 1 of run `1bb3f07a` that prefix was four good
Opus 5 trials, and the tempting reading is that throwing them away lets our bug destroy
evidence. The reason it is still right to throw them away: a prefix of a plan is not the
plan the critique reviewed, and which cases survive is decided by wherever the failure
happened to land, so an accuracy computed over them describes an arbitrary subset while
looking like a measurement. The observations stay in the claim's receipts for anyone who
wants to read them; they are simply never promoted to an axis. `TruncatedRunTests` in
`tests/test_local.py` pins this, and `WITHHELD_FOR_FAULT` carries the reasoning inline so a
later reader does not add partial-accuracy reporting as an improvement.

**2. `status` stays a scientific verdict. Decided: keep.** The operator proposed
redefining it as an indicator of process completeness — `pass` when the workflow finished,
`fail` otherwise, with the detail in `fault` — on the sound reasoning that a pass/fail
summary duplicates what accuracy and consistency already report and forces a judgement the
human should make. It was rejected for one specific consequence: the reliably-wrong card
would then read `status: pass` beside `accuracy: 0 of 15`, which is operational success
producing a scientific `pass`, the exact thing `CLAUDE.md` names as a bug however the tests
read. Whether the process finished is already answered three times over by `completeness`,
`fault`, and `verification_complete`. The misleading-ness the proposal targeted was a
property of the old card, where status was the only field and was nulled to nothing; on the
six-axis card the verdict sits beside the numbers it came from and the rule that produced
it. The rejection is recorded in `evidence-rubric.md` so it is not re-proposed from scratch.

If the verdict later proves unhelpful in practice, the clean move is to **remove** `status`
and let readers conclude from grade, accuracy and consistency. Repurposing the word `pass`
is not an available option.

### Open questions for the operator

**1. Should the aggregation rule become a plan field?** It is currently the installed
constant `unanimity`, recorded on every card so `fail` is interpretable. Making it
planner-selectable per claim is the right end state — the rubric already requires the rule
be chosen from the claim — but it changes an audited tool schema, which means the
`workflow.md` matrix and `tool-contracts.md` move together with it. Not started, and not
yet urgent: every claim seen so far is a correctness claim that unanimity scores correctly.
Two triggers should reopen it — a submitted claim genuinely worded as typical behaviour, or
a trial count raised far enough that unanimity starts failing sound skills on noise. That
second one is arithmetic rather than opinion: a skill reliable 99% of the time per trial
passes 15 trials 86% of the time, 30 trials 74%, and 50 trials 60%, so the same skill looks
worse the more thoroughly it is tested.

**2. Re-registration is required for the model pin.** The `--model claude-opus-5` change is
in the install guide only. The live MCP server is registered in the operator's personal
Claude Code configuration, outside this repository, and still runs with the `opus` alias
until it is removed and re-added. Until that happens the fault that voided claim 1 of run
`1bb3f07a` can recur on any run.

### Urgent next steps, if any

None. Everything above is committed and green, and nothing is half-applied.

### Suggested next move

Re-register the MCP connection with the pinned model, start Docker, and rerun
`sar-analysis`. That exercises the whole change against the run that motivated it: the
`rdFMCS threshold` claim should now either reach a settled B with executed trials or fail
for a newly named reason, and the `makeDummiesQueries` claim should produce a graded
verdict instead of vanishing — which also means it never reaches the assessor, so the
malformed-reply fault stops mattering on its own.

### Recommended next action

Compare the new run's card against run `1bb3f07a` claim by claim. It is finished when a
claim that splits its trials shows a grade, a status and a `split` consistency label on the
same card, because that is the outcome the old code could not express.

## Claude: 2026-09-21 (continued: live rerun and two evaluator-quality fixes)

This continues the same calendar day as the six-axis entry, which is now in the archive.

### Current stage and status

The rerun that entry asked for happened and **completed end to end**. Run
`e13f50ee-a390-4130-83e6-8641cfd28367` closed as `completed` with
`completion_reason: local_report_complete`: six claims extracted, **five settled with a
grade and a status**, one closed as an operational limitation, 69 scored trials of which 66
passed, and a full report written. It ran against `main` at `536733d` plus the
unused-import cleanup then in the working tree, started 2026-09-21T23:17:25Z, finished
2026-09-22T00:14:08Z, about 57 minutes, recorded cost $15.32, 53 steps, 78 subject calls,
observed planner model `claude-opus-5`.

Three things the previous two entries were waiting on all landed. The `rdFMCS threshold`
claim reached **A with 12 of 12 executed trials** rather than the predicted B. The
`makeDummiesQueries` claim produced **grade A, status `fail`, consistency `split`** instead
of vanishing — the defect the six-axis card was built to fix, confirmed live. And
`RGroupDecompose` settled at **B**, the first settled B grade in the project's history.

The substance of this entry is not the grades. It is that **the run's two `fail` verdicts
were artifacts of how the tests were written rather than findings about the skill**, and
the two fixes that follow from that. Both are committed.

### What has been done

**1. Claim by claim, against run `1bb3f07a`.**

Same submission, byte-identical snapshot (`SKILL.md`, 23,276 bytes). Trial count 3.

| Claim | `1bb3f07a` | `e13f50ee` |
| --- | --- | --- |
| pIC50 definition | A / pass, 12 of 12 | **A / pass**, 15 of 15 |
| `rdFMCS` threshold | no grade, `subject_model_changed`, 5 of 12 | **A / pass**, 12 of 12 |
| `DrawMoleculeACS1996` | D / inconclusive (documentary) | **A / fail / split**, 18 of 18 |
| `makeDummiesQueries` | no grade, `assessor_response_invalid`, 15 of 15 | **A / fail / split**, 12 of 12 |
| `RGroupDecompose` | not extracted | **B / pass**, 12 of 12 |
| `GenerateDepictionMatching2DStructure` | not extracted | no grade, `subject_model_changed`, 9 of 15 |

Every claim that carried a fault last time now carries a grade. `DrawMoleculeACS1996` moved
off the documentary path entirely, which is why the malformed-assessor-reply fault stopped
mattering on its own, as predicted. `overall_scientific_grade` is `None` only because the
sixth claim is ungraded.

**2. The model pin was necessary and not sufficient.**

Open question 2 of the six-axis entry is closed: the MCP server is re-registered with
`--model claude-opus-5`, and `subject_config.model_id` and the controller receipt both
record it.

The `subject_model_changed` fault did not go away. **It moved.** The failing observation is
`claim-002/009-response.json`, case `depiction-reference-needs-coords`: `model_id` is
`claude-opus-5` as requested, but `observed_model_ids` is
`["claude-opus-4-8", "claude-opus-5"]` — the CLI served part of **one session** from another
model. That is upstream fallback inside a single session, not alias resolution differing
between sessions, so pinning on this side cannot prevent it. The guard behaved correctly:
`status_withheld_reason: unattributable_observations`, eight completed trials discarded.

A navigation trap worth recording: `subject-runs/<run>/claim-00N` directories are numbered
in processing order and **do not** match claim-id hash order in the card. The faulted claim
was `claim-006` in the report and `claim-002` on disk. Map by `case_id`.

**3. Two `fail` verdicts that a chemist would not endorse.**

Both came from documentation-phrasing recall under exact string comparison:

- `dummies-conversion-target`: expected `"any-atom queries"`, one trial answered
  `"any-atom query"`. Singular against plural.
- `acs1996-guideline-target`: expected `"ACS 1996 guidelines"`, two trials of three
  answered `"ACS 1996 mode"`.

Under `unanimity` a single such trial fails the claim. The run's own critique on claim 1 had
already named the general problem: the oracle "measures recitation fidelity as a proxy for a
semantic claim," and a behavioural oracle was "available and unused."

**4. Fix one: an exact answer must have one correct surface form** (`e5329de`).

Contracts first. `qualify()` already required every expected value to be a verbatim quote
from a fetched reference, which keeps the answer key out of the model's hands and should not
be relaxed. Its unstated side effect: the only askable questions are ones whose answer is a
literal string in a document, so cases drift toward reciting prose, and
`actual.strip() == expected.strip()` cannot tell a paraphrase of a right answer from a wrong
one. Nothing constrained the *form* of the answer that rule produces.

`qualify_local_candidate` now requires two forms only: a whitespace-free token, or a closed
choice, where the case lists `options` and its `input` presents every one of them verbatim
so the subject selects rather than phrases. `options` is an optional schema field, so
existing token cases are unchanged. Controls probe each rejected option as well as the near
misses. Numeric answers take no options. Whether a distractor is genuinely wrong stays a
planner assertion, recorded in `QUALIFICATION_LIMITS`.

Replayed against the **64 real cases** from all live runs, the rule flags 8 and leaves 56
untouched. The 8 are both verdicts above, the prose case belonging to the claim voided for
the model swap, `"fraction of the dataset that must contain the MCS"` in both runs,
`"SVG molecule drawer"`, and `"unsigned int"`. The last four passed on luck.

Six tests added, mutation-tested: disabling the rule fails four of the six, the other two
being the positive control and the probe-count assertion.

**5. Fix two: a naming case does not test a behavioural claim.**

Fix one removes the wording lottery. It does **not** remove recitation. "What is the flag
called?" is a single token, passes the new rule cleanly, scores 3 of 3, and says nothing
about whether the claim is true. Three such cases scored perfectly in this run.

The structural cause is incentive, not laziness. The planner must propose the strongest
grade its design supports, and a naming case satisfies every mechanical A requirement
trivially — the name is in the docs, it is one clean token, exact match compares it
perfectly. Naming cases were the cheapest route to an A.

Python cannot separate them: once quoted, `51` (a glycosylation position, a real scientific
fact) and `makeDummiesQueries` (pure vocabulary) are the same shape. So this is left where
judgment already lives. `evidence-rubric.md` now states that a case testing what something
is *named* does not count toward the representative cases grade A requires when the claim is
about behaviour, meaning or a numeric relationship, and that naming cases remain legitimate
where the claim is itself about an API surface. The critique packet note
(`local.py`) points at that rule and says plainly that a finding which does not move the
grade changes nothing. `coverage` in the planner's justification must now state which cases
test what the claim asserts rather than what it is named.

No new mechanism was needed. The revision loop already exists: the critique lowering the
grade fires `local_grade_revision_required`, which returns `objections`,
`required_revisions` and `rounds_remaining` to the planner, and the rubric already lists
"cases that cover the stated scope" as a legal way to strengthen a design. It never fired in
this run because the trigger is `settled_ceiling != target_grade`: the planner proposed A,
the critique supported A, so the objection was recorded as a finding and changed nothing.

### Decisions taken 2026-09-21 (continued)

**1. Fault discards, bad accuracy keeps. Confirmed, not changed.** The operator restated the
principle: a fault inside the verifier, such as a model switch, throws the evidence away,
while poor accuracy or consistency is a finding about the skill or the world and keeps
everything. That is what the code does, and this run demonstrates both halves — two claims
with failing trials kept all their observations and were graded, and the faulted claim
discarded its eight. A refinement to retry only the affected trial rather than discard the
claim was raised and **not adopted**; it remains available if the 1-in-5 claim loss rate
across two runs becomes annoying.

**2. No machinery for computed ground truth. Decided: let the grade fall.** The question was
how to support a behavioural oracle whose expected value no document states. The operator's
answer: if nobody published it, the evidence genuinely is weaker, so it should earn a low
grade and be left to the AI to propose and the critique to settle. Building a mechanism to
manufacture an answer key is rejected. Note that behavioural tests **are** reachable today
where the reference itself publishes a worked example with its output; that path is
underused rather than blocked.

**3. The grade covers the whole evidence design, not the reference alone.** The six-axis
entry said the grade "answers one question, how good the reference was." That phrasing is
narrower than the code, which already grades case count, token-exactness, comparison
determinism and trial count alongside reference origin, and `POLICY["axes"]` says "reference
and test bundle." The operator confirmed the broader reading: the grade should reflect the
whole testing process, including how the tests were built, because a reader cannot be
expected to audit cases one by one. The contrast the earlier entry was drawing — against
*behavioural and operational* reasons — still holds exactly.

**4. Relevance, not strictness.** A proposal to instruct the planner toward "the strictest
kind of test" was considered and **rejected**. A naming case is already maximally strict:
exact match, zero tolerance, no partial credit, and it still tests nothing. Strictness
invites trick questions; the property wanted is whether the case tests what the claim
asserts.

### Open questions for the operator

**1. Should the aggregation rule become a plan field?** Carried forward unchanged from the
six-axis entry. Still `unanimity`, still recorded on every card, still correct for every
claim seen so far. Two triggers reopen it: a claim genuinely worded as typical behaviour, or
a trial count raised far enough that unanimity fails sound skills on noise.

**2. Does the naming rule actually change what the planner writes?** This is the one real
unknown. Both fixes are enforced at different strengths: fix one is mechanical and cannot be
ignored, fix two is a rule the critique must choose to apply — and the last critique named
the problem and waived it anyway. The check is cheap and exact, because the report card saves
both the critique's findings and the settled grade.

### Urgent next steps, if any

None. Everything above is committed and pushed, the suite is green at 257 passed, 2 skipped,
and nothing is half-applied.

### Suggested next move

Rerun `sar-analysis` against the current `main` and read the planner's behaviour rather than
the grades. Four of the grades are established twice over and are not the point.

### Recommended next action

Run `sar-analysis` once and answer two questions from the saved card. First: what did the
planner write for the eight cases fix one now rejects — closed choices that still settle at a
grade, or narrower claims that dodge the rule? Second: for any claim whose cases are mostly
naming, did the critique object **and lower the grade**, or object and settle anyway? It is
finished when both have a recorded answer. If the second answer is "objected and settled
anyway," the cheap fix has failed and the next step is forcing the planner to declare
per-case intent in the schema, which is a larger change and should not be paid for until
this one is shown insufficient.

## Claude: 2026-09-22 (four sar-analysis runs; indexed choices; reply reader; case scope; no-grade plans run)

### Current stage and status

Run `fb64115f-c50f-42e6-8408-8ed4feacab43` **completed end to end** and is the cleanest run
the project has produced: four claims, all four graded, **51 of 51 observations obtained and
evaluated**, zero faults, zero invalid, zero split cases. 38 minutes, $9.73, 40 steps,
observed model `claude-opus-5`. Grades A, B, B, A; three pass, one fail.

**The 2026-09-21 fixes work.** Every multi-word answer became a closed choice, the wording
lottery is gone, and — the part that had never happened before — the critique **objected and
lowered the grade**, twice. Two claims whose mechanical ceiling was A settled at B after two
critique rounds, on exactly the naming-versus-substance ground the rubric sentence added.

Two defects were found and fixed in the process. One was in yesterday's own commit.

### What has been done

**1. `METHOD_VERSION` was not bumped when the qualification rules changed** (fixed, this
session). The catalog import path re-qualifies a candidate against current rules, but the
local lookup path in `candidates()` does not — it filters on `method_version` and trusts
what it finds. All thirteen saved candidates still read `local-reference-comparison-1`, so
the eight prose-answer candidates from run `e13f50ee` were still selectable and the planner
could have reused them, skipping the new rule entirely and making the run worthless as a
test of it. Caught before starting. That string is the only thing standing between a
superseded rule set and a later run, and there is now a test that says so.

**2. The run, claim by claim.** Docker Desktop was stopped again and was started first.

| Claim | Grade | Status | Trials | Accuracy |
| --- | --- | --- | --- | --- |
| `rdFMCS` threshold | A | pass | 12 of 12 | 12/12 |
| `RGroupDecompose` | B | pass | 15 of 15 | 15/15 |
| `makeDummiesQueries` | B | pass | 12 of 12 | 12/12 |
| pIC50 | A | **fail** | 12 of 12 | 9/12 |

**3. The naming rule fired, and the revision loop with it.** Two claims had
`evidence_ceiling: A` and `settled_ceiling: B` after two rounds, so the critique did what
the previous run's critique had declined to do. Its own words:

> "The claim is behavioural ..., but no case invokes RGroupDecompose on any molecule or
> core; the behavioural half of the claim is entirely untested and only the vocabulary of
> the output is probed."

> "Cases 3 and 4 do not test the claim ... both can be answered by name-level familiarity
> with the struct while holding an incorrect belief about what makeDummiesQueries does."

Eight candidate versions were written for four claims, so the planner revised rather than
accepting. This is the pass condition the previous entry set, met.

**4. The same bug returned in a new costume.** The pIC50 failure is not a finding. Case
`molar-unit-open` expected `"molar"` and observed `"Molar"` — capitalization — and failed
3 of 3, so it is a deterministic false failure rather than a coin flip. The 2026-09-21 rule
required a whitespace-free token, and `molar` is one; string equality is still case
sensitive. The multi-word hole was closed and the single-token hole was left open.

Case-insensitive comparison is not the answer: in cheminformatics case is semantic, `c` and
`C` in SMILES being aromatic and aliphatic carbon.

**5. Closed choices are now indexed** (`choice`, a third installed comparison method). The
subject replies with the **option number**, compared numerically, so no wording, casing,
plural or whitespace of a right answer can score as a wrong one — the whole class is
structurally impossible rather than patched. A reply that is not a number returns
`invalid`, which reports a harness problem instead of a verdict about the skill; previously
a surface slip was indistinguishable from a real defect.

Because the index is the planner's own ordering and appears in no reference, the
**provenance anchor moved one level down**: the option the index selects must be the
verbatim quote. Same guarantee, one indirection. `token_exact()` and `answer_text()` in
`local_science.py` resolve the option behind the index so the grade still rests on quoted
bytes.

`exact` reverts to open answers only and no longer takes options. An open answer must have
a forced surface form: a number, or a token fixed by a case change, digit or underscore.
`molar`, `greater`, `true` and `three` are therefore no longer legal open answers.

**6. Four alternatives minimum, plus a reserved `none of these`.** The previous floor was
two, and this run's critique independently flagged that as the weakest item it saw:
"combined with only two options it is the weakest of the four items." Arithmetic agrees —
over three trials a coin flip carries a case 12.5% of the time at two options and 1.6% at
four. Beyond four the return is negligible; the binding constraint is distractor
plausibility, which Python cannot check and which stays a planner assertion, now stated in
`QUALIFICATION_LIMITS`.

The reserved final option is never the answer, so scoring stays ungameable, but a case
whose trials all select it is far more likely to have a broken option set than a wrong
subject. That is a diagnostic to read, not a verdict: the claim still fails, but visibly
for the right reason.

**7. Verification.** Replayed against **78 distinct expected values** from all four live
runs: 53 stay open, 25 now require a choice. The 25 include every value that has ever
produced a false failure — `any-atom queries`, `ACS 1996 guidelines` and `molar` — plus
`true`, `false`, `larger`, `greater`, `enhanced`, `three`. Suite **260 passed, 2 skipped**
from a 257 baseline. The new rules were mutation-tested: disabling the surface-form check,
the reserved-option rule or the options-in-prompt check each fails a test.

**8. A general review of the repository** for conflicting directions, overlapping
instructions, ambiguous references and dead content. The expensive class is clean: the
local state x tool matrix in `workflow.md` was diffed mechanically against `CLAIM_LEGAL`
and `OPERATIONS` in `local.py` and matches exactly, every documented constant matches its
code constant, no relative link in any document is broken, no module-level definition of
262 is unreferenced, and no fixture under `examples/`, `tests/recorded/` or `catalog/` is
orphaned.

Four small problems were fixed directly. `evidence-rubric.md` contradicted itself inside
one sentence, opening with eligibility over "reference and test-bundle facts only" and
closing with "a statement about the reference"; the closing clause now says evidence
design, matching `POLICY["axes"]`. That drift is not academic -- it is what made a correct
proposal look like a design violation during this session's discussion.
`local-contract.md` and `LOCAL-INSTALL.md` still described two comparison methods after
`choice` was added earlier the same day. And `evaluators/` was removed: it held nothing
but `__pycache__` bytecode for the helper deleted on 2026-09-15, untracked and invisible
to `git status`, while its name implied the helper still existed.

**9. The fourth run answered the three questions the third left open.** Run
`7efbdd8c-80e6-4545-a641-82826316833e`: four claims, 57 of 57 observations obtained, zero
faults, zero missing, 45 minutes, $12.01, model `claude-opus-5`. Grades A, B, A, A.

| Claim | Grade | Status | Accuracy | Invalid |
| --- | --- | --- | --- | --- |
| `rdFMCS` threshold | A | invalid | 9/12 | 3 |
| `makeDummiesQueries` | B | invalid | 17/18 | 1 |
| pIC50 | A | pass | 15/15 | 0 |
| `RGroupDecompose` | A | invalid | 11/12 | 1 |

*Did the planner adopt `choice`?* Yes, and used all three methods deliberately: five
candidates were `choice`, one was `numeric` for the pIC50 arithmetic, and one was `exact`,
titled "remedy named from scratch". That last one was the planner's own response to a
critique objecting that choices test recognition — it switched a case to make the subject
generate the answer. The critique in turn lowered `makeDummiesQueries` from A to B after
three rounds, attacking recognition directly: "all six cases supply that identifier or its
documented description among the options, so the instrument tests recognition of the
answer."

*Did any case come back `invalid`?* Five did — but not for the predicted reason. The
question anticipated a subject replying with option text instead of a number. **Every one
of the five was the correct number, in markdown bold**: `**1**`, sometimes followed by a
paragraph of explanation. Counting those, the subject answered **57 of 57 correctly**. No
case produced a genuinely wrong answer.

*Did coverage return to six?* No. Four again, missing the same two API-surface claims.

*Did any case draw unanimous `none of these`?* No trial selected it, so no option set was
broken.

**10. Replies are read from their first line, with emphasis removed** (fixed this session,
contracts first). This is the same fault a third time, in a third form:

| Run | Correct answer | Scored as | Cause |
| --- | --- | --- | --- |
| `e13f50ee` | any-atom queries | fail | plural |
| `fb64115f` | molar | fail | capitalization |
| `7efbdd8c` | 1 | invalid | markdown bold |

Indexing turned the third into an honest `invalid` rather than a false `fail`, which is
exactly what it promised and is why the subject's 57 of 57 was visible at all. The fix is
in the reader, not the prompt: the subject has now broken formatting three different ways
in three runs, the planner's prompt already asked for "the number of the single best
option", and the verifier's model is changing, so a prompt tuned to one model's habits
would not transfer.

`reply_number()` in `local_candidates.py` takes the first non-empty line, strips whitespace
and markdown emphasis (`*`, `_`, a backtick) from its ends, and parses what remains. It
**never searches inside the line**: `The answer is 1` stays `invalid`, because extracting a
number from prose is how a wrong reply becomes a false pass. It applies to `choice` and
`numeric` only. A number cannot contain those characters, so stripping them cannot change
its meaning; in `exact` answers they are content — `rgroup_label`, and `[*]` is a dummy
atom in SMARTS — so `exact` is never normalized. A trailing `.` is deliberately not
stripped either, because that would turn `.5` into `5`.

Every `choice` and `numeric` candidate now proves the rule during its own qualification:
three new controls check that a bold reply and a bold reply with an explanation both pass,
and that a sentence containing the right number stays `invalid`. `METHOD_VERSION` moved to
`-4` accordingly, so the seven candidates this run qualified without those controls are not
reused. Five tests were added, including one built from the verbatim observations, and
three mutations were each caught: removing normalization, making it greedy, and applying it
to `exact`. The greedy one matters most, since it is the false-pass path. Replayed through
the new code, the 57 saved observations went from 52 pass and 5 invalid to 57 pass, and no
passing verdict changed. Suite 260 → 265.

**11. The verifier's model pin moved to `claude-opus-5-5`, then back — superseded by
item 12.** Operator's request. The registration was changed by the documented
remove-and-re-add procedure, with the previous registration backed up first and diffed
after: exactly one argument changed, and the token field stayed a
`${SCI_VERIFIER_OAUTH_TOKEN:-}` placeholder throughout. What was not checked is whether
the CLI could run the model at all, and it could not. The same paragraph of
`LOCAL-INSTALL.md` had claimed that pinning makes "that whole class of lost run" disappear,
false since 2026-09-21 when the fault recurred with the pin in place; that correction
stands, as does the note that switching models starts a new series.

`LOCAL-INSTALL.md` also stated that only one live run had ever completed and that grades
B, C, D and U had "still never run live" — false four runs ago. Under the one-owner rule it
now points at "Current state" here instead of restating status. That section had itself
drifted, saying "Three runs" above a table of four; the prose count is gone, so the table is
the only thing that states it.

**12. The first Opus 5.5 run never started, and the pin went back to Opus 5.** Run
`a8036722-914b-4981-acdc-cca8ed01e61a` ended `incomplete` after 2.7 seconds with zero steps,
zero claims and no recorded model usage, so it cost nothing. The attempt log
(`6d3c58ae-af02-40cc-ba09-a716fc742f45`) carries the cause in its `process_diagnostic`
event: `[claude-code:unrecognized_model]`, then `API Error: 400 Claude Code 2.1.268 does not
support this model; version 2.1.280 or newer is required`. The planner was refused before
its first turn.

The upgrade path was a deadlock. `claude update` reported 2.1.280 available but declined
to install it, because WinGet manages this installation and it defers to WinGet; `winget
upgrade Anthropic.ClaudeCode` then reported no newer version in the configured sources.
WinGet's catalog lags Anthropic's releases.

The pin was reverted by the same procedure, and the result is identical to the original
Opus 5 registration rather than merely similar — compared against the backup taken before
the first change. Before reverting, a direct CLI call confirmed the distinction that failed:
`claude-opus-5-5` prints `unrecognized_model` before authentication is even attempted,
while `claude-opus-5` does not. That call could not complete, since a plain shell has no
verifier token, but the model check precedes sign-in, so it answers the question that
mattered; the authenticated path was already established by run `7efbdd8c`, on the same CLI,
hours earlier.

`LOCAL-INSTALL.md` is reverted to Opus 5, which also removes a contradiction introduced
with the switch: step 2 declared 2.1.248 sufficient while step 5 pinned a model needing
2.1.280. The model-pin section now tells anyone changing the pin to run
`claude.exe -p "Reply OK" --model <id>` first and look for `unrecognized_model`, and
explains that `Not logged in` in a plain shell is expected and does not mean the check
failed.

**13. The reader test run, `b43780be-7a3b-4c6d-b37c-d649fba918bb`.** Opus 5, confirmed on the
running server before starting. 53 minutes, $15.69, 56 steps. **Six claims**, 81 trials
planned, 63 observed, **zero `invalid`**, 18 never run.

| Claim | Grade | Status | Observed | Accuracy |
| --- | --- | --- | --- | --- |
| `rdFMCS` threshold | A | pass | 12/12 | 12/12 |
| `ringMatchesRingOnly` (new) | A | pass | 12/12 | 12/12 |
| `RGroupDecompose` | D | inconclusive | 0/18 | — |
| R-group dummy atoms | B | pass | 12/12 | 12/12 |
| pIC50 | A | fail | 12/12 | 9/12 |
| `DrawMoleculeACS1996` | B | pass | 15/15 | 15/15 |

*The reply reader works on a live subject.* Every observation was a `choice`, and nine were
not bare numbers: each put the answer on its first line and explained below. The previous
reader would have scored all nine `invalid`; this one read six correct answers and three
wrong ones. Opus 5 did not use bold this run, so that branch stays proven by the replay
and the tests rather than live. The planner now writes "Reply with the option number only
as the first line of your reply", matching the reader.

*Coverage came back to six.* On the same model as two runs that extracted four, including
`DrawMoleculeACS1996`. That largely retires the idea that the 2026-09-21 rubric edit was
narrowing extraction: it was run-to-run variation in what the planner chooses to extract.

**14. The pIC50 `fail` was a case that asked more than the claim.** The definition passed 9
of 9 on its three relevant cases. The fourth asked "which statement does a reference work
make about higher pIC50 values", expecting "higher values of pIC50 indicate exponentially
more potent inhibitors". All three trials chose `none of these`, and said why: "The skill's
only mention of pIC50 (line 114) defines it as `pIC50 = -log10(IC50_in_M)`; it makes no
statement about what higher pIC50 values indicate." The claim asserts the definition; the
direction of the scale is in neither the claim nor the skill. A subject applying the skill
had nothing to answer from, and read "a reference work" as its own loaded material.

Rewording it to "which is true" would be the wrong fix: the subject would answer from the
base model's knowledge and pass, crediting the skill for something the model already knew.
So the rule was extended instead. `evidence-rubric.md` now says a case must test what its
claim asserts **no less and no more**: not only what something is named, and not a
consequence the claim never states. The critique was given a sixth criterion saying the
same, which makes the judgment mandatory rather than advisory — `validate_critique` rejects
a reply with fewer findings than criteria. The previous critique of this claim had noticed
the attribution framing and kept grade A; it can no longer leave the question unanswered.

That criterion was not invented here. `critic-extra-finding.jsonl`, a real reply from run
`e035eef6`, answered the five v2 criteria and then added one more, unprompted: its cases
"test facts the claim does not print". A reviewer found the gap before the rubric had a slot
for it.

Adding a criterion made three genuine recordings incomplete, and `tests/recorded/README.md`
forbids editing a recording to make a test pass. So each is now judged against the rubric it
was *answering*. v2 is rebuilt as v3's first five criteria and pinned by v2's digest, taken
before v3 existed, which proves the reconstruction exact; criteria are append-only so that
stays true. `validate_critique` and `critique` take the rubric they judge against and record
its digest, defaulting to the installed one. The tests assert both halves: the three
recordings are complete answers to v2, and the live rubric refuses them.

`tool-contracts.md` also said a unanimous `none of these` means "a broken option set". This
run is the counterexample — the option set was fine — so it now says a broken case: options
that omit the answer, or a question about something the claim never asserts.

**15. The D claim could not run, and the guard let it leave.** Two faults, both code drifting
from contracts that were already right.

*Accepting a D critique was impossible.* The tool contract and the code's own comment say
accepting a design's critique ends the negotiation "including when it concluded that the
design supports no grade", and the plan then runs ungraded. `audit()` reads a D verdict as
no execution grade; `select()` did not. It computed the accepted grade as `weaker(ceiling,
"D")`, which is `"D"` — and D cannot be proposed, since only A, B and C are proposable, while
reproposing the ceiling on the same design was refused as unchanged with the message
"propose D". A `"none"` verdict always worked, because `weaker(x, None)` is `None`; only D was
trapped. The trace matches: two revision rounds held at D, one refused proposal, one
rejected attempt, then documentary as the only exit. The planner was not skipping the
experiment. It had no legal way to run it.

`select()` now maps any verdict other than A, B or C to no execution grade, as `audit()`
does, so reproposing the ceiling accepts a D exactly as it accepts `"none"`. The refusal
message now tells a planner that, instead of offering nothing.

*The guard checked selection, not execution.* `workflow.md` refuses documentary while a claim
"still holds a candidate it qualified for itself and never executed". The code returned
early as soon as a candidate was **selected**, so a selected but unexecuted plan could leave
for documentary. It now asks whether the claim is still in `local_discovery`, which no path
returns to after execution.

The order mattered. Tightening the guard alone would have closed the only exit a D-trapped
claim had, leaving it nowhere to go; the accept path had to open first.

Two tests, and all three changes were mutation-tested — reverting the accept fix, reverting
the guard and removing the criterion each fail a test. The criterion's first mutation
reported "caught" through a syntax error in the edited module rather than a test; it was
discarded and redone as a removal the parser accepts, which fails four tests on its own.
Suite 265 → 270.

### Decisions taken 2026-09-22

**1. Index the choices rather than loosen the comparison.** Operator's proposal. Turning
the answer into a number removes the surface-form question instead of managing it.

**2. Keep open answers where the surface form is already forced.** Numbers especially. The
pIC50 case that made the subject compute `-log10(1e-9)` and answer `9` was the strongest
evidence in the run: generation, not recognition. Turning arithmetic into a menu would
downgrade it, so the `choice` method is the default for everything else and not universal.

**3. A reserved always-incorrect option.** Operator's proposal, adopted with the framing
shifted from trap to diagnostic.

**4. `local-contract.md` is authoritative, and the co-edit rule is now general.** The
2026-09-22 review found CLAUDE.md contradicting itself: it listed six authoritative
documents without `local-contract.md`, while stating elsewhere that the local profile's
enforceable behavior is documented there. `agent.py:269` settles it — the local profile
pins that file, in full, as a planner instruction, which is more direct than the
section-only pinning some listed documents get. It is now item 5 on the list, and
`SKILL.md` names it and `local-evaluator-spec.md` in its reference guide.

The narrow co-edit rule was the second half of the bug. It protected exactly one pair by
name, so adding the `choice` method left `local-contract.md` wrong twice and
`LOCAL-INSTALL.md` wrong once for a day while the named pair stayed perfectly in sync.
CLAUDE.md now states the general form: a fact stated in more than one place has one
owner, every other mention links the owner rather than restating it, and the owner moves
in the same commit. `tool-contracts.md` owns the installed comparison methods,
`workflow.md` owns tool legality, `evidence-rubric.md` owns the grade standards. The
duplicate method lists in `local-contract.md` and `LOCAL-INSTALL.md` were replaced with
pointers, so the four copies of that list are now one.

**5. Fix reply formatting in the reader, never the prompt.** Three runs, three different
formatting habits, and a prompt that already asked for a bare number. The reader strips
presentation and never searches content; that line — strip wrapping, never search inside —
is what keeps a lenient reader from producing false passes, and it is tested by mutation.

**6. The move to Opus 5.5 is deferred until the CLI can serve it.** Operator's decision.
*This supersedes the same day's earlier decision 6, "The verifier moves to Opus 5.5".* The
operator chose to revert rather than wait, and the timing turns out to help: the next run
is meant to test the reply reader, and every previous sar-analysis run was on Opus 5, so
staying on Opus 5 tests one change instead of two. Changing the model and the reader in the
same run would have left a clean result unattributable, since Opus 5.5 might simply not
write bold. The switch happens as its own step once WinGet ships 2.1.280, and that run
starts the new series.

**7. A case asking more than its claim is fixed by scope, not by rewording.** Operator's
decision. Rewording an attribution-framed case to "which is true" would convert a false
fail into a false pass by letting the base model answer; restricting cases to what the claim
asserts removes the case instead.

**8. Case scope is a mandatory reviewer criterion, not guidance.** Operator's decision. A
rubric sentence alone left the last critique free to notice the problem and keep grade A.
A criterion must be answered or the whole critique is rejected.

This is the rubric's second case-type rule, after naming. The case-level contract below is
flagged not to be built until four or five such rules accumulate; two is not the trigger,
but this is the direction it counts toward.

### Designed, flagged do-not-implement: a case-level contract

**Nothing below is implemented, approved for implementation, or tested.** The operator
considered it and declined it as unnecessary complexity for the project's current size.
It is recorded because the design is finished and the trigger for revisiting it is
specific.

**The question it answers.** There is no general contract saying which kinds of test may
support which grade. `evidence_ceiling()` computes from reference and test-bundle facts
only — origin, scorer authorship, determinism, token-exactness, case count, trial count —
and is blind to what a case asks. Exactly one type rule exists, added 2026-09-21: a
behavioural claim whose cases only recite naming or spelling does not support grade A.
That rule works; it demoted two claims from ceiling A to a settled B in run `fb64115f`.

**The design.** Do not enumerate test types, which is a taxonomy that rots. Classify what
the subject must *do* to answer, which is close to exhaustive in three levels: **generate**
(produce a value present in nothing it was given — compute, execute, derive),
**discriminate** (choose among plausible alternatives it is shown), and **recall**
(reproduce a string from the material). The ceiling then follows from whether the case
level meets what the claim demands:

| Claim asserts | Recall case | Discriminate case | Generate case |
| --- | --- | --- | --- |
| a name or API surface | matches, A | A | A |
| a behaviour or meaning | below, max B | matches, A | A |
| a computed value | below, max B | below, max B | matches, A |

Row two column one is the existing 2026-09-21 rule; the table only generalizes it. Row
three column two is the case not yet met: a computation claim tested by multiple choice
turns arithmetic into recognition and should not reach A either.

**How it would bind.** The same division of labour as everywhere else. The planner
declares the claim kind and each case's level as small enums; Python computes the ceiling
from the table, which is arithmetic once declared and sits beside
`insufficient_distinct_cases`; the critique audits the declaration rather than judging
taste, because "this case is declared generate but its answer is printed in the prompt" is
concrete and checkable. That is the unlock: Python cannot classify a case but can enforce a
ceiling on a declared classification, which makes the demotion mechanical instead of
depending on drawing a diligent critique session.

**Why it was declined.** Cost is a schema change, `evidence_ceiling()` arithmetic, two
contract files, report-card rendering and tests, against one known problem that a single
sentence already solves. It also carries the coverage risk below: claim extraction fell
from six to four after one restriction was added, and this would be the second.

**Trigger to revisit.** Ad-hoc type restrictions accumulating in the rubric. One is a
sentence; four or five are a taxonomy pretending not to be, and at that point the table
above is cheaper and more consistent than the prose it replaces. A single new restriction
is not a trigger.

### Open questions for the operator

**1. Should the aggregation rule become a plan field?** Carried forward unchanged.

**2. Claim coverage — largely answered, kept open one more run.** After six, four and four,
`b43780be` extracted six again on the same model, including `DrawMoleculeACS1996`, one of the
two that had disappeared. The narrowing looked like the 2026-09-21 rubric edit and was
run-to-run variation in what the planner extracts. It stays here only because this run
also added a new criterion and a scope rule the planner reads before extracting, so the next
count is worth a glance; a fall back to four would reopen it.

**3. A narrow capitalization residue remains by choice.** `forced_surface_form()` accepts
any token carrying both cases, so `Core`, `Threshold` and `Fuc` stay open answers. Their
case is genuinely semantic — a C++ string key, a property name, an SNFG symbol — but a
subject could still lowercase one. Tightening to require an *internal* case change
(camelCase) would catch them at the cost of turning legitimate scientific symbols into
menus. Not done; the looser rule is what was agreed.

**4. The runner blames the operator for a planner that never started.** Recorded rather
than fixed, because it sits in the runtime's recovery path. When the planner process exits
before its first step, the runner closes the run through `cancel_verifier_run`, whose fixed
message is persisted into the operational outcome: run `a8036722` reads "The operator
cancelled this run." Nobody cancelled it — the CLI refused the model. The true cause,
`claude_code_version_too_old`, was in the event stream and did not reach the saved outcome.
The top-level error, `planner_incomplete`, is honest; the persisted record is not, and it is
the record a reader of the report sees. The fix is to carry the planner's observed failure
into the outcome instead of routing every dead planner through the cancellation path. The
preflight compounds it by recording `live_execution_tested: false`: it never asks the CLI
whether it can serve the pinned model, which would have caught this in seconds and for free.

**5. Recognition is untouched.** A choice can be passed by recognising the
conventional-looking option. This run's critique said so directly: "Closed-choice recall
with the correct wording present verbatim among the options tests discrimination, not
generation." Indexing does nothing about that, and neither does raising the option count.

### Urgent next steps, if any

**Restart Claude Desktop before the next run.** The verifier's Python runtime — critique
validation, `select()`, the documentary guard — runs inside the `serve-local` process, and
Python does not reload modules in a running process. The one running when this was written
(pid 23076, started 14:32) loaded the code *before* the scope criterion, the accept fix and
the guard fix. A run on it would test the old code, and its result would be misread as the
fixes failing.

Everything else is committed, pushed and green.

### Suggested next move

Run `sar-analysis` on Opus 5 and see whether the two fixes change what happens, not just
whether the tests pass. Two things can only be seen live: whether a critique answering the
new scope criterion actually lowers an out-of-scope design, and whether a claim critiqued
down to D now runs its trials before the documentary path.

Separately, once WinGet offers Claude Code 2.1.280, run the check in `LOCAL-INSTALL.md`
before moving the pin to Opus 5.5, and treat that run as the start of a new series.

### Recommended next action

After restarting Claude Desktop, confirm the running server's `--model` reads
`claude-opus-5`, then run `sar-analysis` once. First confirm the run used the new code: its
critiques' `rubric_ref` must be `07140328e5a3cbdd4eec803717fa0c71e0b05c0c5394d4f73b72b1f581c8663e`,
the v3 digest; `91f33b72…` means the old server ran it and nothing below counts. Then check
three things. Did every critique answer the sixth criterion, and did any lower a grade on
scope? Did any claim critiqued to D or `none` record observed trials before its documentary
assessment, rather than zero? Is `invalid` still zero? It is finished when all three are
recorded. If no claim happens to be critiqued to D, say so — the accept fix is then proven by
its tests but not yet seen live.
