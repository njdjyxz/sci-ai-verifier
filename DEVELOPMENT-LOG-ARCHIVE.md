# Development log archive

Full text of every development entry from 2026-09-08 onward, oldest first. The entries
through 2026-09-21 were moved here on 2026-09-21 when the active plan was condensed; those
from 2026-09-28 through 2026-10-25 were moved here on 2026-10-25, when `DEVELOPMENT-PLAN.md`
was rewritten as the project's introduction, current state and roadmap. Nothing is edited;
entries appear exactly as written. New dated entries are appended here, at the end, under
the rules in `DEVELOPMENT-PLAN.md`.

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

## Claude: 2026-09-23 (handoff, run b0955d2f, four fixes)

### Current stage and status

Version 0.7.0, local workflow. This entry began at 00:25 as a handoff checklist for a fresh
session and now records the day. Superseded from that version: the rubric digest to check is
v5 (`bf944269…`), not v3, because commit `a202146` moved the critique rubric on; the run to
clean is `b0955d2f`, not `b43780be`; and the runner no longer blames the operator for a
planner that stopped by itself (formerly open question 4), pending a live run.

Run `b0955d2f`, on commit `041552c`, completed cleanly: four claims at A, B, B and D, 54 of 54
trials passed, no `invalid`, no faults, every trial on `claude-opus-5`. It proved live:

- the five-minute critique deadline: two critiques took 123 s and 124 s and completed;
- a no-grade plan running before its documentary assessment: claim 3's nine trials ran first;
- case verdicts binding: a `beyond_scope` case and a `duplicate` case each stayed out of a grade;
- an exhausted replacement budget: claim 3's third critique settled it.

It did not exercise four fixes from `041552c`, which stay proven by tests only: an `exact`
answer followed by an explanation (all 54 replies were a single line), extra keys in a case
verdict (none of seven critiques added one), the varied-position rule (all nine designs
varied unprompted), and a `choice` case with no options.

It exposed four problems, fixed in this session with contracts first. **The fixes are tested
and pushed to `main` in the commit that carries this entry, but have not met a live run.**

### What has been done

Earlier today, by other sessions, summarised from their commit messages:

- `593ff24`: this entry's original handoff checklist.
- `a202146`: grades counted over the cases the critique counts ("Cases each grade requires"
  in `evidence-rubric.md`), a verdict per case, two replacement rounds, `mixed` designs,
  rubric v5, policy `evidence-strength-v4`, the rubric's case sections pinned to the planner,
  and retried temporary-directory cleanup. Runs `28d19f8a` and `d87a6d5c`.
- `041552c`: `exact` read from the first line, up to four extra keys in a case verdict, varied
  `choice` positions, a five-minute critique deadline, and a `choice` without options refused
  at qualification, under qualification version `-5`. Runs `0a243b7e` and `74eadedd`.

This session:

- Run `7f88fbef`, on `041552c`, stopped after 40 minutes: its planner hit the subscription
  session limit (HTTP 429), and the runner recorded that as the operator's cancellation. Its
  files were moved to the session scratchpad.
- Run `b0955d2f`: results above. Report
  `.verifier/runs/b0955d2f-fb7a-4e47-8cec-e8495f1b12e8/report-card.md`, workflow log
  `.verifier/attempts/7f6b7cd3-b609-4247-90e3-be450496454b/workflow.md`. About $20.89 at API
  rates, $13.14 of it the planner.
- Problems it exposed:
  1. The planner told reviewers what earlier reviews decided, three times, through its own
     notes: "The previous round settled at C…", "…the previous no-grade outcome", and "Two
     independent critiques have given this case the verdict counts." The hidden-grade rule
     was enforced only on what Python itself carries.
  2. Two pages were refused under one message naming two possible causes. Both were size: a
     974 KB tutorial holding 21 KB of text, and a 344 KB source listing holding 88 KB. The
     planner guessed the cause, and its guess reached the documentary packet as fact.
  3. Claim 3's D followed one verdict on an unchanged case: counted by two reviewers, then
     called `leaked` by the third, correctly (the question named `makeDummiesQueries`, and
     only the right option mentioned dummy atoms). Its design held exactly the minimum.
  4. `7f88fbef`'s false "operator cancelled" record.
- Considered and dropped because they contradict the reviewed design: changing
  `replacement_rounds_remaining` (`local-contract.md` counts a round when its critique rejects
  cases, so the counter is right), hiding the justification from the critique, a
  Python-computed leak hint (judging cases is the critique's job), and a bigger page limit
  without bounding the reply. The operator declined lowering grade A's case count and chose
  to keep earlier grades hidden from reviewers.
- The four fixes:
  1. **Hidden grade enforced against planner notes.** Step 3 of "Negotiating the grade" in
     `evidence-rubric.md` owns the rule. `select_local_candidate` refuses
     `prior_review_in_packet`, naming the field and phrase, before a critique session starts.
  2. **Page limits.** `reference_too_large` and `reference_credential_material` replace the
     single refusal, pages may hold up to 2 MiB, and the reply carries at most 40 KiB of text
     with `text_truncated` while the whole page is pinned. `tool-contracts.md` owns the numbers.
  3. **Who stopped a run.** `cancelled` only for the operator, `timeout` for the deadline, and
     otherwise `agent_unavailable` with the planner's own last result, as
     `artifact-contracts.md` already required. The runner passes it by a keyword no tool
     argument can set, so no tool schema changed. New real recording
     `tests/recorded/planner-session-limit.jsonl`.
  4. **A spare case**, in "Cases each grade requires".
- Verification: suite 294 → 301 passed, 2 skipped. The new tests fail against the old code,
  except the one proving that accepting a settled grade is never refused. Six one-line
  mutations of the fixes were each caught. One test replays `7f88fbef`'s real stream through
  `verify()` and checks the saved outcome and partial report.

### Before the next run

Check all of these; each one has cost this project a run.

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`
   (`python:3.12-slim`). The preflight does not catch a stopped daemon.
2. **The verifier server is running current code.** This session changed `src/`, so the
   `serve-local` process must have started after the commit that carries these fixes. Python
   does not reload modules, and a new chat in a running app reuses the same server. Read the
   start time with PowerShell:
   `Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like '*serve-local*' }`,
   and restart Claude Desktop if it predates the commit.
3. **The model is `claude-opus-5`**, read from the same command line. Claude Code 2.1.268
   cannot serve `claude-opus-5-5`, and WinGet does not yet offer 2.1.280.
4. **The working tree is clean** at that commit, or at a later one that did not touch `src/`.
5. **The plan's 5-hour window has room.** `7f88fbef` died on it, and a run costs about $21 at
   API rates.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `b0955d2f`:

- `.verifier/runs/b0955d2f-fb7a-4e47-8cec-e8495f1b12e8`
- `.verifier/attempts/7f6b7cd3-b609-4247-90e3-be450496454b`
- `.verifier/subject-runs/b0955d2f-fb7a-4e47-8cec-e8495f1b12e8`
- the **nine** candidates in `.verifier/candidates/` whose `method_version` is
  `local-reference-comparison-5`

**Keep** the glycoengineering run: `.verifier/runs/76ce4af1-…`, its attempt `a1ec3e49-…`, its
subject-runs, and the five candidates at `local-reference-comparison-1`. Leave
`.verifier/store/` alone; it is shared and content-addressed. Do not leave a shell inside a
directory you are moving: on Windows that blocks its removal.

### What to check in the run

`verify_skill` returns about 190 KB, which overflows the tool result. Read
`.verifier/runs/<run>/report-card.json` on disk instead.

1. **The new code ran.** The critique rubric did not change (`bf944269…`, v5), so its digest
   cannot show this; the server's start time can (item 2 above). A cut fetch reply carries
   `text_truncated`, and a refused note returns `prior_review_in_packet`.
2. **The new refusal.** Did the planner meet `prior_review_in_packet`, and did it rewrite the
   note and continue without looping? Quote the note it rewrote.
3. **Pages.** Any `reference_too_large`, `reference_credential_material` or `text_truncated`?
   Did a cut page still give the planner the quotes it needed?
4. **Spare cases.** Did designs hold one more independent case than their grade needs, and
   did one absorb a rejected case?
5. **Still unexercised from `041552c`:** an `exact` answer followed by an explanation, extra
   keys in a case verdict, the varied-position refusal, and a `choice` with no options. Say
   which, if any, occurred.
6. **`invalid` is still zero.** Record the claim count too: `b0955d2f` extracted four,
   `74eadedd` three.

### Reading the results without fooling yourself

- **Before calling any `fail` a finding about the skill, read the observed reply, the
  expected answer and the reference quote verbatim.** Every misleading result so far looked
  like a real one.
- **A unanimous `none of these`** means a broken case far more often than a wrong subject.
- **`claim-00N` directories under `subject-runs/` do not follow the report's order.** Map them
  by `case_id`.
- **`subject_model_changed`** is upstream fallback inside one CLI session, not a verifier bug.
- **A run the runner closed should now say `agent_unavailable`** with the planner's own
  reason. If it still says "The operator cancelled this run." for a stop nobody made, the
  server is running old code.
- **`workflow.jsonl` truncates long tool results** at about 16 KB. The whole request and
  result of every tool call, including every critique round and not only the final one, is
  in `.verifier/runs/<run>/events/`.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct for
   every claim seen.
2. **Claim coverage.** `b0955d2f` extracted four claims and `74eadedd` three. Still open.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. Their case is semantic, but a subject could still
   lowercase one.
4. **The preflight never asks the CLI whether it can serve the pinned model.** The other half
   of the old question, the runner blaming the operator, is fixed today and awaits a live run.
5. **Recognition is untouched.** Claim 3's leaked case is an instance: the only option naming
   dummy atoms was the right one.
6. **The section reader can return up to 128 KiB** (`get_verifier_context` with `section`),
   above the 53 KB reply once spilled to a file. It has not been seen to fail.
7. **Reviewers disagree on unchanged cases.** The rule that the latest critique governs and
   may only lower the grade is the conservative one; the spare-case guidance is being tried.

### Deferred, and why

- **Opus 5.5** — until WinGet offers Claude Code 2.1.280. Before switching, run
  `claude.exe -p "Reply OK" --model claude-opus-5-5` and look for `unrecognized_model`, as
  `LOCAL-INSTALL.md` describes; treat the first run after as a new series.
- **The case-level contract** — flagged do-not-implement until four or five case-type rules
  accumulate. Commit `a202146` has since added answer forms and four case verdicts, which
  overlap this design; whether they settle it has not been reviewed. Design in the archive,
  2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-23"). Follow its preflight, clean the previous run as it
describes, and use scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\sar-analysis"

Show me the report and workflow-log paths, a table with one row per claim
(grade, accuracy, consistency, status and the other measurements) and, for each
claim, a table with one row per test. Tell me whether it is a good run, and
whether our fixes work: go through the entry's "What to check in the run" list
item by item. Before concluding anything from a `fail`, an `invalid` or a
unanimous "none of these", quote the verbatim reply behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None now. Before the next live run, restart Claude Desktop so `serve-local` loads the commit
that carries these fixes; the server running when it was made started before it.

### Suggested next move

Run `sar-analysis` once on the new code and read the planner's behaviour rather than the
grades: whether it meets the new refusal and recovers, whether a fetch reply is cut, and
whether designs carry a spare case.

### Recommended next action

Restart Claude Desktop, confirm the server started after this commit, clean `b0955d2f` as
above, and run once. It is finished when every item under "What to check in the run" has a
recorded answer.

## Claude: 2026-09-24 (runs 3dc02567, 84e90683, 31b67427 and 3b3f3c94; one model per trial, a re-run, a fallback D, an RDKit image, critique rubric v7, claim-only answers)

### Current stage and status

Version 0.7.0, local workflow. Four sar-analysis runs today.

Run `3dc02567`, on `18ef2b9`, completed six claims: A, A, A, B and A, and one voided by a
refusal fallback; 95 of 95 scored trials passed. It led to commit `2d9f8af`: one model per
trial, one disclosed re-run at the end, a narrower prior-review trigger, the leak shapes in
the rubric, the 40 KiB limit on section and resource-preview replies, and a startup model
probe.

Run `84e90683`, on `2d9f8af`, completed four claims:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | B | 12 of 12 | four counting cases |
| `completeRingsOnly` / `ringMatchesRingOnly` | withheld | none | not obtained | `claude_timeout`, and again on the re-run |
| pIC50 | pass | A | 15 of 15 | one `duplicate` case not counted |
| dummy atoms / `makeDummiesQueries` | inconclusive | D | n/a | documentary, no trials |

It used 2,762 s of the 5,400 s limit, cost about $16, and had no `invalid` and no model
change. Of `2d9f8af`'s fixes, the probe worked (4.6 s), the re-run fired with time to spare
and repeated the timeout, and the section limit cut the planner's end-of-run report re-read.
No refusal occurred, so the one-model rule and the fallback switches are still unobserved;
the prior-review trigger never fired; `leaked` was two of the three rejections.

It exposed three problems:

1. **A critique counted cases its own objection placed outside the claim.** It wrote that "a
   subject applying the claim as worded answers 2 to both and fails", counted both cases, and
   all six trials of one of them failed. Had the claim finished it would have read A with
   status fail. Two of `3dc02567`'s critiques made the same contradiction.
2. **The ring-option claim reported nothing.** Both attempts stopped at the 120 s subject
   limit, and the report never named the limit.
3. **The sandbox had no RDKit.** Every ring-option trial first tried to import and install
   it. Two ran out of time working an MCS out by hand, and six worked one out wrongly. In the
   new image RDKit returns every expected answer.

The `84e90683` session's fixes, contracts first, are tested and pushed to `main` in
`d8a71f6`. Their first live run is `31b67427`, below:

1. **Fallback D.** A claim that a subject-trial fault still stops after the re-run gets a
   documentary assessment Python assembles from its cases' reference quotes, and the fault
   stays on the record. "Independent documentary path" in `local-contract.md` owns the rule.
2. **An honest timeout.** A `claude_timeout` names the case, the trial and the
   `subject_timeout_seconds` it reached, and says the limit is the verifier's.
3. **Critique rubric v6.** `beyond_scope` covers a key that a subject correctly applying the
   claim could miss, and `verdict_consistency` says objections and verdicts must agree.
4. **A fifth leak shape**: the correct option in the source's wording among options written
   fresh.
5. **The subject's command tool says nothing can be installed.**
6. **An RDKit image**, [images/rdkit/](images/rdkit/Dockerfile), pinned in
   `.verifier/local-settings.json`.

Run `31b67427`, on `d8a71f6` with the RDKit image, completed three claims:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | A | 15 of 15 | five counting cases, two open |
| `completeRingsOnly` / `ringMatchesRingOnly` | pass | B | 12 of 12 | one `leaked`; B accepted with a replacement round unused |
| dummy atoms / `makeDummiesQueries` | pass | B | 9 of 9 | one `duplicate`; three counting cases, one open |

It used 2,383 s of the 5,400 s limit, cost about $17, and passed 42 of 42 trials with no
`invalid`, fault, refusal or model change. Against the six fixes:

- **The RDKit image works.** `import rdkit` printed `2026.03.6`. Five trials ran seven
  commands; all succeeded in under a second and none tried to install anything. The longest
  subject session took 33 s. No ring trial ran a command, so `84e90683`'s failing ring cases
  were not retried.
- **Critique v6 was in force but not tested.** All four critiques carry its digest. None gave
  `beyond_scope`, every objection to a counted case questioned only its strength, and no
  counted case failed.
- **The fallback D and the timeout message were not exercised**: nothing stopped a trial.
- **The fifth leak shape was missed once.** In `which-object-is-the-query` the key, quoted from
  MolOps.h, was "a copy of a molecule with query properties adjusted", and the three other
  options began with "the", the tell of `84e90683`. The critique counted it, and the claim's B
  rests on it: without it two cases count, which allows no execution grade.
- **The no-install wording was not tested**, since nothing needed installing.

Two more findings. With RDKit present a subject can look an answer up: two of three trials of
a documented-phrase case printed `rdFMCS.MCSParameters.Threshold.__doc__`, which is the key
word for word. And the planner accepted B for the ring claim because "no second independent
open case is available from documentation alone", though that design already had two open
cases and A needed only one more counting case of either form.

Run `3b3f3c94` repeated the skill on the same code and completed four claims:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | B | 9 of 9 | one open case; one `duplicate` |
| `completeRingsOnly` / `ringMatchesRingOnly` | fail | C | 8 of 9, split | no open case; one `duplicate`, one `beyond_scope` |
| dummy atoms / `makeDummiesQueries` | pass | B | 12 of 12 | one open case; one `duplicate` |
| pIC50 | pass | A | 15 of 15 | redesigned after its first critique found a mis-keyed case |

It used 2,606 s and cost about $19, with no `invalid`, fault, refusal, timeout or model change.
Against `31b67427`:

- **`beyond_scope` worked twice.** Before any trial, the first pIC50 critique found that "30 nM
  is 3e-8 M and -log10(3e-8) = 7.522879, not 7.5", a key a correct subject would miss at the
  1e-6 tolerance; the planner rebuilt the design and the second critique supported A. A
  tutorial's "more intuitive representation of the scaffold" was ruled outside the ring claim.
- **A counted case finer than its claim gave the run's only `fail`.** `ring-no-lone-ring-atoms`
  keyed on RDKit's atom-level docstring "results cannot include lone ring atoms", which the
  planner itself called "a different exclusion from the bond-level partial-ring restriction".
  The failing trial answered `5`, "none of these": "`completeRingsOnly` excludes **partial
  rings** from the MCS … option 4's "lone ring atoms" describes only one narrow case". One
  passing trial had printed that docstring. The `fail` measures the case, not the skill.
- **No `leaked` verdict and no article tell.** The critiques rejected five `duplicate`s and two
  `beyond_scope`s. Three counted keys still carry a trace of their source, unflagged: the only
  option repeating the stem's "threshold", the only "log" among "logarithm"s, and an
  "actually".
- **Weaker designs for two claims.** For the ring claim the planner judged a
  symptom-to-option-name `exact` case recitation, the kind `31b67427` counted, so no open case
  was left and C was the ceiling; the threshold design had one open case, not two. On the same
  code the same claims settled A then B, and B then C.
- **The prior-review refusal fired falsely once**, on "a reviewer may judge one of each pair to
  add little independent evidence", a sentence about the coming review. No session was spent.
- **Subjects ran 14 commands**: ten pIC50 logarithms, three `AdjustQueryProperties`
  experiments and that one docstring lookup. The fallback D and the timeout message are still
  unexercised.

The same session then made seven fixes for those findings, contracts first. They are tested
but **have not met a full run**:

1. **The critique gets the leak shapes.** Its rubric, now v7, lists the five shapes of "Common
   leaks" in `evidence-rubric.md`. Until now only the planner received them, which is how
   `31b67427`'s critique counted the article tell.
2. **Qualification refuses the article tell.** A correct option whose first word or
   capitalisation alone differs from every other option's is rejected, as
   `local-reference-comparison-6`. Over the saved choice cases of `84e90683`, `31b67427` and
   `3b3f3c94` it flags the three known tells and none of the other 27.
3. **A claim-only answer tests `beyond_scope`.** Before counting a case the critique answers
   it from the claim alone; if another option, `none of these` included, is as defensible as
   the key, the case does not count. `ring-no-lone-ring-atoms` is the worked example.
4. **An effect-to-setting case is not naming.** Asking which setting produces a described
   effect tests what the setting does; a name that hints at the effect bears on strength only.
5. **The revision reply states the case gap.** `case_gap` gives the counting and generated
   cases the proposal needs, has and lacks, and names the critique's own grade when that
   limits the settled grade too.
6. **Qualification refuses a lone repeated word**, added after the replay below at the
   operator's request. A correct option that alone repeats a content word of the question is
   rejected, in the same `-6`. Over the same 30 saved choice cases it flags nine keys, six of
   which critiques had counted, `ring-no-lone-ring-atoms` among them. With the leading-word
   check, 11 of the 30 would have been refused at qualification, so expect more rewrites; a
   refusal costs a planner turn, never a session.
7. **Python measures the claim-only answer**, built at the operator's request after the
   prototype under open question 12. Before each critique that would start, every case of a
   design scored by installed methods goes twice to a fresh no-tool session on the pinned
   model, which sees only the claim's statement and expected behaviour and the case input. A
   case any answer misses does not count, and is returned as `beyond_scope` from the
   claim-only answers; a session that fails, or that another model answered after a refusal,
   leaves its case unmeasured with the critique's verdict standing. An unchanged case reuses
   its earlier answers from the negotiation history. Sessions run four at a time, two minutes
   each; the workflow log gained a thread lock so their streams keep one digest chain. The
   critique judging a design never sees its answers, and the report marks the cases they
   rejected. `evidence-rubric.md` "No more" owns the rule; `select_local_candidate` in
   `tool-contracts.md` owns the mechanics.

Not done, and why: making acceptance wait until the replacement rounds are spent (open
question 9), because acceptance is right when an objection concerns the oracle rather than
the count; and narrowing the prior-review trigger (open question 11), because its false
positive costs one planner turn while a false negative would carry a grade to the critique.

Operator decisions today: D stays pure AI judgment and needs no trials, so every claim gives
the reader something to refer to; a re-run claim's first attempt stays out of the report,
being the product of a runner fault; `subject_timeout_seconds` stays at 120 s until a large
skill needs more; RDKit belongs in the image; an effect-to-setting case counts, as this
session recommended.

Superseded today: "a safety refusal is never retried", replaced by the one disclosed re-run;
the reading of `subject_model_changed` as random fallback, which was a refusal fallback; my
recommendation that D follow an execution, declined; a stopped ungraded plan ending with
nothing, since it is still not re-run but now gets the fallback; the pinned image
`78387bc3…`, now `12771144…`; checking the server's start time, replaced by the run's own
code digest below; critique rubric v6, now v7; and the fifth leak shape as planner guidance
only, now also in the critique's rubric and, in part, a qualification check.

### What has been done

In the session of runs `31b67427` and `3b3f3c94`, started after `d8a71f6`:

- Cleaned `84e90683` into the session scratchpad and ran `31b67427`. Report
  `.verifier/runs/31b67427-6db9-4e0e-ac8b-ae15aba4b21c/report-card.md`, workflow log
  `.verifier/attempts/6f0bb1b2-cfa7-4ac1-8d81-80853d68baa0/workflow.md`. Cost: planner
  $11.08, 42 subject sessions $4.80, four critiques $0.91.
- Cleaned `31b67427` the same way and ran `3b3f3c94` on unchanged code. Report
  `.verifier/runs/3b3f3c94-6892-4de7-a09e-a37f2092ef00/report-card.md`, workflow log
  `.verifier/attempts/7deed1ed-05b8-46d3-b919-0b22c1035c31/workflow.md`. Cost: planner
  $11.00, 60 subject sessions $6.60, five critiques $1.10.
- Checked both item by item against "What to check in the run"; the results are above.
- Implemented the six fixes in `evidence-rubric.md`, `tool-contracts.md`, `documentary.py`,
  `local_candidates.py`, `local_science.py` and `local.py`. Verification: suite 321 → 327 tests,
  with 324 passing, 2 skipped and the machine-only failure under "Current state". Seventeen
  one-line mutations of the fixes were each caught, with the tests run from `tests/` as
  discovery runs them. A first count of twelve had named the integration tests in a way that
  cannot import them, so it proved nothing and was redone. `test_recorded_replies.py` rebuilds
  v6 from v7 and pins its digest, `9dc8fd5d…`.
- Replayed saved critique packets through `critique()` on `claude-opus-5`: nine sessions, $2.39,
  the token passed as the MCP registration passes it, `CLAUDE_CODE_OAUTH_TOKEN` from
  `SCI_VERIFIER_OAUTH_TOKEN`. The replay script is in the session scratchpad.
  - `which-object-is-the-query` still counted under v7, in two samples of two, and neither
    reply mentioned the article tell. The rubric text did not carry the fifth shape to this
    model; qualification's check (fix 2) is what now stops that case.
  - `ring-no-lone-ring-atoms` counted in no fresh sample, v7 or v6: all three called it
    `leaked`, as the only option mentioning rings. The original count was one reviewer's miss,
    and none gave the claim-only test as the reason.
  - v7 newly called `application-reason-retain-rings` leaked, its key the only option echoing
    the stem's "application-side"; the original v6 critique counted it.
  - The effect-to-setting cases still counted, "so it is not mere naming". The pIC50 control
    kept A with every verdict unchanged. The threshold control fell from A to B:
    `molecules-left-out-below-one` became a duplicate, the objection its v6 critique had
    already raised while counting it.
- Earlier, a blind subagent proxy on a different model had caught the article tell that the
  pinned model then missed. A proxy on another model does not predict the pinned one.
- After `096273e`, in a new session: the 19 saved designs of the three runs, re-qualified with
  the committed code against their stored references. Ten that had qualified are refused, each
  for its flagged leak, among them the two that decided grades; the pIC50 designs still
  qualify. Rewriting `ring-no-lone-ring-atoms`'s distractors to mention ring atoms, as its
  message says, clears it. At the four saved revisions `case_gap` states what each design
  lacked; at `31b67427`'s ring claim it reads "add at least 1 more counting case of either form".
- Six more replays on `claude-opus-5`, $2.31. `84e90683`'s scope case, whose reviewer wrote that
  a subject applying the claim "answers 2 to both and fails" and counted both: caught in one v7
  sample of two, and in the one sample under its original v5. `ring-no-lone-ring-atoms` with
  the word cue removed counted in all three samples, v6 or v7, the reviewer reading "a ring is
  matched in full or not at all" broadly; one v7 reviewer wrote that an atom-level reading
  "would give 2" and counted the case anyway. The claim-only rule does not reliably change
  this model's scope verdicts, so a case the planner rewrites to pass the new checks can keep
  a scope problem that nothing catches.
- Prototyped the claim-only answers on eight saved ring questions ($0.49; open question 12
  has the results), then built them as fix 7. Verification: suite 327 → 337 tests, with 334
  passing, 2 skipped and the machine-only failure. The new tests cover the split rule, faults
  and substituted models, reuse, a requested stop, the caller's deadline in worker threads,
  counting and the report, and forty concurrent log emits. Fifteen one-line mutations of the
  probe were each caught. The one removing the log's thread lock was caught only after a test
  simulated POSIX file locks, which admit every thread of one process; Windows's do not.
- Ran the built `claim_probe()` live, with the real adapter and a real workflow log, over the
  whole saved ring designs of `3b3f3c94` (its lone-ring case rewritten as qualification now
  forces) and `84e90683`: 22 sessions, $0.61, 28 s and 61 s. Missed: `cro-pentane-cyclohexyl`
  and `cro-aziridine-series` in both answers, `cro-cyclobutyl-cyclohexyl` and the "more
  intuitive" scaffold in one of two. Reached: all six other cases, among them the rewritten
  lone-ring case, answered 4 both times. The log kept one unbroken chain of 264 events.

In the `84e90683` session:

- Cleaned `3dc02567` into the session scratchpad and ran `84e90683`. Report
  `.verifier/runs/84e90683-1e8f-4712-bf32-a8754c0322e7/report-card.md`, workflow log
  `.verifier/attempts/74972df6-1d0d-46d6-b341-05fd8f918e70/workflow.md`. Cost: planner
  $10.74, 36 subject sessions $4.21, four critiques $0.96, assessor $0.14; the two timed-out
  sessions are unpriced.
- Checked the failure against its source. RDKit's own `test4RingMatches` asserts 3 atoms for
  `completeRingsOnly=True` on `CCCCC` and `CCC1CCCCC1`, so the key was right and the
  subject's `2` wrong. The timed-out trials ran `import rdkit` and `pip install rdkit`, then
  thought until they were killed.
- Implemented the six fixes in `local-contract.md`, `tool-contracts.md`,
  `artifact-contracts.md`, `evidence-rubric.md`, `LOCAL-CONFIG.md`, `local.py`,
  `documentary.py`, `subject_server.py` and `images/rdkit/`.
- Verification: suite 315 → 319 tests, with 318 passing, 2 skipped and the one machine-only
  failure under "Current state". Twelve one-line mutations of the fixes were each caught.
  `test_recorded_replies.py` rebuilds v5 from v6 and pins its digest, `bf944269…`. The image
  was checked through the verifier's own `DockerSandbox` and subject tool, as user 65534
  with no network. RDKit 2026.03.6 and pandas 3.0.6 import, the six ring-option questions
  return 3, 2, 3, 2, 3 and 5 as RDKit's tests assert, and an ACS1996 SVG draws.
- Not verified: any of the six fixes live, and still the effect of
  `CLAUDE_CODE_NO_MODEL_FALLBACK` and `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK`.
- Considered and not done: requiring execution before D (declined); a Python check that
  objections agree with verdicts, since 26 of the two runs' 92 objections and revisions name
  a counted case legitimately; reporting the first attempt's answers (declined); a longer
  subject limit (deferred by the operator).

Earlier today, in the `3dc02567` session: `2d9f8af`'s six fixes, with the suite 301 → 315,
seventeen mutations caught and two new recordings replayed through the real subject adapter.
That run took 90 minutes, 8 s inside the limit.

### Before the next run

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:127711447fe5260556ae724850ef4186a79ea774ec119ebb01c3775240f5264e`
   (`sci-verifier-rdkit:2026.3.6`, built from `images/rdkit/` as `LOCAL-CONFIG.md` says).
2. **A new Code-tab session after the commit that carries these fixes.** Every session, new
   or resumed, starts its own `serve-local`, and a resumed one keeps the code it started
   with; restarting the app is not needed. After the run, the run itself settles it:
   `run.json`'s `local_method_ref` must equal the tree's digest, printed by
   `python -c "import sys; sys.path.insert(0, 'src'); from sci_ai_verifier.storage import implementation_bytes; from sci_ai_verifier.common import digest; print(digest(implementation_bytes()))"`.
3. **The model is `claude-opus-5`.** The probe stops a run the CLI cannot serve.
4. **The working tree is clean** at that commit, or at a later one that did not touch `src/`.
5. **The plan's 5-hour window has room**; `3b3f3c94` cost about $19, `31b67427` $17,
   `84e90683` $16 and `3dc02567` $35.
6. **The timeout.** The app passes 5,400 s; three claims took 40 minutes, four took 43 to 46 and
   six took 90. A fallback needs up to nine minutes of the time left.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `3b3f3c94`:

- `.verifier/runs/3b3f3c94-6892-4de7-a09e-a37f2092ef00`
- `.verifier/attempts/7deed1ed-05b8-46d3-b919-0b22c1035c31`
- `.verifier/subject-runs/3b3f3c94-6892-4de7-a09e-a37f2092ef00`
- the **seven** candidates in `.verifier/candidates/` at `local-reference-comparison-5`, one of
  them a rejected qualification

**Keep** the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs, and
the five candidates at `local-reference-comparison-1`. Leave `.verifier/store/` alone. Do not
leave a shell inside a directory you are moving.

### What to check in the run

`verify_skill` returns 150–350 KB, which overflows the tool result; read
`.verifier/runs/<run>/report-card.json` on disk.

1. **The new code ran.** `run.json`'s `local_method_ref` matches the tree, every critique's
   `rubric_ref` is v7,
   `58b2509c3e8799cf55cf60033edcb7e2d550d4ce8821295cb4daeddbeaba7aa9`, and every candidate is
   at `local-reference-comparison-6`.
2. **RDKit.** Which subjects ran it, and did they compute an answer or print documentation?
   Any `claude_timeout`, and what was the subject doing? Quote the events.
3. **The fallback.** Did any claim carry `fallback`? Its status and reason, and the record's
   first limitation line.
4. **Critique v7.** Did any critique still count a case its own objection placed outside the
   claim? Quote every `beyond_scope` verdict, and say which rest on the claim-only answer.
   Did any counted case fail a trial whose reply applied the claim? Quote the reply.
5. **Leaks.** Quote every qualification refused for a correct option that starts alone or
   alone repeats a word of the question, and count the rewrites they cost. In every counted
   `choice` case, is the key written like its options? The `leaked` count.
6. **Grades.** Quote every `case_gap` summary and say what the planner did next. Did it accept
   a settled grade below its proposal while a replacement round remained? Quote its reason.
7. **Effect-to-setting cases.** Did the planner design any, and did the critique count them?
8. **Claim-only answers.** Quote every `missed` case with its answers and key, and say whether
   it was a scope problem or a slip, from the session's full reply in `workflow.jsonl` (role
   `claim_probe`). Did any `unmeasured` case occur, and why? What did the answers cost in money
   and minutes, and how many were reused?
9. **The rest.** Any refusal (quote the `model_refusal_*` events), `invalid` still zero, the
   claim count and the run time.

### Reading the results without fooling yourself

- **Before calling any `fail` a finding about the skill, read the observed reply, the expected
  answer and the reference quote verbatim.**
- **A unanimous `none of these`** means a broken case far more often than a wrong subject.
- **`claim-00N` directories under `subject-runs/` do not follow the report's order**, and a
  re-run's trials sit in `claim-NNN-retry`. Map them by `case_id`.
- **`subject_refused` or `subject_model_changed`: read the trial's `system` events** in the
  workflow log (`model_refusal_*`) before advising anything. A refusal may or may not recur.
- **A `claude_timeout` can come from the case itself.** Trace the subject's commands and
  thinking before promising that a re-run or a longer limit fixes it.
- **A run the runner closed should say `agent_unavailable`** with the planner's own reason; one
  that still says "The operator cancelled this run." for a stop nobody made means old code.
- **`workflow.jsonl` truncates long tool results** at about 16 KB; every tool call's whole
  request and result, including every critique round, is in `.verifier/runs/<run>/events/`.
- **With RDKit in the image, a subject can compute an answer instead of recalling it, or look
  it up.** A pass then says the skill-guided subject ran RDKit correctly, a different statement
  from knowing it. In `31b67427` two trials printed `rdFMCS.MCSParameters.Threshold.__doc__`,
  their case's key word for word.
- **A counted case can still turn on a finer fact than its claim.** In `3b3f3c94` the only
  failing trial applied the skill's "partial rings" and rejected the atom-level docstring
  "lone ring atoms". Compare such a reply with the claim's wording before calling it a finding.
- **A fallback D rests on its cases' quotes alone.** Read it as documentary, never as behaviour.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct.
2. **Claim coverage.** `3dc02567` extracted six claims, `84e90683` four, and `74eadedd` and
   `31b67427` three.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. Their case is semantic, but a subject could still
   lowercase one.
4. **Recognition.** The fifth leak shape covers one tell; a subject can still pick the
   conventional-looking option.
5. **Reviewers and planners disagree across runs.** Spare cases absorbed two rejections in
   `3dc02567` and five `duplicate`s in `3b3f3c94`. Whether an effect-to-setting case counts is
   now decided: it does. Planners still differ elsewhere, as on whether "8 of 10 → 0.8" is the
   reference's value or the planner's arithmetic.
6. **A claim Opus 5 refuses cannot be verified on Opus 5.** If the re-run is refused too, the
   report says so, and that is the finding: a provider limitation, not the skill's.
7. **Other operational endings.** Only subject-trial faults get a fallback D; a claim ended by
   `critic_unavailable` or by the planner still reports nothing. Should they get one?
8. **Knowledge or execution.** With RDKit available, should some cases stay questions a
   subject must answer without running code? In `31b67427` a documented-phrase case was
   answered by printing the docstring that is its key.
9. **Accepting a lower grade.** The rubric lets the planner accept a settled grade. In
   `31b67427` it accepted B one counting case short of A, with a replacement round unused, on a
   misreading of what A needs. Should acceptance wait until the replacement rounds are spent?
   `3b3f3c94` did not repeat it: its pIC50 claim was redesigned to A rather than accepted at B.
   Not changed; the revision reply now states the case gap instead.
10. **How strict qualification should be.** It now refuses a correct option that alone starts
    differently or alone repeats a word of the question, which would have refused 11 of the
    last three runs' 30 choice cases. If rewrites start to cost more than the leaks did,
    should the repeated-word check drop to a warning the critique sees? The "log" among
    "logarithm"s trace stays with the critique.
11. **The prior-review trigger.** It refused a first proposal for "a reviewer may judge one of
    each pair to add little independent evidence", a sentence about the coming review. It cost
    no session; should it match only references to an earlier review?
12. **How many claim-only answers per case.** Fix 7 measures the claim-only answer twice. Its
    prototype, on eight saved ring questions ($0.49), gave the claim as its statement and
    expected behaviour to fresh no-tool sessions and scored each answer with the question's
    own method. Over two samples it missed no fair question in 8 answers. It missed the key of
    all four questions reviewers had counted or disputed: `cro-pentane-cyclohexyl` and
    `cro-aziridine-series` in both samples, a claim-faithful "2" against the key "3"; the
    tutorial's "more intuitive" scaffold in both; and `ring-no-lone-ring-atoms`, its word cue
    removed, in one of two, answering `none of these` because "the claim does not settle that
    phrasing". Given only the skill's sentence instead of the claim, it passed two of the four.
    The built code then answered that lone-ring case 4 both times, so it has been missed in one
    answer of four. Two answers catch a case that faithful readers split on in that proportion
    about half the time. A third answer would raise the catch rate for about $0.03 a case, and
    no fair question has been missed in 20 answers. Should it be three?

### Deferred, and why

- **Parallel trials** — the operator agreed it is a good design. It is not built: the sandbox is
  configured with one CPU, and parallel sessions spend the usage window faster, so both need a
  decision first. Running a case's three trials at once would cut about 29 minutes of trials to
  about 10.
- **Opus 5.5** — until WinGet offers Claude Code 2.1.280; the startup probe now catches a
  premature switch.
- **A longer subject limit** — the operator will raise `subject_timeout_seconds` when a large
  skill needs it; the report now names the limit whenever it stops a trial.
- **The case-level contract** — flagged do-not-implement until four or five case-type rules
  accumulate; `a202146`'s answer forms and case verdicts overlap it, unreviewed. Design in the
  archive, 2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18. `images/rdkit/` is the manual path it would automate.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-24"). Follow its preflight, clean the previous run as it
describes, and use scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\sar-analysis"

Show me the report and workflow-log paths, a table with one row per claim
(grade, accuracy, consistency, status and the other measurements) and, for each
claim, a table with one row per test. Tell me whether it is a good run, and
whether our fixes work: go through the entry's "What to check in the run" list
item by item. Before concluding anything from a `fail`, an `invalid`, a refusal
or a unanimous "none of these", quote the verbatim reply or event behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None for the code, which is committed and pushed with this entry. Before the next live run,
start a new session: a session started before this commit runs a `serve-local` with older
code. A run now also spends about $0.03 per case per claim-only answer; the first round of a
six-case claim adds about a minute.

### Suggested next move

Run `sar-analysis` once on this code, and read the claim-only answers, the critiques'
`beyond_scope` verdicts, any qualification refusals and any `case_gap` reply rather than the
grades.

### Recommended next action

In a new session after the commit, clean `3b3f3c94` as above and run once. It is finished when
every item under "What to check in the run" has a recorded answer.

## Claude: 2026-09-25 (run d416f79d; a log that keeps up with its readers, reused answers under their case's ID)

### Current stage and status

Version 0.7.0, local workflow. Run `d416f79d`, on `da7605b`, ran from 22:58 to 23:50 PDT on
2026-09-24 and completed four claims, all passing at B:

| Claim | Status | Grade | Accuracy | Note |
| --- | --- | --- | --- | --- |
| FindMCS `threshold` | pass | B | 12 of 12 | four counting cases, two open |
| `completeRingsOnly` / `ringMatchesRingOnly` | pass | B | 9 of 9 | round 1 lost `ring-atom-count` to the claim-only answers; one `duplicate` |
| pIC50 | pass | B | 9 of 9 | three counting cases, one open |
| dummy atoms / `makeDummiesQueries` | pass | B | 9 of 9 | one `leaked`; one case `unmeasured` |

It used 3,096 s of the 5,400 s limit and cost about $18.90: planner $12.21, 45 subject
sessions $4.69, six critiques $1.56 and 40 claim-only sessions $0.42. All 39 counted trials
passed, with no `invalid`, fault, refusal, timeout, fallback, re-run or model change. It is the
first full run of the 2026-09-24 fixes, and the claim-only answers did what they were built
for: both answers to the ring claim's `ring-atom-count` gave `2` against RDKit's `3`, the split
behind `84e90683`'s failure, and the case left the design before any trial ran.

It exposed two defects in the verifier, fixed in this session with contracts first. Neither
changed a counted case or a grade. **The fixes are tested and pushed to `main` in the commit
that carries this entry, but have not met a live run.**

1. **The workflow log starved its pipe readers.** Every write re-read and re-verified every
   earlier event file, and the path check behind each read lstat'ed every parent directory. A
   write took about 0.09 s around the 350th event and 0.94 s by the 2,100th. The readers logged
   as they read, so with four claim-only sessions sharing the lock a reader fell more than the
   5 s drain grace behind its exited process. Two finished claim-only sessions were read as
   `claude_incomplete`, leaving two cases `unmeasured`. Four more kept their answers but lost
   their last lines from `workflow.jsonl`: `StreamLog.close()`, called on another thread,
   flushed the unread remainder as one unparseable line. The gap between a trial's wall time and
   the CLI's own time grew from 2.0 s in claim 1 to 6.1 s in claim 4. Now the readers only read,
   the thread waiting for the process logs its stream and returns exactly what it logged, and a
   write reads back only event files it has not verified or whose size or modification time
   changed. `local-contract.md` "Acceptance" owns the rule.
2. **Reused claim-only answers kept an earlier round's case ID.** The planner renamed
   `ring-which-argument` to `ring-prevent-argument` without changing it, and its reused answers
   were reported under the old name. Counting matches misses by ID, so a renamed miss would still
   have counted. The answers now carry the current ID. `select_local_candidate` in
   `tool-contracts.md` owns the rule.

Why neither touched the result: a slow reader loses only the end of a session's output, and an
answer is recorded only once the final `result` line has arrived, so nothing partial was scored.
All 45 subject sessions, the six critiques and the planner have complete logs. The two lost
answers belonged to cases the critique had ruled `leaked`, and a claim-only answer can only drop
a case from the count. The renamed case asks the same question, with the same input, key and
method, and its answers were `reached`; only a `missed` answer affects counting.

### What has been done

In the session of run `d416f79d`, started at 22:55 PDT on 2026-09-24 after `da7605b`:

- Preflight as the 2026-09-24 entry lists it: Docker 29.8.0 with the pinned image; this
  session's own `serve-local` started six minutes after `da7605b`; `claude-opus-5`; a clean
  tree; 27 % of the five-hour window used.
- Cleaned `3b3f3c94` into the session scratchpad: 2,458 files, counts and bytes matched.
- Ran `d416f79d`. Report `.verifier/runs/d416f79d-dbf4-4c0b-a5e1-69f53c5772c8/report-card.md`,
  workflow log `.verifier/attempts/2275addb-174d-4ac5-9db8-325bf15593bb/workflow.md`.
- Checked it against "What to check in the run"; the answers are below.
- Traced both defects to the code and measured the log on a copy of the run's 2,430 events: a
  write took 2.34 s there, of which 2.00 s path checks, 0.23 s reads, 0.06 s rewriting the two
  timelines and 0.04 s parsing and digests.
- Fixed both in `local-contract.md`, `tool-contracts.md`, `claude_runner.py`, `runlog.py` and
  `documentary.py`. Verification: suite 337 → 341 tests, with 338 passing, 2 skipped and the
  machine-only failure under "Current state". Three of the four new tests fail on `da7605b`'s
  code: a slow observer loses a finished process's output and runs on the reader thread; a write
  re-reads every file; a reused answer keeps the old ID and its miss counts. The fourth, a
  changed event still detected, guards the new cache; the old code passed it by reading
  everything. Six one-line mutations of
  the fixes were each caught. Each test run compiled into its own bytecode cache: a same-size
  mutation restored within the same second had left a `.pyc` that still looked current.
- On the same copy the fixed log writes in 0.034 s. A process opening a 2,430-event log for the
  first time verifies it once, in 2.5 s.
- Not verified: either fix live. The two timelines are still rewritten whole on every write,
  0.06 s at 2,430 events.
- Later, at the operator's request: corrected `local-contract.md`, whose paragraph on the
  installed policy still said that invalid observations prevent a grade and that trials must
  agree unanimously for one. That was true when written in `f7293ec` (2026-09-12); since the
  six-axis report card, `670033f` (2026-09-21), `decide()` keeps the settled grade and both
  change only the status and the execution limits, as `evidence-rubric.md` says. The local
  planner receives that file in full, so every local run since 2026-09-21 was given the old
  rule. The paragraph now states the current rule and names its owner. Suite unchanged: 338
  passing, 2 skipped, the machine-only failure.

Against "What to check in the run" of the 2026-09-24 entry:

1. **The new code ran.** `local_method_ref` matched the tree's `98882e6b…`, all six critiques
   carried v7's `58b2509c…`, and all six candidates were at `local-reference-comparison-6`.
2. **RDKit.** No subject ran it, or any command: all 45 trials used only the Skill tool, in
   three turns each. No `claude_timeout`.
3. **The fallback.** Not exercised; nothing stopped a claim.
4. **Critique v7.** One `beyond_scope`, the ring claim's first-round `ring-atom-count`, which
   the claim-only answers also missed. No critique counted a case its own objection placed
   outside the claim: every objection to a counted case questioned its strength. No counted
   case failed a trial.
5. **Leaks.** No qualification was refused, so the leading-word and repeated-word checks cost
   no rewrite and did not fire. Two `leaked` verdicts, both claim 4's. One counted key stands
   alone among its options: `thr-proportion-of-what`'s "the dataset" is the only option naming
   the molecule set. Its critique objected to exactly that and counted it; claim 4's critique
   ruled the same shape `leaked`.
6. **Grades.** Two `case_gap` replies. The ring claim's first round: "This design has 1 counted
   case, 1 generated: add at least 2 more counting cases of either form. The critique's own
   grade is none, so its objections need answering as well." The dummy claim's: "This design
   has 2 counted cases, 1 generated: add at least 1 more counting case of either form." Both
   times the planner replaced the rejected cases and the next critique supported B. It never
   accepted a grade below its proposal. It proposed B for all four claims, and each
   `stronger_grade_considered` names why no further independent case with a quotable key
   existed. The dummy claim's critique did not accept that reason: "rdkit.Chem.rdmolops
   documents AdjustQueryProperties as a module function on the same page", so a second
   generated case "appears to have been available"; with four counting cases it would still
   have been B.
7. **Effect-to-setting cases.** Three designed, all counted: `thr-which-property`,
   `ring-prevent-argument` and `dummy-which-field`.
8. **Claim-only answers.** One miss, `ring-atom-count`, answered `2` twice against the key `3`
   that RDKit's test asserts: a scope problem, not a slip. One reply: "The claim, applied
   literally, bars any partial-ring fragment from the MCS. … any single ring carbon would be a
   partial-ring fragment". Two `unmeasured`, both from the log defect. 40 sessions, $0.42 for
   the 38 that returned, about 2.3 minutes over six rounds; six answers reused.
9. **The rest.** No `model_refusal_*` event, `invalid` zero, four claims, 3,096 s.

### Before the next run

1. **Docker Desktop is running** and the pinned image is present:
   `sha256:127711447fe5260556ae724850ef4186a79ea774ec119ebb01c3775240f5264e`
   (`sci-verifier-rdkit:2026.3.6`, built from `images/rdkit/` as `LOCAL-CONFIG.md` says).
2. **A new Code-tab session after the commit that carries these fixes.** Every session, new or
   resumed, starts its own `serve-local`, and a resumed one keeps the code it started with.
   After the run, `run.json`'s `local_method_ref` must equal the tree's digest, printed by
   `python -c "import sys; sys.path.insert(0, 'src'); from sci_ai_verifier.storage import implementation_bytes; from sci_ai_verifier.common import digest; print(digest(implementation_bytes()))"`.
3. **The model is `claude-opus-5`.** The probe stops a run the CLI cannot serve.
4. **The working tree is clean** at that commit, or at a later one that did not touch `src/`.
5. **The plan's 5-hour window has room**; `d416f79d` cost about $19, `3dc02567` $35.
6. **The timeout.** The app passes 5,400 s; three claims took 40 minutes, four took 43 to 52 and
   six took 90. The log fix removes most of the late-run overhead; by how much is unmeasured.

### Cleaning the previous sar-analysis run

Move, do not delete, into the session scratchpad. The previous run is `d416f79d`:

- `.verifier/runs/d416f79d-dbf4-4c0b-a5e1-69f53c5772c8`
- `.verifier/attempts/2275addb-174d-4ac5-9db8-325bf15593bb`
- `.verifier/subject-runs/d416f79d-dbf4-4c0b-a5e1-69f53c5772c8`
- the **six** candidates in `.verifier/candidates/` at `local-reference-comparison-6`, all
  qualified

**Keep** the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs, and
the five candidates at `local-reference-comparison-1`. Leave `.verifier/store/` alone. Do not
leave a shell inside a directory you are moving.

### What to check in the run

`verify_skill` returns 150–350 KB, which overflows the tool result; read
`.verifier/runs/<run>/report-card.json` on disk.

1. **The new code ran.** `run.json`'s `local_method_ref` matches the tree, every critique's
   `rubric_ref` is v7, `58b2509c3e8799cf55cf60033edcb7e2d550d4ce8821295cb4daeddbeaba7aa9`, and
   every candidate is at `local-reference-comparison-6`.
2. **The log keeps up.** Every subject, critique and claim-only session has its `result` event
   in `workflow.jsonl`; no `process_unparsed_output`; no claim-only sample `claude_incomplete`.
   Late in the run, the gap between a trial's wall time and the CLI's `duration_ms` should stay
   near claim 1's 2 s, not reach `d416f79d`'s 6 s.
3. **Reused answers.** A claim-only case reused under a new name shows its current ID.
4. **Claim-only answers.** Quote every `missed` case with its answers and key, and say whether it
   was a scope problem or a slip, from the full reply in `workflow.jsonl` (role `claim_probe`).
   Any `unmeasured` case, and why. Cost, minutes and reused answers.
5. **Critique v7 and leaks.** Quote every `beyond_scope` verdict. Did any critique count a case
   its own objection placed outside the claim? Quote every qualification refused for a leak
   and count the rewrites; both checks have yet to fire live. The `leaked` count.
6. **Grades.** Quote every `case_gap` summary and what the planner did next. Did it accept a
   settled grade below its proposal while a replacement round remained? For each grade below
   A, did the critique accept the planner's `stronger_grade_considered`?
7. **RDKit and timeouts.** Which subjects ran commands, and did they compute or look up? Any
   `claude_timeout`, with the subject's events quoted.
8. **The fallback.** Did any claim carry `fallback`? Its status and reason.
9. **The rest.** Any refusal (quote the `model_refusal_*` events), `invalid` still zero, the
   claim count and the run time.

### Reading the results without fooling yourself

- **Before calling any `fail` a finding about the skill, read the observed reply, the expected
  answer and the reference quote verbatim.**
- **A unanimous `none of these`** means a broken case far more often than a wrong subject.
- **`claim-00N` directories under `subject-runs/` do not follow the report's order**, and a
  re-run's trials sit in `claim-NNN-retry`. Map them by `case_id`.
- **`subject_refused` or `subject_model_changed`: read the trial's `system` events** in the
  workflow log (`model_refusal_*`) before advising anything. A refusal may or may not recur.
- **A `claude_timeout` can come from the case itself.** Trace the subject's commands and
  thinking before promising that a re-run or a longer limit fixes it.
- **A `claude_incomplete` from a session that exited 0** was the log starving its reader until
  this fix. On the fixed code, it means this diagnosis was incomplete.
- **Trial wall times before this fix include log overhead** that grew through a run. Compare
  runs with the CLI's own `duration_ms`.
- **A run the runner closed should say `agent_unavailable`** with the planner's own reason; one
  that still says "The operator cancelled this run." for a stop nobody made means old code.
- **`workflow.jsonl` truncates long tool results** at about 16 KB; every tool call's whole
  request and result, including every critique round, is in `.verifier/runs/<run>/events/`.
- **With RDKit in the image, a subject can compute an answer instead of recalling it, or look it
  up.** In `31b67427` two trials printed a docstring that was their case's key word for word.
- **A counted case can still turn on a finer fact than its claim.** Compare a failing reply with
  the claim's wording before calling it a finding.
- **A fallback D rests on its cases' quotes alone.** Read it as documentary, never as behaviour.
- **A clean run is not proof of a fix** if the model never produced the case the fix handles.

### Drafted, not built: calculated answers for exact-maths claims

Raised by the operator after the run, on 2026-09-25; the operator will decide and build it on
2026-09-26. Nothing here is implemented.

**The problem.** A maths claim reaches A only if the planner finds a page that happens to print
enough worked examples. `local-contract.md` requires that "Reference quotes and expected values
must occur in retrieved material" at every grade, and `local-evaluator-spec.md` holds a
generated evaluator's expected value to its quote as well, so no grade accepts a calculated
answer. `evidence-rubric.md` defines A as "traceable or mathematically exact", with a
monoisotopic-mass calculation as its example; the local profile implements only the traceable
half.

**The evidence.**

- In `d416f79d` the pIC50 claim settled at B with three counting cases, one open (1 nM → 9), no
  case rejected, one review and 9 of 9 passing. The planner quoted ChEMBL's FAQ and Papadatos
  2015, which hold one worked conversion between them, and wrote that "a second numeric
  conversion would have no quoted expected value". Its critique agreed that A was "genuinely
  unreachable here rather than passed over out of convenience".
- Under the same case and quoting rules the claim reached A in `84e90683` and `3b3f3c94`, both
  from TeachOpenCADD T006, whose EGFR table lists IC50 and pIC50 side by side. `84e90683`
  counted five open conversions from it; `3b3f3c94` added a CDD blog and counted five cases,
  three open. `d416f79d`'s B came
  from the pages its planner chose, which neither Python nor the critique can see (open
  question 5).
- A quoted number is no safer than a calculated one. `3b3f3c94`'s first design keyed 30 nM to a
  page's "which is pIC50 = 7.5"; the exact value is 7.522879, and its critique caught it.
  `84e90683`'s `pic50-anchor-1nm` key `9` was quoted from "Number of compounds with pIC50 > 9:
  186", which contains the token but not the conversion: the token check proves presence, not
  support.
- Duplicates are not the obstacle. Critiques ruled a conversion `duplicate` only when nothing
  but the number changed (`84e90683`'s `pic50-inverse-b`, `3b3f3c94`'s
  `pic50-chembl-nondecade`); a change of unit or of direction counted.

**The proposed rule.** A calculated answer counts toward A for a mathematically exact claim when
all four hold:

1. The formula is quoted token-exactly from bytes Python retrieved, such as ChEMBL's
   "-Log(molar IC50, XC50, EC50, AC50, Ki, Kd or Potency)".
2. Python runs the planner's program in the pinned container `qualify_local_evaluator` already
   uses, never the planner's own arithmetic, and before any case uses it the program
   reproduces every worked example on that page, such as ChEMBL's 1 nM → 9. A wrong formula (a
   natural log, a dropped sign, a nanomolar number logged bare) fails there.
3. Scoring stays an installed comparison method. A slip in one case's input, such as µM entered
   as nM, is left to the claim-only answers: sessions computing from the claim miss the wrong
   key, and the case stops counting.
4. The report's AI involvement records that the planner wrote the program.

The formula has to be quoted because an answer calculated from the claim is circular. Had the
skill said pIC50 = -ln(IC50), a key derived from the claim would give 20.7 for 1 nM, the subject
following the skill would answer 20.7, and a wrong claim would pass. Under this rule
`d416f79d`'s two ChEMBL pages alone would have supported A: 1 nM, conversions in µM, pM and M,
and one in reverse.

**Still to decide.**

- The rule bends "A planner-authored scorer cannot reach A" in `local-contract.md`: the scorer
  stays installed, but the planner writes the program that produces the answers. Whether
  reproducing the page's worked examples keeps that outside "AI judgment in scoring or the
  verdict" is the operator's call.
- One worked example cannot catch a unit slip outside its own unit; there the claim-only
  answers are the only guard.
- Claim-only sessions have no tools and take the logarithm in their heads, so keys to six
  decimals, as both A designs used, could make correct cases miss. Neither design met the
  claim-only check, which came after them; two decimals are safer.
- Scope: exact maths first. Answers produced by running RDKit for RDKit claims stay under open
  question 8: there is no formula to quote, because the library is the reference; an answer
  holds only for the pinned 2026.03.6; and subjects have the same RDKit in their sandbox.

**Where it would go**, contracts first: the grade list and the "Reference quotes and expected
values" sentence in `local-contract.md`, which own the rule; `qualify_local_candidate` in
`tool-contracts.md`; `local-evaluator-spec.md` if the program travels in that specification;
then the code, tests and one live run. `evidence-rubric.md`'s A row already allows it, and
`workflow.md` changes only if a new tool is added, and none is planned.

### Open questions for the operator

1. **Should the aggregation rule become a plan field?** Still `unanimity`, still correct.
2. **Claim coverage.** `3dc02567` extracted six claims, `84e90683`, `3b3f3c94` and `d416f79d`
   four, and `74eadedd` and `31b67427` three.
3. **A narrow capitalization residue, by choice.** Tokens carrying both cases — `Core`,
   `Threshold`, `Fuc` — stay open answers. It now costs evidence: `d416f79d`'s threshold planner
   named it as the reason `Threshold` could not be a fifth, open case.
4. **Recognition.** The fifth leak shape covers one tell; a subject can still pick the
   conventional-looking option. `thr-proportion-of-what` counted although its critique wrote
   that the key could be reached "on general plausibility".
5. **Reviewers and planners disagree across runs.** In `d416f79d` one critique counted a key that
   alone names what the stem is about and another ruled that shape `leaked`. The threshold and
   pIC50 claims settled at B after reaching A in earlier runs. For pIC50 the cause was the pages
   the planner chose; see "Drafted, not built" above.
6. **A claim Opus 5 refuses cannot be verified on Opus 5.** If the re-run is refused too, the
   report says so, and that is the finding: a provider limitation, not the skill's.
7. **Other operational endings.** Only subject-trial faults get a fallback D; a claim ended by
   `critic_unavailable` or by the planner still reports nothing. Should they get one?
8. **Knowledge or execution.** With RDKit available, should some cases stay questions a subject
   must answer without running code? In `d416f79d` every B rested on sources that quote only
   three or four independent facts, and the ring planner wrote that "Executing RDKit to measure
   a fresh consequence is not available to this verifier for this claim".
   `qualify_local_evaluator` has never run. Is an executed key the route to A for narrow API
   claims? For exact maths, "Drafted, not built" above proposes one; answers produced by
   running RDKit stay open here.
9. **Accepting a lower grade.** In `31b67427` the planner accepted B one counting case short of
   A with a replacement round unused. Neither later run repeated it. Not changed; the revision
   reply states the case gap instead.
10. **How strict qualification should be.** Its two leak checks would have refused 11 of the 30
    choice cases before them, yet refused none of `d416f79d`'s designs. If rewrites start to
    cost more than the leaks did, should the repeated-word check drop to a warning?
11. **The prior-review trigger.** It refused a first proposal in `3b3f3c94` for a sentence about
    the coming review, and did not fire in `d416f79d`. Should it match only references to an
    earlier review?
12. **How many claim-only answers per case.** Two answers caught `d416f79d`'s one miss, which both
    answers made. A case missed in one answer of four, as `3b3f3c94`'s lone-ring case was, slips
    past two answers about half the time; a third answer cost about $0.01 a case in `d416f79d`.
    Should it be three?

### Deferred, and why

- **Parallel trials** — the operator agreed it is a good design. It is not built: the sandbox is
  configured with one CPU, and parallel sessions spend the usage window faster, so both need a
  decision first.
- **Appending to the timelines** instead of rewriting them on every write — 0.06 s per write at
  2,430 events. Rewriting keeps each projection rebuilt from verified events.
- **Opus 5.5** — until WinGet offers Claude Code 2.1.280; the startup probe catches a premature
  switch.
- **A longer subject limit** — the operator will raise `subject_timeout_seconds` when a large
  skill needs it; the report names the limit whenever it stops a trial.
- **The case-level contract** — flagged do-not-implement until four or five case-type rules
  accumulate. Design in the archive, 2026-09-22.
- **Automatic dependency resolution** — flagged do-not-implement, design in the archive,
  2026-09-18. `images/rdkit/` is the manual path it would automate.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-25"). Follow its preflight, clean the previous run as it
describes, and use scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\sar-analysis"

Show me the report and workflow-log paths, a table with one row per claim
(grade, accuracy, consistency, status and the other measurements) and, for each
claim, a table with one row per test. Tell me whether it is a good run, and
whether our fixes work: go through the entry's "What to check in the run" list
item by item. Before concluding anything from a `fail`, an `invalid`, a refusal
or a unanimous "none of these", quote the verbatim reply or event behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None for the code, which is committed and pushed with this entry. Before the next live run,
start a new session: a session started before this commit runs a `serve-local` with older code.

### Suggested next move

Run `sar-analysis` once on the fixed code and read the log's completeness and timing, and any
claim-only answers reused under a new name, before the grades. Separately, the operator will
decide and build "Drafted, not built" above on 2026-09-26; open question 8 keeps the RDKit half.

### Recommended next action

In a new session after the commit, clean `d416f79d` as above and run once. It is finished when
every item under "What to check in the run" has a recorded answer.

---

## Claude: 2026-09-28 (reply schemas; calculated answers; run 0aeca4c6; skill environments)

### Current stage and status

Version 0.7.0, local workflow. Earlier this day two operator-requested changes were built,
committed and pushed as `265a095`:
- the verifier's own sessions (critique, documentary assessment, claim-only answers) now answer
  through a reply schema that Claude Code enforces;
- a maths claim's expected answers may be calculated by Python from a quoted formula.

Later, a new session ran **`0aeca4c6` on scikit-survival**, the first non-chemistry run since
glycoengineering:
- the reply schemas worked live;
- no planner wrote a calculation;
- the fallback D ran for the first time.

The run could execute nothing, because the pinned image lacks scikit-survival. So the operator
asked, by name, for the 2026-09-18 automatic dependency resolution design. It is now built, contracts
first, as **skill environments**: the packages a skill declares are downloaded in one step before
the run exists, and installed offline into an image that only its subject trials use.
**Skill environments build live on a blank base and are removed after each run, but have not yet
been used in a verifier run.** A Windows
long-path fix to temp cleanup was also made. The long-path fix is on `main` (`f61a97b`). At the
operator's request, skill environments live on this branch, `skill-environments`, until they have
been tested; this copy of the entry describes them.

### What has been done

In the session of run `d416f79d`, continued on 2026-09-28:

- `a7f023b`, pushed on 2026-09-25: the grade-rule correction in `local-contract.md` that the
  2026-09-25 entry records.
- The pIC50 claim's B traced to its planner's pages (the archived 2026-09-25 entry, "Drafted,
  not built"). The operator asked for that fix built, and asked why the verifier's replies were
  never held to a schema.

**1. Reply schemas.** Python parsed the three sessions' free text and learned each tolerance
after a lost reply: a code fence and a list-shaped field in `a392ea65`, a sixth finding in
`e035eef6`, an empty extra key in `0a243b7e`. Claude Code 2.1.268 has `--json-schema`; the
runner never passed it.

- Probed first, on the pinned model with the runner's own flags: five sessions, $0.13. Claude
  Code adds one `StructuredOutput` tool even under `--tools ""`, checks the reply against the
  whole schema (a `minLength` was enforced, so it validates rather than only constraining
  generation), hands a refused reply back to the session with the validator's message, and puts
  the reply in `structured_output` on the `result` event. A session whose replies could not meet
  the schema stopped as `error_max_turns`, exit 1.
- Built in `documentary.py`: `critique_schema`, `assessment_schema` and `CLAIM_PROBE_SCHEMA`; only
  the `StructuredOutput` tool is allowed; the reply is read from `structured_output`; a session
  that ends without a reply in shape is `<role>_response_invalid`. Case verdicts are keyed by case
  ID, so the schema itself demands one per packet case, and findings are exactly one per
  criterion. Python checks the reply again against the same schema with `common.validate`, which
  gained `anyOf` and `pattern`; the citation check stays Python's alone. Turn limit 2 → 4.
- Removed, because the schema prevents what they handled: the code-fence stripper, the
  lone-string, `null`-replacement, extra-finding and extra-key tolerances, the second fresh
  session for an unusable shape, judging a reply against an earlier rubric, the format paragraphs
  of the three system prompts (field meanings moved into the schemas' descriptions), the
  `attempts` record, and eight text-reply recordings with their tests.
- Recorded instead, live through the new code, $0.42: `d416f79d`'s pIC50 critique packet under
  rubric v8 (B, all three cases counted, as that run's critique judged them), `a392ea65`'s
  documentary packet, and one `d416f79d` claim-only case. **Two of the three first replies broke
  the schema**: the critique wrapped its reply in a stray `$PARAMETER_NAME` key and the
  claim-only answer added a stray `a`. Each session corrected it on the next call. Either would
  have been a lost reply before.
- Minimum Claude Code 2.1.248 → 2.1.268, the version the schemas were tested on
  (`LOCAL-INSTALL.md`). Contracts: the reply-shape paragraph under `select_local_candidate` in
  `tool-contracts.md`, which owns it, and the critique, assessor and fallback-budget paragraphs of
  `local-contract.md` (the fallback now needs one assessor session plus five minutes).

**2. Calculated answers**, built as the draft proposed. `qualify_local_candidate` in
`tool-contracts.md` owns the rule; `local-contract.md` (grade list, "Scope and evidence"),
`evidence-rubric.md` (the eligibility predicate) and `artifact-contracts.md` point to it.

- A design's `calculation` holds the program, the formula's reference and exact quote, and one to
  eight `anchors`, each a worked example quoted from a fetched page. A calculated case gives
  `arguments` and `decimals` (0 to 6); Python supplies its `expected`, rounded half away from
  zero, and its `reference_ref` and `source_quote`, the formula's. `local_evaluators.calculate`
  runs the program once per distinct argument in one container of the pinned image. Every anchor
  must reproduce at the precision its page prints, so run `3b3f3c94`'s rounded "which is pIC50 =
  7.5" for 30 nM passes as 7.522879.
- The receipts (program digest, image, outputs, anchors) let selection re-check a saved candidate
  without running it again; a catalog import runs it again. `traceable()` accepts a calculated
  answer whose anchors all reproduced, and the origin check covers the anchors' pages. Policy
  `evidence-strength-v5` → `v6`; critique rubric v7 → v8, adding `calculated_answers`. The critique
  sees the program whole, the formula, each anchor with its output and each case's arguments.
  `ai_involvement` says the planner wrote the program; the report card gains a `calculation`
  record, a "Calculated answers" line and each test's `calculated` arguments.
- With it, `d416f79d`'s two ChEMBL pages alone would support A for pIC50: the quote
  "-Log(molar IC50, XC50, EC50, AC50, Ki, Kd or Potency)" and the anchor "an IC50 measurement of
  1nM would have a pChEMBL value of 9" are both on its FAQ page.

Verification:

- Suite 341 → 349 tests: 346 passing, 2 skipped, the machine-only failure under "Current state".
- Seventeen one-line mutations of the two changes were each caught. The first pass missed one:
  selection not loading a worked example's own page went unnoticed, because the end-to-end test's
  example shared the formula's page. That test now fetches a second page.
- **Live sandbox check**, after the operator saw to Docker Desktop: the pinned image ran the
  program on six inputs in 1.3 s against the real ChEMBL page bytes. The anchor 1 nM → 9
  reproduced (the program printed 9.0); the keys were 3.60, 8.49, 9.02, 11.22 and 7.52 for 250 µM,
  3.2 nM, 950 pM, 6.0 × 10⁻¹² M and 30 nM; the ceiling at three trials was A with no limits. A
  natural-log program was refused: "The calculation gives '20.72326583694641' for the anchor with
  arguments '1e-9', where its reference prints '9'." The re-check from receipts ran nothing.
- Not verified: a critique of a calculated design, and either change in a verifier run.

Later on 2026-09-28, in a new session:

**3. Run `0aeca4c6`** (scikit-survival, 3,827 s, about $27 at API rates, 5-hour window 26% → 77%).

Results:
- Five claims: Coxnet at A; the CIF array, FastSurvivalSVM `rank_ratio` and GBSA `criterion`
  claims at B; Brier-score input at D by fallback.
- 62 of 64 obtained trials passed and none was invalid.
- The new code ran: `local_method_ref` matched the tree, and every critique ran rubric v8 under
  policy v6.
- The reply schemas held. All 59 of the verifier's own sessions ended with a valid structured
  reply, and 11 first replies refused for a stray key were corrected on the next turn.
- No planner wrote a `calculation`: no claim had a formula with a worked example.
- The log kept up: all 134 sessions have a `result` event and there was no unparsed output.

Problems it showed:
- **A content-triggered refusal voided the Brier claim.** Opus 5 flagged `brier-column-alignment`
  as `model_refusal_no_fallback`, category `reasoning_extraction`, in 4 of 4 sessions (2 per
  attempt) and in no other session. Trial 1 recovered and answered correctly; trial 2 ended with
  the error text, which stopped the claim. The end-of-run re-run repeated the pattern exactly.
- **Two correct answers were scored `fail`** because the reply opened with a code fence
  (```` ```python ````) and `exact` reads the first line. The case was uncounted, so the grade was
  unaffected.
- **Nothing could run.** No subject tried to import scikit-survival; all 113 commands read the
  skill's own files. All five planners said the library was not in the image, so every grade rests
  on scikit-survival's own documentation.
- Three B grades came from claims too narrow to supply five independent cases.

**4. Long-path fix.** The test that failed only on this machine, and the `%TEMP%` leftovers behind
it, had one cause:
- Claude Code saves large tool results 273–277 characters deep in the controller's temp folder.
- `LongPathsEnabled` is 0 on this machine, so Python could not see those files.
- `shutil.rmtree` therefore skipped them silently.

The fix:
- `extended_path()` in `claude_runner.py` gives both the per-session cleanup and the startup sweep
  the `\\?\` form.
- Two regression tests failed before the fix and pass after it.
- The 25 leftover folders were sent to the Recycle Bin at the operator's request.
- `local-contract.md` states the rule.

**5. Skill environments**, the operator's request with the constraint that package downloads
happen only in this step. `local-contract.md` "Skill environment" owns the mechanism;
`resource-policy.md` "Packages a skill declares" owns the trust decision.
- **Declarations** are read only from the skill's own snapshot, taken in setup exactly as
  `load_submitted_skill` will take it. They come from install commands in fenced Markdown blocks,
  `requirements*.txt` and `pyproject.toml` dependencies. Prose, URLs, paths, VCS references,
  markers, index options and installer packages are rejected. Import-only names are never installed.
  On the real skills: scikit-survival gives its 10 pins, sar-analysis nothing, and
  glycoengineering's `uv pip install -e .` is rejected.
- **The build** runs in setup, after the model probe and before the run or planner exists. It
  starts from `environment_base_image`, a plain Python image the operator pins, never from
  `sandbox_image`:
  1. a resolver container, the only container with a network, runs `pip download` for wheels only;
  2. Python checks and hash-locks the wheels;
  3. an offline installer applies the lock with `--require-hashes`, then `pip check`, under the
     base's own empty entrypoint;
  4. `docker commit` makes an image tagged for this build alone.

  Any failure stops the run before a planner is spent.
- **Removal.** The image is removed when the verification ends, however it ends. Setup also
  removes environment images more than a day old that a killed verification left behind. Nothing
  is cached, so each verification rebuilds, which took about 30 s.
- **Only subject trials use the built image.** Calculations, evaluators, scoring and catalog
  requalification keep the operator's image, so no package the skill chose runs where keys are
  produced or trials scored. The image is folded into the subject identity (`--subject-image` to
  the internal server) and `environment_digest` includes the record.
- **The planner** gets a pinned block rendered only from checked values, and the full record as the
  `environment` context section. A skill changed between setup and `load_submitted_skill` ends the
  run as `source_changed`.
- **Settings:** `package_index` (null by default), `environment_base_image` (required with it),
  `max_package_bytes` and `max_packages`.

Verification of items 4 and 5:
- Suite 349 → 385 tests: 383 passing, 2 skipped, none failing.
- 34 tests in `test_environment.py` run on fake Docker. Among them, a guard checks that only
  `environment.py` gives a container a network.
- Twelve one-line mutations of the first design's safeguards were each caught.
- `resource-policy.md`'s new section was kept short so that the historical verification profile's
  bootstrap stays under its 200,000-byte test bound (199,805).
- **First live build**, of scikit-survival on the RDKit image, which was the base then:
  - 10 pins resolved to 16 wheels (79 MB) in 30 s, and `pip check` passed;
  - an offline container imported `sksurv` and computed a competing-risk CIF of shape `(3, 6)`;
  - a second call reused the image with no download.

  It showed two faults, both fixed:
  - the environment carried RDKit's 670 MB and had numpy and pandas swapped under it;
  - Docker ignored the `ENTRYPOINT []` reset, so the image kept `python3` as its entrypoint.
- **Live re-check on `python:3.12-slim`:**
  - the same lock, digest `9679b819…`, came out again in 30 s;
  - entrypoint empty, 695 MB, and scikit-survival works;
  - RDKit is absent;
  - the image was gone after `remove_environment`;
  - the sweep ran;
  - `package_index` null gave `disabled`.

  No container or volume was left behind. The operator's settings file was not edited.
- **Not verified:** a verifier run in a built environment.

### Decisions taken 2026-09-28

- **Build both, and delete what the schema makes unnecessary** (operator).
- **Schemas for the verifier's own sessions only.** Subject replies keep the first-line reader:
  the subject is the skill under test, and a schema would change its session and could clash with
  the skill's own output format. Open question 3.
- **A planner-written program may key a grade-A answer** (operator, confirmed after the build).
  The planner writes a fresh program for each claim rather than the verifier holding a reviewed
  calculator; the quoted formula, the reproduced worked examples and the disclosure in the report
  are what make it acceptable. The rubric's A is "traceable or mathematically exact", and the
  local profile had implemented only the first.
- **Build automatic dependency resolution** (operator, by name, lifting the 2026-09-18
  do-not-implement flag), **with package downloads only in that one step**. This supersedes the
  "Deferred" entry and "Dependencies must already exist in the pinned image".
- **A failed build stops the run in setup** (operator), before any planner cost; `package_index`
  null runs on the operator's image instead.
- **Only declared installs** (operator): names inferred from imports are never installed.
- **Subject trials only** (approved in the plan). The verifier's own calculations, evaluators and
  scoring keep the operator's image, which also leaves open question 2 open.
- **Keep skill environments on their own branch** (operator): `skill-environments`, until they have
  been tested. The operator may still change them before any merge.
- **Build on a blank base** (operator, after the first live build). Environments start from a plain
  Python image (`environment_base_image`), never from the RDKit image. This corrects the plan's
  choice of `sandbox_image` as the base, which contradicted what had been proposed to the operator.
- **Delete each built image after its run** (operator), rather than caching it: nothing
  accumulates, at the cost of about 30 s and an 80 MB download per run.
- **Delete the 25 leftover temp folders** (operator). They went to the Recycle Bin, not
  permanently.

### Before the next run

1. **Docker Desktop's engine is running** (`docker info` prints a server version) and the pinned
   image is present:
   `sha256:127711447fe5260556ae724850ef4186a79ea774ec119ebb01c3775240f5264e`
   (`sci-verifier-rdkit:2026.3.6`). On 2026-09-28 launching Docker Desktop alone left the
   `docker-desktop` WSL distro stopped; the engine came up once the operator saw to the app.
2. **A new Code-tab session after the commit that carries these changes.** A resumed session
   keeps the `serve-local` it started with. After the run, `run.json`'s `local_method_ref` must
   equal the tree's digest, printed by
   `python -c "import sys; sys.path.insert(0, 'src'); from sci_ai_verifier.storage import implementation_bytes; from sci_ai_verifier.common import digest; print(digest(implementation_bytes()))"`.
3. **Claude Code is 2.1.268 or later** and the model is `claude-opus-5`.
4. **The working tree is clean** at that commit.
5. **The plan's 5-hour window has room.** `0aeca4c6` cost about $27 and took the window from 26%
   to 77%, so plan one run per window.
6. **The timeout.** The app passes 7,200 s, the most `serve-local` accepts; the operator raised it
   from 5,400 s on 2026-09-29, and a session started before that still serves 5,400 s. `0aeca4c6`
   used 3,827 s for five claims, and each environment build adds about 30 s of setup.
7. **For a skill environment**, the operator adds two settings to `.verifier/local-settings.json`:
   - `package_index: "https://pypi.org/simple"`;
   - `environment_base_image:
     "sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea"`, the local
     `python:3.12-slim`.

   Each run downloads the scikit-survival stack, about 80 MB of wheels.

### Cleaning the previous run

Move, do not delete, into the session scratchpad:
- `.verifier/runs/0aeca4c6-5f2c-4d72-87a4-e8452340a5dc`
- `.verifier/attempts/f32cd389-5e51-4b87-adb9-b17de85e397d`
- `.verifier/subject-runs/0aeca4c6-5f2c-4d72-87a4-e8452340a5dc`
- the nine candidates it wrote at `local-reference-comparison-6`, dated 2026-09-28

Keep the glycoengineering run `76ce4af1-…`, its attempt `a1ec3e49-…`, its subject-runs and its five
candidates. Leave `.verifier/store/` alone: environment build records live there. `d416f79d`'s
files are already in an earlier session's scratchpad. Built environment images need no cleaning:
each run removes its own.

### What to check in the run

1. **The new code ran.** `local_method_ref` matches the tree, every critique's `rubric_ref` is v8,
   `499ff634d7fbd0e28780ecff9370a6bd587ab6354f1af57cd8dfe00073bbb1a7`, and the audits carry policy
   `evidence-strength-v6`.
2. **Reply schemas.** Every critique, assessor and claim-only session ends `success` with a
   `structured_output`. Count the sessions whose first reply Claude Code refused (a `tool_result`
   with `is_error` in the events) and quote the validator's messages. Any `*_response_invalid`,
   with its stream. How many turns sessions used.
3. **Calculated answers.** Did any planner write a `calculation`, the pIC50 claim above all?
   Quote its program, formula and anchors, any qualification it was refused, and what the
   critique said of the program under `calculated_answers`. The grade it settled at, and why.
4. **Claim-only answers on calculated cases.** Any `missed` at the case's rounding, with the
   answers and key: a reader working by hand, or a wrong key?
5. **Carried from 2026-09-25.** The log keeps up: every session has its `result` event, no
   `process_unparsed_output`, no claim-only `claude_incomplete`, late-run wall-time gap near 2 s.
   A reused claim-only answer shows its case's current ID.
6. **The rest.** Refusals (quote `model_refusal_*`), `invalid` still zero, claim count, run time.
7. **Skill environment.**
   - The setup log's `preflight.environment` status should be `built`, on `python:3.12-slim`.
   - The lock (digest `9679b819…` if nothing moved on PyPI).
   - That no `sci-verifier-env` image remains after the run.
   - The planner's pinned block.
   - Whether subjects now run scikit-survival or the skill's scripts.
   - Any docstring lookups of a key: trace `mcp__subject__run_command`, as with RDKit in `31b67427`.
   - Whether any planner designs an executed case.
   - That calculations and scoring still report the operator's image ID.

### Reading the results without fooling yourself

The 2026-09-25 list still holds (archived), with three additions:

- **A critique is one session now.** A reply Claude Code refused is visible only in the stream,
  as a `StructuredOutput` call answered by a `tool_result` with `is_error`.
- **A calculated case's `reference_quote` is its formula**, not its value; the value came from
  the program, whose anchors are in the report's `calculation` record.
- **A calculated key is exact at its rounding.** A subject that answers more decimals than the
  question asks for fails at the installed tolerance; read the question before the verdict.

### Open questions for the operator

1. **Is one anchor enough?** A worked example in nanomolar cannot catch a micromolar slip in a
   case's arguments; only the claim-only answers do.
2. **Answers produced by running RDKit** for RDKit claims: no formula to quote, since the library
   is the reference; an answer holds only for the pinned 2026.03.6; and subjects hold the same
   RDKit. Was open question 8's other half.
3. **Subject replies through a schema?** Not done, for the reason under "Decisions".
4. **From `0aeca4c6`**, proposed, not built:
   - **Refusals.** Replay the flagged question a few times on the pinned model first. If recovery
     is random, retry only the refused trial. If it is deterministic, let the planner reword the
     case instead of re-running the claim unchanged. Either way, show a stopped claim's obtained
     trials in its headline.
   - **Code fences.** Read the first line inside a fence for all three methods.
   - **Coverage.** A run sampled five narrow API facts and none of the skill's workflow advice.
   - **Narrow claims.** Say in the report when a B was limited by the claim's size rather than its
     source.
5. **From skill environments:**
   - Subjects can read installed docstrings, so doc-keyed cases can be looked up.
   - A fenced counter-example install line stops the run if it cannot resolve.
   - Should library output ever key an answer? That is open question 2.
6. **Carried from 2026-09-25**, detail in the archive: the aggregation rule as a plan field; claim
   coverage (three to six claims per run); the capitalisation residue; recognition cases passed on
   plausibility; planners and reviewers differing across runs (for pIC50 the cause was pages, now
   answered by calculated answers); claims Opus 5 refuses; a fallback for other operational
   endings; accepting a lower grade; how strict qualification should be; the prior-review
   trigger; two or three claim-only answers per case.

### Deferred, and why

Unchanged from 2026-09-25: parallel trials, appending to the timelines, Opus 5.5 (until WinGet
offers Claude Code 2.1.280), a longer subject limit and the case-level contract. Automatic
dependency resolution left this list on 2026-09-28, when the operator asked for it.

### Prompt for the next session

```text
Before anything else, read the latest entry in DEVELOPMENT-PLAN.md
("Claude: 2026-09-28"). Follow its preflight, clean the previous run as it
describes, and use scientific-verifier-local to verify this skill:
"D:\Su Lab\verifier-submissions\examples\scikit-survival"

Show me the report and workflow-log paths, a table with one row per claim
(grade, accuracy, consistency, status and the other measurements) and, for each
claim, a table with one row per test. Tell me whether it is a good run, and
whether our changes work: go through the entry's "What to check in the run" list
item by item. Before concluding anything from a `fail`, an `invalid`, a refusal
or a unanimous "none of these", quote the verbatim reply or event behind it.

Do not change code, commit or push unless I ask.
```

### Urgent next steps, if any

None blocking. Skill environments are committed on this branch with this entry and are not merged
into `main`. Testing them needs this branch checked out, and a new session started after that,
because a session started earlier runs a `serve-local` with the old code.

### Suggested next move

Run scikit-survival in a built environment. The build itself is proven live. The question now is
whether subjects execute the library once it is installed, and whether planners design executed
cases.

### Recommended next action

With the operator's go-ahead:
1. Add the two settings under "Before the next run", item 7.
2. Start a new session with this branch checked out.
3. Clean `0aeca4c6` as described above.
4. Run scikit-survival once.

It is finished when every item under "What to check in the run" has a recorded answer.

## Claude: 2026-09-29 (typed answers and the AI reader, on skill-environments; run d3892f6c)

### Current stage and status

Version 0.7.0, local workflow, on the `skill-environments` branch. The operator asked for one
general fix for replies that give the right answer in a form the scorer cannot read. The earlier
fixes had turned good open questions into multiple choice: `choice` went from no cases at method
versions 1 and 2 to 52–71% at versions 3 to 6, and 13 claim grades in 17 runs were capped for
want of generated cases. Two parts are built, contracts first, on top of the skill environments
of the 2026-09-28 entry:
- **Typed answers.** Seven installed answer types, one reader that finds the answer line past a
  code fence or an `Answer:` label, controls generated for each type, and one line Python adds to
  each case's input stating its answer form.
- **The AI reader.** A counted trial Python's reader does not pass is read again by a fresh no-tool
  session. Its reading decides that trial unless Python's checks refuse it. The grade stays, and
  the report shows every reading beside the status Python's reader alone gives.

Later the same day, at the operator's request, claims were sized to their tests (**Claim scope**
below). All of it is committed on `skill-environments` as `73496d6` and pushed; `51b3cd2` then gave
each verification two hours (`--timeout 7200`). **Run `d3892f6c` used all of it** (below): five
claims, four at A and one at B, every counted trial passing. This replaces the earlier "none of
this has been used in a verifier run, and nothing is committed yet".

### What has been done

This session, 2026-09-29, after the work of the 2026-09-28 entry:

**1. The format history.** A replay of 945 saved replies from 17 report cards found five forms
that had misread right answers: a plural (`e13f50ee`), `Molar` (`fb64115f`), `**1**`
(`7efbdd8c`), an explanation below the answer (`0a243b7e`) and a code fence (`0aeca4c6`). Only
the two fenced replies were still misread by the old reader.

**2. Contracts.**
- `tool-contracts.md`, under `qualify_local_candidate`, owns the types and "Reading a reply".
  The types are `numeric` (with an optional `unit`), `exact`, `term`, `expression`, `list`, `set`
  and `choice`. It also owns the answer-format line and the controls.
- `local-contract.md` gains "Reading replies", which owns the AI reader. The same file points to
  it where grades, verdicts and subject input are described.
- `evidence-rubric.md`:
  - A's row allows an AI reading of which answer a reply gives;
  - "generated" points to the open types;
  - AI-involvement says a reading does not lower A.
- `artifact-contracts.md`, `local-evaluator-spec.md` and `LOCAL-INSTALL.md` are updated to match.

**3. Code.**
- The new `answers.py` holds the reader, the types, the controls and the answer-format lines. The
  fence parser moved from `environment.py` to `common.py`, so both use it.
- `local_candidates.py` qualifies each case by its type; method version `-6` → `-7`.
- `local_science.py`:
  - counts every open type as generated;
  - traces a term to its quote by its words;
  - policy `evidence-strength-v6` → `v7`;
  - `decide` records `reading_summary`, with the status and accuracy Python's reader alone gives.
- `documentary.py`:
  - adds the reader session, and reads claim-only misses except `UNDETERMINED` and
    `none of these`;
  - critique rubric v8 → v9, adding `answer_types` and wording A as the rubric's row now does.
- `local.py`: the tool schema, the answer-format line, readings after each claim's trials,
  reading receipts, and a report with a "Read by" column and an AI-reader paragraph per claim.

**4. Verification.**
- Suite: 385 → 419 tests, 417 passing and 2 skipped, none failing (425 after claim scope below).
- `tests/recorded/subject-replies.json` keeps all 945 replies, labelled right, wrong or
  paraphrase; `test_answers.py` replays them:
  - every right answer passes, including the 19 trials misread when they ran;
  - the 10 wrong trials still fail, and the 3 paraphrases are left to the AI reader.
- 32 one-line mutations were each caught, and the baseline and restored trees passed:
  - 30 of the reader, the type rules, the AI reader, the Python-only status and the disclosure;
  - 2 of the follow-ups below.
- Follow-ups the new tests found or prompted:
  - a label's emphasis closing after the answer (`**Answer: 42**`) is now removed;
  - an option whose text reads as another option's number (`3` at position 1) is refused;
  - `term` refuses a number with the right message.
- **Live recordings**, about $0.23 on the operator's go-ahead, through the code that reads them:
  - `d416f79d`'s critique packet under rubric v9 settled at B with all three cases counted, as
    under v8.
  - The AI reader called `MolOps::adjustQueryProperties` `matches` for key
    `adjustQueryProperties`, "a formatting difference". It did so although the question asked for
    no namespace prefix.
  - It called a paraphrase of a sentence the question wanted verbatim `differs`.
  - All three first replies met their schemas.
- The verification bootstrap is 199,919 of its 200,000 bytes after claim scope, 81 to spare. Each
  document pinned for the local planner fits the 40 KiB section reply, now tested.
- Not verified then: any of this in a verifier run. Run `d3892f6c` below has since used it.

### Decisions taken 2026-09-29

- **Build the full typed-answer system and the AI reader together, on this branch** (operator),
  to be tested with skill environments in one run.
- **An AI reading counts, and the grade stays** (operator). The other options were capping the
  claim at B, or lowering it to C. A reading establishes what a reply says, never what the right
  answer is, so the rubric's A row now allows it. It is disclosed on every trial and claim.
- Proposed here and built:
  - the reader reads only counted trials Python did not pass;
  - Python refuses a reading whose copied answer is not in the reply, that another model gave,
    or that its own reader settles the other way;
  - no reading is ever retried;
  - Python, not the planner, writes the answer-format line;
  - the critique learns the answer types but not the reader.

### Claim scope

The operator asked why extracted claims are so narrow, and why they vary so much between runs.
A survey of the 17 report cards answered both:
- **Narrow claims cap grades.** Since per-case verdicts began (`28d19f8a`), 24 of 41 graded claims
  settled below their source's grade only because of their case count, most often one counting
  case short of A.
- **They also produce padding.** Critiques rejected 17 cases as `duplicate`, the same fact asked
  from the other direction. The critique of one `0a243b7e` claim wrote that it was "narrow enough
  (two documented constants plus one corollary) that five genuinely independent counting cases may
  not be constructible".
- **The variety is in the cutting, not the facts.** The 13 sar-analysis runs drew their claims from
  the same few passages: the FindMCS settings at `SKILL.md:37` in all 13, pIC50 in 12, dummy atoms
  in 12, RGroupDecompose in 10. That one passage became one, two or three claims, and runs had
  three to six claims. No claim ever tested the skill's workflow advice; `0aeca4c6`'s five were
  narrow scikit-survival facts too.
- **Cause.** The local planner's only guidance is the tool description "commit atomic claims".
  Nothing says how broad a claim is, how many to write, or what to cover.

Proposed changes, of which 1 to 3 are built:
1. Replace "atomic" with a scope rule, owned by `local-contract.md`. A claim is one behaviour the
   skill tells its user to rely on: a procedure step, a documented rule, or one function's
   behaviour. It includes every fact the skill states about that behaviour, and is broad enough
   for about six independent questions (A's five plus a spare). A behaviour that cannot support
   that merges with a neighbouring one; unrelated behaviours never merge.
2. A fixed procedure:
   - walk the skill's sections in order and take one claim per section that makes a testable
     promise;
   - prefer what the skill tells its user to do over library trivia;
   - write at most five claims, because broader claims mean more trials, and runs are near the
     90-minute limit.
3. Report lines: "limited by the claim's size, not its source" where only the case count held a
   grade down (open question 4 of the 2026-09-28 entry), and the skill's sections that received
   no claim.
4. Optional: start a re-run of an unchanged skill from the previous run's claims, keeping or
   replacing each with a reason. Runs become comparable, but earlier mistakes carry over.

**Decided** (operator): first "not before the next run"; then, superseding that, build items 1
to 3 before it and save item 4 for later.

Built:
- **Contract.** `local-contract.md` gains "Claims", which owns the scope rule, the
  section-by-section procedure and the limit of five. A section is the text under one heading
  of `SKILL.md`, and a reference file belongs to the first section that names it.
  `tool-contracts.md` lists a manifest over the limit as retryable, and `artifact-contracts.md`
  lists the new report fields.
- **The planner's tools.**
  - The shared `commit_claim_manifest` description still says "atomic" for the older profiles.
    The local planner's copy states the local rule instead: `local_definitions` in `tools.py`,
    used for both the served tools and the pinned block.
  - Step 1 of the planner prompt points to "Claims".
  - `MAX_CLAIMS = 5` is the local `max_claims` limit, with its own refusal message.
- **Coverage.** `claims.sections` reads `SKILL.md`'s sections, skipping frontmatter, a `#` inside
  a code fence, and headings with no text of their own. `claims.section_coverage` maps each
  claim to the section it covers.
- **Report.**
  - A "Skill sections" line near the top lists the sections no claim covers, and each claim has
    a "Skill section" line. The JSON gains `coverage` and each row gains `sections`.
  - `local_science.size_limit` gives a claim held below its source's grade only by its case
    count a "Limited by its number of independent cases, not its source" line, and its row a
    `size_limited` record.
  - `reference_grade` now holds the half of `evidence_ceiling` that the report reads back.
- **Replayed on real claims,** the coverage shows the problem:
  - `d416f79d`'s four claims covered two sections, two claims each;
  - three of `3dc02567`'s six came from the one MCS section;
  - three of `0aeca4c6`'s five came from "Model choice".
- **Verification.** Suite 419 → 425 tests. Ten one-line mutations were each caught, after one test
  was tightened: the first pass missed frontmatter handling, because the section test gave the
  frontmatter an intro line. It now also checks frontmatter directly before a heading.

**Across all 15 sar-analysis runs**, the claims covered 2 to 4 sections each, and 14 runs put a
second claim on a section already covered. Workflow was tested in 3 runs, Decision Framework and
Best Practices in 1 each, and Substructure Alignment and Activity Heatmap never. Two causes:
- **Splitting one passage.** The MCS section is one paragraph (`SKILL.md:37`), and 7 of the 17
  manifests split it into two or three claims (definition, threshold, ring options). Those split
  claims are the ones capped by their case count.
- **Chasing the easy oracles.** MCS parameters, pIC50 and dummy atoms have crisp API
  documentation; the workflow advice does not.

**Drafted, decide after the run: one claim per paragraph.** Python would refuse, as retryable, a
local manifest in which two claims quote the same paragraph, telling the planner to merge them.
Replayed over the 17 saved manifests, it refuses exactly the 7 that split the MCS paragraph and
nothing else. Claims on separate "Common Pitfalls" items, and on different scikit-survival
reference files, still pass. It enforces the "one behaviour" rule where planners broke it.
Python cannot tell which sections are testable, so it cannot force coverage of the hard ones.
The operator chose to run first on the instructions and the coverage line, and add this only if
the run still splits a passage.

### Run `d3892f6c`

Scikit-survival, 2026-09-29, on `51b3cd2`, after a Claude restart, from a session whose
`serve-local` started after both commits, with `--timeout 7200`:
- **Result.** Five claims, four at A and one at B, all `pass`. All 81 counted trials passed; none
  was invalid, missing or refused.
- **Time.** 3,641 s. Setup, including the environment build, took 34 s, and each claim 7 to 16
  minutes.
- **Cost.** About $24.69 at API rates: the planner $13.06 over 45 turns, 84 subjects $7.22, 7
  critiques $3.27, 64 claim-only sessions $0.97 and 17 readings $0.17. The 5-hour window went from
  3% to 52%.
- **Report.** `.verifier/runs/d3892f6c-4597-440b-a3fd-e008dbe2fc8e/report-card.md`, outside Git.

The checks this entry set for the run, answered:
- **The new code ran.** `local_method_ref` equals the tree's digest, `95f2ea51…`. All five critiques
  carry rubric v9, the audits carry policy `evidence-strength-v7`, and all nine trial readings carry
  `reader_ref` `738e3dbe…`.
- **Answer types.**
  - 1 of the 28 final cases is `choice` (3.6%, against 52–71% at versions 3 to 6). The rest are 16
    `term`, 4 `expression`, 3 `exact`, 3 `numeric` and 1 `set`; one replaced design had a `list`.
  - Every claim had at least two generated counting cases, so none was capped for want of them (13
    grades in 17 runs before).
  - One qualification was refused, by the new `exact` rule: a dtype keyed as `exact` although its
    case carries no meaning. The planner re-keyed it.
- **The AI reader** read 17 answers. It called all of them `matches`, and Python refused none.
  - Nine were counted trials, each a right answer that Python's reader failed for extra words on the
    answer line: "floating-point" for `float` (3), "Higher-is-riskier risk scores" and "Risk scores
    (…)" for `risk scores` (3), and "Estimated survival probabilities" and the like for `survival
    probabilities` (3). By Python's reader alone C1 would be `fail` at 15 of 18, and C2 at 12 of 18.
    Each copied answer is the reply's leading phrase, and each reason calls it the expected answer
    in other words, for example "'floating-point' is an equivalent wording of the expected answer
    'float'". The report quotes all nine.
  - Eight were claim-only answers. Six were the same kind, such as "boolean (bool)" for `boolean`.
    The other two read "the event time points" as matching `unique times`: a paraphrase, not
    presentation, and it hid the miss that claim-only answers exist to catch. The critique rejected
    that case as `beyond_scope` anyway, because its key is finer than the claim's wording, and the
    planner replaced it. See open question 1.
- **Claim scope, against the survey:**
  - five claims from five of the skill's 14 sections, one each; in `0aeca4c6` three of five came
    from "Model choice";
  - one claim settled below its source only for its case count: C4, at B with 4 of 5 counting cases
    (24 of 41 before). The report's "Limited by its number of independent cases" line names it;
  - one `duplicate` in seven critique sessions, replaced before any trial (17 in 17 runs before),
    with two `leaked` and one `beyond_scope`;
  - no claim summarises the skill, but four are broader than their cases. The critiques note that no
    case tests `concordance_index_ipcw` or `integrated_brier_score` (C2), the two competing-risk
    prohibitions (C3), C4's central GridSearchCV instruction, or seven of C5's nine estimator
    families. C2, C3 and C5 still settled at A (open question 5);
  - no two claims quote the same paragraph, so, as the operator decided, the drafted paragraph rule
    is not added;
  - the skill's workflow advice, "Non-negotiable workflow" and "Leakage-safe pipeline", got no
    claim, nor did Scope, installation, the CLIs, security triage, reference files, dated sources
    or citing.
- **C4 stayed at B by the planner's choice.** Its critique asked for four revisions, among them a
  case for the claim's central instruction. The planner re-proposed B on the same design instead.
- **Skill environment.**
  - Built on `python:3.12-slim` in 34 s, with lock `9679b819…`, the same as the live check.
  - The planner's 1,104-byte pinned block listed the 16 packages. No `sci-verifier-env` image,
    container or volume remained afterwards.
  - **No subject ran scikit-survival or the skill's scripts.** 30 of 84 trials used `run_command`,
    and all 79 commands read the skill's own reference files with `grep`, `sed`, `cat`, `find` or
    `ls`. So there was no docstring lookup to trace.
  - No planner designed an executed case or a calculation, and scoring used the operator's image.
- **Sessions and log.**
  - All 174 sessions ended `success`, each with its result event.
  - Every critique, claim-only and reader session returned a `structured_output`. Claude Code
    refused the first reply of 6 of 7 critiques and 4 of 64 claim-only sessions, each for an extra
    property such as `input`, `reason_for_call`, `_dummy` or `tool_use_id`, and every retry passed.
  - The two revised designs reused the claim-only answers of their unchanged cases, under the
    current IDs: 64 sessions for 32 distinct cases.
  - No refusal, `process_unparsed_output`, `claude_incomplete`, `*_response_invalid`, model change
    or timeout. No assessor ran.
  - The log kept up: at most 0.09 s between a session's result and its end, late in the run too.

### Open questions for the operator

1. **How lenient the AI reader should be.** It may judge `7.6e-9 M` to match 7.6 nM, a scientific
   equivalence rather than presentation, and in a recording it ignored a question's "without the
   namespace prefix". In `d3892f6c` every trial reading was presentation, but a claim-only reading
   called "the event time points" a match for `unique times`, and so hid a key finer than its
   claim. Claim-only misses could be read only for presentation, or not read at all, or the
   critique could see Python's reading beside the AI's.
2. **Uncounted trials are not read**, to save run time. Their report rows keep Python's verdict.
3. **List and set items are typed by their own form**, so a capitalised item such as `Core` is
   compared exactly.
4. The 2026-09-28 entry's open questions stand.
5. **Broad claims with partial cases.** Four of five claims settled with cases that test part of
   what they state, three of them at A. Should A need counting cases that reach each fact a claim
   states, or should a claim be cut down to what its cases test?
6. **The environment went unused.** Subjects answered documentation questions from the skill's own
   files, so the packages installed for them made no difference. Whether planners should write
   cases that need the library turns on open question 2 of the 2026-09-28 entry, a library's output
   as a key.

### Urgent next steps, if any

None. `skill-environments` is committed and pushed; merging it into `main` is the operator's call.

### Suggested next move

Settle open questions 1, 5 and 6, then run sar-analysis on this branch. The claim-scope survey's
baseline is 15 sar-analysis runs, so that run shows whether the instructions alone stop planners
splitting the MCS paragraph (`SKILL.md:37`) and returning to the same few passages. It also gives
typed answers and the AI reader a second skill.

### Recommended next action

This entry's earlier next action, to commit and run scikit-survival, is done; its checks are
answered under "Run `d3892f6c`". Next, with the operator's go-ahead:
1. Answer open questions 1, 5 and 6, or leave them open.
2. Follow "Before the next run" in the 2026-09-28 entry. Move, do not delete, into the session
   scratchpad:
   - `.verifier/runs/d3892f6c-4597-440b-a3fd-e008dbe2fc8e`
   - `.verifier/attempts/90e15c3d-e24d-4ee9-86e4-f5ae97d7deee`
   - `.verifier/subject-runs/d3892f6c-4597-440b-a3fd-e008dbe2fc8e`
   - the nine candidates it wrote at `local-reference-comparison-7`, dated 2026-09-29

   Keep the glycoengineering run, its attempt, subject-runs and five candidates, and
   `.verifier/store/`. `0aeca4c6`'s files are already in this session's scratchpad.
3. Start a new session and run sar-analysis.

Record, against the survey and this run: the claims and sections covered, claims held back only by
their case count, `duplicate` verdicts, any two claims on one paragraph, every AI reading, and what
subjects did with `run_command`. It is finished when each has a recorded answer.

## Claude: 2026-09-30 (runs fbd49132 and 26312681; planner told to test each fact a claim states; critique given Python's search record)

### Current stage and status

Version 0.7.0, local workflow, on `skill-environments`. On 2026-09-29 the operator ran a new skill,
`tooluniverse-dose-response`, as run `fbd49132`: one claim at A and three at B, every counted trial
passing, and every claim leaving facts it states untested (below). The operator judged the planner
lazy and asked for the planner's and the reviewer's instructions to be fixed. That is built (`fe47267`):
- **Planner.** Test a claim fact by fact, searching for each fact's source; keep a quote whole;
  revise, answering every required revision, before accepting a lowered grade.
- **Reviewer.** Critique rubric v10 lists the claim's facts against the counting cases, and turns a
  gap it can see a way to close into a required revision.

**Run `26312681`** then used it on the same skill (section 5): two claims at A and two at B. The
revise-before-accepting rule worked once, on C2, which went from B to A. The search rule did not:
C3 and C4 got no web search, were designed at B's minimum of four cases, and their critiques took the
planner's description of searches made for other claims as searches for theirs. The critiques also
read the planner's notes cut short. On the operator's go-ahead both are now fixed (section 6): the
critique reads the notes whole and judges searches by **Python's search record**, read from the
planner's own stream, under rubric v11. That fix is replayed live (below) and **not yet seen in a
run**. It cannot reach a plan that settles at its own proposal, as C3 and C4 did (open question 4).

### What has been done

This session, 2026-09-30:

**1. Run `fbd49132`**, tooluniverse-dose-response, 2026-09-29, on `4308111`, in a session started
after a Claude restart, with `--timeout 7200`:
- **Result.** Four claims: C1 (the 4PL equation) at A; C2 (data preparation), C3 (reading the four
  parameters) and C4 (quality gotchas) at B; all `pass`. 51 of 51 counted trials passed, and the 9
  uncounted ones too; none was invalid, missing or refused, and every case was unanimous.
- **Time and cost.** 3,061 s. About $19.79 at API rates: the planner $13.87 over 51 turns, 60
  subjects $2.60, 5 critiques $2.48 and 46 claim-only sessions $0.84; no readings. The 5-hour window
  went from 0% to 39%.
- **The new code ran.** `local_method_ref` equals the tree's digest, `95f2ea51…`. The critiques
  carry rubric v9 and the audits policy `evidence-strength-v7`.
- **Calculated answers, first seen live.** C1's keys came from a program implementing GraphPad's
  4PL formula, anchored on three Wikipedia Hill-equation statements; C2's from a percent-of-control
  program that reproduced four percentages printed in a CCK-8 protocol's table.
- **Against the claim-scope survey:**
  - four claims from four of the skill's eight sections, one each; none for the title section,
    "Step 2 — Fit / get the potency", "Honest limitations" or "Related skills";
  - three claims held back only by their case count, C2 and C3 at 4 of 5 counting cases and C4 at 3,
    each with `size_limited` showing that its source supports A;
  - three `duplicate` verdicts, two in C2 and one in C3, in designs that executed;
  - no two claims on one paragraph, and no AI reading;
  - `run_command` in 20 trials, each one line of `python3 -c` evaluating the formula, 18 in C1 and 2
    in C2. No subject ran the skill's script, which imports scipy: the skill declares no packages,
    so setup built no environment (`not_needed`) and the operator's image has no scipy.
- **Report.** `.verifier/runs/fbd49132-6165-44d5-93de-33025f8a5577/report-card.md`, outside Git.

**2. What went wrong: the planner took the cheapest legal path.**
- **Facts untested in every claim.** No case tested C1's statement about the helper's `hill_4pl`;
  C2's cases tested 3 of its 6 preparation rules; C3's left every threshold, the fold-shift rule and
  the Emin reading untested; C4's three cases reached 2 of its 5 gotchas. The coverage notes and
  critiques said so, but each claim's row gives one grade and `pass` for the whole statement.
- **No search for C4's missing gotchas.** The planner fetched two Wikipedia pages by URL, made no
  WebSearch for that claim, and designed exactly the three cases B needs, with no spare.
- **Accepting instead of revising.** C2's and C3's critiques settled B below a proposed A, with 4
  negotiation rounds and 1 replacement round left, and required cases for named untested rules; for
  C2's linear-vs-log10 rule the GraphPad page was already fetched. The planner accepted B both times,
  "rather than spend the remaining time on further revisions". Run `d3892f6c`'s C4 did the same.
- **Revisions answered in part.** C4's first critique required a case for the incomplete-curve
  remedy; the revised design met its other three requests and skipped that one.
- **A cut quote.** The first manifest was refused over a doubled space in C4's quote. The planner cut
  the quote to two of five gotchas and kept the statement of all five.
- **Where the rules allowed it.** The planner prompt offered accepting as one of "two moves";
  nothing asked cases to reach a claim's facts or asked for a search per fact; Python checks that a
  quote occurs, never what the statement adds; and a plan whose critique agrees with its proposal is
  fixed at once, so a design built at a low ceiling never returns to the planner.

**3. Changes**, contracts first:
- `local-contract.md`, "Claims", which owns both: **Quoted whole** (a quote carries every fact its
  statement states; correct a refused quote, and a shorter quote needs a shorter statement) and
  **Tested fact by fact** (a case for each fact a source can key before a second case on any; a
  search for each fact before leaving it untested; the spare case; within the subject-call budget,
  the facts the skill's user relies on most).
- `evidence-rubric.md`, step 4 of "Negotiating the grade": **Revise before accepting.** A revision
  answers every revision the critique requires; a lowered grade is accepted only when no search finds
  a source for what the critique asks, and saving run time is no reason.
- `tool-contracts.md`, `select_local_candidate`: `coverage` goes through the claim's facts, naming
  the cases for each and, for an untested fact, what was searched for and found.
- `SKILL.md` and the negotiation paragraph of `local-contract.md` restated step 4's old choice;
  both now point to it, and the operator's `LOCAL-CONFIG.md` describes the new rule.
- Code:
  - the planner prompt's steps 2 to 4 in `local_entry.py` follow these;
  - `local.py`'s `local_design_unchanged` message says to answer every required revision and to
    propose the settled grade only when step 4 allows it;
  - `claims.py`'s `quote_not_found` message, shared by every profile, says to correct the quote and
    to shorten the statement with it;
  - critique rubric v9 → v10 in `documentary.py`: criterion 2 is checked "as rubric.coverage says",
    and `coverage` asks for the facts with the counting case testing each. When the critique's grade
    is below the proposal, each untested fact a listed reference bears on, or no stated search
    covers, is a required revision; listing a gap does not by itself lower the grade.

**4. Verification.**
- Suite 425 → 426 tests, 424 passing and 2 skipped, none failing. New checks: the planner prompt
  and pinned blocks carry the new rules and no longer offer "two moves"; the quote refusal says how
  to repair; the v10 rubric carries its coverage rule.
- Sizes: the pinned `local-contract.md` is 38,580 of its 40,960 bytes, and the verification
  bootstrap 199,970 of its 200,000, so the next text added to `evidence-rubric.md` or `SKILL.md`
  must be offset there.
- **Live recording**, about $0.37: `d416f79d`'s pIC50 packet under v10 settled at B with all three
  cases counted, as under v8 and v9, and criterion 2's finding listed the claim's three facts with
  the cases testing each. Its first reply added a stray `evidence_ceiling` key, which Claude Code
  refused and the session resent.
- **Replays** of `fbd49132`'s four final critique packets on `claude-opus-5`, about $6.02: two
  samples of each under v10, and a second v9 sample of C2 to C4 beside the run's own critique.
  - **No grade moved.** C1 settled at A in all three samples, and C2, C3 and C4 at B in all four
    each. C2 counted four or five cases under either rubric; the other verdicts never changed.
  - **Criterion 2 now lists the facts.** Every v10 finding went through the statement fact by
    fact, eleven facts for C3, seven for C2 and six for C4, marking each untested one with whether
    a fetched reference bears on it and whether a search is stated. v9's findings summarised
    coverage in a sentence or two. Each list fit its 4,000-character field, and the report prints
    it under the claim.
  - **Required revisions** already named untested facts under v9 whenever the grade fell below
    the proposal (C2, C3). Under v10 they also tie each gap to the fetched page that bears on it,
    such as C2's linear-scale rule and the GraphPad page in hand; the number of gaps named did not
    rise.
  - **C4 is out of the reviewer's reach.** Its grade equals its proposal, so no revision is
    required, and v10 accepted the planner's mention of C2's blocked NCBI chapter as a search for
    C4's gotchas, though no search was made for that claim. Only the planner rules reach it.
  - One C3 sample offered narrowing the claim's scope as the alternative to a case, which the
    rubric's `verdict_consistency` rules out.
  - As in `d3892f6c`, Claude Code refused the first reply of 11 of the 12 sessions, v9 ones
    included, for a stray property such as `reason`, `cases` or `dd`; every retry passed.
- The 5-hour window was at 28% after this session's recordings and replays.
- A baseline in a scratchpad worktree failed on Windows' path limit (WinError 206), not on the
  code; in the repository the suite passed 425 of 425 before these changes.

Not verified then: any planner change in a run. Run `26312681` below has since used them.

**5. Run `26312681`**, tooluniverse-dose-response, 2026-09-30, on `fe47267`, from a session whose
`serve-local` started at 16:56 after that commit, with `--timeout 7200`. `fbd49132`'s files were moved
first, as this entry's recommended action said.
- **Result.** C1 (the 4PL equation) and C2 (data preparation) at A; C3 (reading the parameters) and
  C4 (quality gotchas) at B; all `pass`. 57 of 57 counted trials passed and the 3 uncounted ones too;
  none invalid, missing or refused; every case unanimous. Two C2 trials passed by the AI reader:
  "ic50" for an `exact` key "IC50". By Python's reader alone C2 is 13 of 15 and `fail`.
- **Time and cost.** 3,328 s of 7,200, and 60 of 128 subject calls. About $20.86 at API rates: the
  planner $15.12 over 51 turns, 60 subjects $2.68, 5 critiques $2.33, 42 claim-only sessions $0.69 and 2
  readings $0.03. The 5-hour window went from 29% to 70%.
- **The new code ran.** `local_method_ref` equals the tree's digest, `35bd30f0…`; the critiques carry
  rubric v10.
- **Against `fbd49132`, as this entry asked:**
  - facts tested, from each critique's v10 list: C1 6 of 7, C2 5 of 7, C3 4 of 12, C4 4 of 7, the
    three untested C4 facts being the incomplete-curve, too-few-points and biphasic gotchas;
  - WebSearch: 4 queries for C1 and 4 for C2 (one counted under C1, made before C2's first call), and
    **none for C3 or C4**. C3 fetched two Wikipedia pages by URL and C4 one, and the planner wrote
    "moving quickly" before C4;
  - critiques and their revisions: C2's first critique settled B below a proposed A, with 4 rounds and
    1 replacement round left, and required four revisions. **The next design answered all four** (a
    replacement for the leaked case, a direction case, and recorded searches for the point-count and
    unit rules) and settled at A. C3 and C4 were proposed at B, the ceiling of their four cases, and
    fixed at once, so neither critique could ask for more;
  - no accept below a proposal, so "revise before accepting" held where it applied;
  - no quote refusal: the manifest was accepted first time, and C4's quote now holds all five
    gotchas;
  - C1's first proposal was refused for `prior_review_in_packet` over the word "verdict" in its notes,
    spending no session;
  - grades 2 A + 2 B, against 1 A + 3 B; time 3,328 s against 3,061; subject calls 60 against 60;
  - sections covered: the same four of eight; no subject ran the skill's script, which needs scipy.
- **Two defects the run exposed:**
  - **The critique read the planner's notes cut short.** Every packet clipped the coverage note at
    2,000 characters and the design's limitations at 800, though the schemas allow 4,000 and 8,000. Two
    critiques said they could not confirm a search because the note was cut.
  - **The critique trusted described searches.** C3's critique wrote "every gap accompanied by a
    recorded search" and C4's credited GraphPad and NCBI searches; those were made for C1 and C2.
- Report: `.verifier/runs/26312681-3f7c-4573-8a4b-9da8b2c41c6b/report-card.md`, outside Git.

**6. Fixes after `26312681`**, on the operator's go-ahead, contracts first:
- `local-contract.md`: the critique receives the justification and the design's scope and
  limitations whole, and **Python's search record**: every WebSearch query the planner ran, marked
  with the claim it was working on (the one its last verifier tool call named), and every reference,
  resource or asset fetch with the claim it was for and its outcome. "Tested fact by fact" says the
  critique checks each described search against it. `tool-contracts.md`'s `coverage` points there.
- Code:
  - `local.py`: `NOTE_TEXT` (8,000) and `JUSTIFICATION_TEXT` (4,000) are shared by the tool schemas
    and the packet, so the packet carries what the schema accepted. `search_record` reads the
    attempt's event files, which are written once and never replaced, and `select` puts its result in
    `python_checked.search_record`; with no workflow log it says no search was recorded.
  - `documentary.py`: rubric v10 → v11, judging a search by `python_checked.search_record` ("the
    justification only describes searches, and one the record does not show was not made").
    `CRITIC_PACKET_LIMIT` goes from 160,000 bytes to 512 KiB: the largest packet the schemas allow is
    about 500 KB, so even the old limit never covered it.
- Verification:
  - Suite 426 → 429 tests, 427 passing and 2 skipped. New: the record read from a real
    `WorkflowLog` through `select`, attributing searches to this claim, another claim or none yet,
    reading a refused fetch, reporting results in no expected shape rather than failing the
    selection, and ignoring a subject's stream; the notes reaching the packet whole; and the
    schemas' largest packet, 500,611 bytes, under the limit.
  - Sizes: the pinned `local-contract.md` is 39,288 of its 40,960 bytes; the verification bootstrap
    is unchanged at 199,970.
  - **Packets rebuilt** from `26312681`'s journal, store and attempt log with today's code matched
    what was sent in everything but the rubric, the whole notes and the new record. The record showed
    8 searches when C3 and C4 were proposed, none of them while working on either.
  - **Live recording**, $0.43: `d416f79d`'s packet under v11, with its limitations whole and no log,
    settled at B with all three cases counted, as under v8 to v10. Its first reply added a stray
    `StructuredOutput` key, which Claude Code refused and the session resent.
  - **Replays** of `26312681`'s rebuilt packets under v11, $2.78: C1 once, C2's first round once, C3
    and C4 twice each, against the run's own v10 critiques. No grade moved: A, B, B, B. Every coverage
    finding used the record, for example C4's "search_record shows no query using any term for it
    (no 'plateau', 'incomplete curve', 'extrapolated IC50')". C2's first-round critique turned it into
    required revisions: "record an actual search for a source stating a minimum number of
    concentrations; the current search record contains none", and correct the justification's search
    narrative to match the record. C3's and C4's grades equal their proposals, so they required
    nothing (open question 4). Verdicts moved by one case in three samples: C2's first round judged a
    second case `leaked`, one C3 sample a case `duplicate` and one C4 sample a case `beyond_scope`;
    none changed a grade.
  - Not verified: any of this in a run.

### Decisions taken 2026-09-30

- **Fix the planner's and the reviewer's instructions** (operator), rather than cut claims down to
  their cases or add Python checks first.
- Proposed here and built: the two "Claims" rules, step 4, fact-by-fact `coverage`, the quote
  message and rubric v10.
- **Held back** at first: Python refusing an accept while replacement rounds remain, and returning a
  plan fixed at a low ceiling to the planner when its critique names a gap, until a run showed the
  text alone did not hold.
- **After run `26312681`** (operator: "yes, do both fixes and record the run"): the critique reads
  the planner's notes whole and judges searches by Python's search record, under rubric v11, with
  the packet limit raised to fit. This replaces the first half of what was held back with something
  narrower: the critique sees the searches, rather than Python refusing the planner anything.
- **Still held back:** refusing an early accept, which `26312681` never attempted, and returning a
  plan fixed at its own proposal to the planner (open question 4).

### Open questions for the operator

1. The 2026-09-29 entry's open questions stand. Question 5 is narrowed, not settled: the planner and
   reviewer now push coverage up, but whether A needs every fact a claim states tested stays open.
2. **The fitting step cannot run.** Step 2 needs the ToolUniverse `tu run` tools or the skill's
   scipy script, and the skill declares neither. A fenced `pip install numpy scipy` in the
   submission would let a claim on fitting execute; that is a change to the submission, not the
   verifier.
3. **More cases cost trials.** At three trials a case, the 128-call budget holds 42 cases a run.
   `fbd49132` and `26312681` each used 60 calls for 20 cases, and testing each fact could double that.
4. **A plan fixed at its own proposal never returns to the planner.** C3 and C4 of `26312681` were
   designed at B's minimum and settled at once. With the search record their critiques can name the
   facts no search sought, but only in the report. Returning such a plan to the planner, once and
   within its rounds, when its critique names such facts would make the search rule bite. It changes
   when `select_local_candidate` returns `local_grade_revision_required`.
5. **The planner hurries.** It wrote "moving quickly" before C4 of `26312681`, and accepted B in
   `fbd49132` "rather than spend the remaining time", though neither run used 56 of its 120 minutes.
   It is never told its deadline, and "Claims" still says a six-claim run used all but 8 seconds of
   its 90 minutes. Telling it the deadline and the time used might remove the pressure.
6. **C2's A rests on the AI reader.** Two of its 15 counted trials passed only because the reader
   judged "ic50" to match the `exact` key "IC50". This bears on the 2026-09-29 entry's question 1.

### Urgent next steps, if any

None. Committed and pushed on `skill-environments` with this entry.

### Suggested next move

Run tooluniverse-dose-response a third time once the 5-hour window allows, to see v11 and the whole
notes live against `26312681`; then decide open questions 4 and 5.

### Recommended next action

With the operator's go-ahead:
1. Move, do not delete, into the session scratchpad:
   - `.verifier/runs/26312681-3f7c-4573-8a4b-9da8b2c41c6b`
   - `.verifier/attempts/dc3fa47d-0ec7-4371-9c76-52dc9fa3576d`
   - `.verifier/subject-runs/26312681-3f7c-4573-8a4b-9da8b2c41c6b`
   - the ten candidates it wrote, dated 2026-09-30, 17:05 to 17:49

   Keep the glycoengineering run, its attempt, subject-runs and five candidates, and
   `.verifier/store/`. `fbd49132`'s files, 3,224 of them and its nine candidates, were moved on
   2026-09-30 to `cleaned-fbd49132` in scratchpad `c7991202…`; `d3892f6c`'s, 4,230 and nine, on
   2026-09-29 to `cleaned-d3892f6c` in scratchpad `8784dcda…`.
2. Start a new Code-tab session, so that `serve-local` starts after this commit, and check Docker and
   the 5-hour window as the 2026-09-28 entry says; `26312681` took 41 points of it.
3. Run tooluniverse-dose-response.

Record, against `26312681`: whether each critique's coverage finding uses the search record; for each
claim, the facts stated and tested and the WebSearch queries made while working on it; any claim
designed below A with no search, and whether its critique names the facts no search sought; each
critique's required revisions and whether the next design answered them; the grades; and run time
against 7,200 s and subject calls against 128. It is finished when each has a recorded answer.

## Claude: 2026-10-01 (runs 3303fd93 and 1d1c3b6e; a plan that settles at its own proposal comes back, and the planner is told its time)

### Current stage and status

Version 0.7.0, local workflow, on `skill-environments`. Run `3303fd93` used the 2026-09-30 fixes
(`66ff13e`): every critique judged the planner's searches by Python's record and named what was left
untested. The planner still built three claims to B's minimum, and their critiques agreed with B, so
those findings reached only the report. On the operator's go-ahead, two returns are now built
(`1ae07f8`, then section 3), both for a critique that agrees with a proposal below A:
- **the coverage-gap return**, once per claim, when the critique names coverage gaps;
- **the concern return**, while rounds remain, when the next critique, now shown every revision an
  earlier one required, judges one unanswered. That critique is the AI judge, as the operator asked;
  Python checks its `searched_no_source` verdicts against the search record.

After either return the grade is accepted only once Python's record shows a new search for the claim.
Both were replayed live (sections 2 and 3).

Run `1d1c3b6e` (section 4) used them, and **neither fired**: the planner proposed A in every round,
and both need a critique that agrees with a grade below A. It settled C1 at A and C2 and C3 at B.
C4 got a documentary D with no design, the planner saying its deadline was near with 62 of 120
minutes left. On the operator's go-ahead two fixes are built (section 5):
- every reply to the planner states the seconds it has left;
- the search record reads fetches from Python's own record of each call. This run's record had
  called five of ten successful fetches unreadable.

Neither fix is yet seen in a run, and neither return has yet fired in one.

### What has been done

This session, 2026-10-01:

**1. Run `3303fd93`**, tooluniverse-dose-response, on `66ff13e`, from a session whose `serve-local`
started at 13:41, after that commit, with `--timeout 7200`. `26312681`'s files were moved first.
- **Result.** C1 (the 4PL equation) at A; C2 (data preparation), C3 (reading the parameters) and C4
  (quality gotchas) at B; all `pass`. 48 of 48 counted trials passed and the 3 uncounted ones too;
  none invalid, missing or refused; every case unanimous.
- **The AI reader decided 8 trials.** In C2, "ic50" for the `exact` key "IC50" (2). In C4, "Cheng-Prusoff
  correction" for the term key "Cheng-Prusoff" (3), and "wider concentrations" for "concentration
  range" (3); the skill's own words are "recommend wider concentrations", so that key was the
  planner's paraphrase. By Python's reader alone C2 is 7 of 9 and C4 6 of 12, both `fail`.
- **Time and cost.** 2,791 s of 7,200, and 51 of 128 subject calls. About $18.04 at API rates: the
  planner $12.56 over 47 turns, 51 subjects $2.15, 5 critiques $2.67, 36 claim-only sessions $0.53 and
  10 readings $0.13. The 5-hour window went from 5% to 41%.
- **The new code ran.** `local_method_ref` equals the tree's digest, `578b3c4c…`; the critiques carry
  rubric v11 and a search record.
- **Against `26312681`, as the 2026-09-30 entry asked:**
  - every critique's coverage finding used the record. C3's, for example: "the record shows no search
    aimed at curve completeness for this claim", and of Emax and Emin, "the Prism variable-slope page
    (fetched twice, once for this claim) … bear[s] on Top/Emax, so a case here was available";
  - facts tested, from each critique's list: C1 3 of 6, C2 2 of 7, C3 3 of about 12, C4 2 of 5
    gotchas;
  - WebSearch: C1 7 queries, C2 2, **C3 and C4 none**; those two fetched two pages each by URL;
  - claims designed below A: C2 with 4 cases (6 in `26312681`), C3 with 3 (4), C4 with 3 then 4. C2
    and C3 were proposed at B, agreed and fixed at once, so their critiques could ask for nothing;
  - C4's first critique supported C below a proposed B and required five revisions. The next design
    replaced the leaked case and restored the case count, and **skipped the sparse-sampling and
    biphasic cases** it also required, with no search;
  - C2's first proposal was refused for `prior_review_in_packet` and spent no session;
  - grades 1 A + 3 B, against 2 A + 2 B; time 2,791 s against 3,328; subject calls 51 against 60.
- Report: `.verifier/runs/3303fd93-9621-42bc-8253-ea2115cc2709/report-card.md`, outside Git.

**2. The coverage-gap return**, on the operator's go-ahead ("yes, build it and record the run"),
contracts first:
- `tool-contracts.md`, `select_local_candidate`, owns it. Once per claim, a critique whose settled
  grade equals a proposal below A and that names `coverage_gaps` returns
  `local_grade_revision_required` with those gaps instead of fixing the plan. A revised design is
  critiqued as usual and never returned for gaps again. Accepting the returned design's grade is
  refused as `gaps_unsearched` until Python's search record shows a search or fetch for the claim
  since the return; with no workflow log there is nothing to check and acceptance stands. The
  critique's reply gains `coverage_gaps`.
- `workflow.md`'s local transition for `select_local_candidate` and `local-contract.md`'s negotiation
  paragraph point to it, in the same commit.
- Code:
  - `documentary.py`: rubric v11 → v12, asking for those gaps in `coverage_gaps` whatever the grade;
    the reply schema gains the field.
  - `local.py`: `select` makes the return and the acceptance check; the search record counts this
    claim's searches and fetches over the whole stream, not the listed 100; the gap return is a
    stored object, `gap_return_ref`, as every claim work field must be; the next critique is told the
    earlier gaps among the concerns it checks; the report prints each coverage gap and says when a
    claim came back.
  - `local_entry.py`: the planner prompt's step 4 names the return.
- Verification:
  - Suite 429 → 433 tests, 431 passing and 2 skipped. New, through `select` with a stand-in critique:
    an agreeing critique with gaps sends a B plan back once; accepting at once is refused as
    `gaps_unsearched` (renamed `return_unsearched` in section 3, which shares it); after one recorded
    search the same grade is accepted with no new session, and
    the report prints the gap and the return; a revised design with gaps left is fixed, with the
    earlier gaps among its critique's concerns; a plan at A, or with no gaps, is fixed at once; with
    no workflow log the returned grade is accepted.
  - Sizes: the pinned `local-contract.md` is 39,514 of 40,960 bytes and `tool-contracts.md` 26,494; the
    verification bootstrap is unchanged at 199,970 of 200,000.
  - **Live recording**, $0.40: `d416f79d`'s packet under v12 settled at B with all three cases counted
    and no coverage gaps, every fact of that claim being tested. Its first reply added a stray
    `evidence_limits` key, which Claude Code refused and the session resent.
  - **Replays** of `3303fd93`'s C2, C3 and C4 (second round) packets, rebuilt with today's code and
    matching what was sent apart from the rubric and the record's new counts, $1.68. C3 settled at B,
    its proposal, with 8 `coverage_gaps` (the Hill-slope and r² thresholds, Emax, Emin, the tested-range
    rule and fold-shift), and C4 at B with 5, among them the sparse-sampling and biphasic gotchas its
    first critique had required. **Under today's code both would come back to the planner.** C2's
    sample judged one more case `leaked`, so it would settle below its proposal and take the ordinary
    revision path, with 5 required revisions and 6 gaps.
  - Not verified: any of this in a run.

**3. The concern return**, on the operator's go-ahead ("let AI reader do the job"; then "build it and
do all tests you need"). A revision could answer some of the revisions its critique required and still
settle, as C4's did here and in `fbd49132`, because the next critique was never shown the required
revisions (only objections and rejected cases), and its prose answer to "is each concern answered"
changed nothing. Contracts first:
- `tool-contracts.md`, `select_local_candidate`: the critique receives earlier required revisions and
  coverage gaps among its concerns and gives each a verdict in `prior_verdicts`: `answered`,
  `searched_no_source`, `unanswered` or `no_longer_applies`. *The concern return*: while rounds
  remain, a critique agreeing with a proposal below A that judges a concern `unanswered` returns
  `local_grade_revision_required` with `unanswered_concerns`. A `searched_no_source` verdict stands only
  when Python's search record shows a search or fetch for the claim since the previous critique;
  otherwise Python counts the concern unanswered, as it overrules an AI reading its own reader settles
  the other way. Both returns share one refusal, `return_unsearched`.
- `workflow.md`'s local transition and `local-contract.md`'s packet and negotiation paragraphs follow.
- Code:
  - `documentary.py`: rubric v12 → v13, with `prior_verdicts` and criterion 5 pointing to it; the reply
    schema holds exactly one verdict per concern; each stored verdict carries the concern it judges.
  - `local.py`: earlier required revisions join the concerns; each critique stores Python's search
    count and `unanswered_concerns` after that check; `select` makes the return, kept as
    `concern_return_ref`, and the acceptance check covers both returns; the report prints each
    concern left unanswered and says when a claim came back for one.
  - `local_entry.py`: step 4 of the planner prompt names both returns.
- **The critique's deadline**, owned by `local-contract.md`, goes from five minutes to ten, and each
  concern's reason is held to one sentence. Live critiques took 90 to 210 seconds before v13, and both
  first v13 replays of a packet carrying eleven concerns ran past five minutes, which in a run would
  end the claim as an operational failure.
- Verification:
  - Suite 433 → 438 tests, 436 passing and 2 skipped. New, through `select`: an agreeing critique that
    finds a carried required revision `unanswered` sends a B plan back, and the second critique is
    shown "An earlier review required: …"; accepting at once is refused as `return_unsearched`, and
    after a recorded search accepted; the report prints the concern and the return; a
    `searched_no_source` verdict with no search since the previous critique is counted unanswered, and
    with one it stands; an answered request, or a plan at A, settles at once. The reply schema refuses
    a missing, extra or unknown verdict.
  - Sizes: the pinned `local-contract.md` is 39,772 of 40,960 bytes; the verification bootstrap is
    unchanged at 199,970 of 200,000.
  - **Live recording**, $0.31: `d416f79d`'s packet under v13 settled at B with all three cases counted,
    no gaps and no earlier concerns, in 76 s. Its first reply added a stray `StructuredOutput` key,
    which Claude Code refused and the session resent.
  - **Replays**, $3.55 for the five that completed (the two that timed out left no cost record):
    `3303fd93`'s C4 second round, rebuilt with today's
    code and now carrying the first round's five required revisions, in three samples (154 to 200 s).
    **Each judged the same three unanswered**, the sparse-sampling case, the biphasic case and
    broadening c2's synonyms, with the objection behind the last, and the two the planner made
    `answered`. Under today's code C4 would come back with four unanswered concerns as well as its gaps.
  - **Negative control**: `26312681`'s C2 second round, whose revision answered all four requests.
    Both first samples ran past five minutes; under the final rubric they took 291 and 218 s. Three
    requests were `answered` and the fourth, "record the search that failed" for the point count,
    `searched_no_source`, which Python's check overrules because that search came before the request.
    Neither sample would return the claim: one supported A, the other B below the proposed A.
  - Not verified: any of this in a run.

**4. Run `1d1c3b6e`**, tooluniverse-dose-response, on `f469ad6`, from a session whose `serve-local`
started at 18:45, after that commit, with `--timeout 7200`; `local_method_ref` is `dcfadc5e…`.
`3303fd93`'s files, 2,862 and six candidates, were moved first, to `cleaned-3303fd93` in scratchpad
`c7991202…`.
- **Result.** C1 (the 4PL model) at A; C2 (data preparation) and C3 (reading the parameters) at B,
  all `pass`; C4 (quality gotchas) at D, `inconclusive`, with no design. 51 of 51 counted trials
  passed, all by Python's reader; the AI reader decided none. Of 3 uncounted trials, 1 passed.
- **Rounds.**
  - C1: A → B (4 counting cases, one `leaked` and one `beyond_scope`), then A → A.
  - C2: A → B three times, a case `leaked` each round (`c2_x_values` twice), fixed at B by the
    round limit.
  - C3: A → B, with 5 coverage gaps and 5 required revisions. After one search the planner wrote
    "Time is tight" and accepted B. Two of those revisions pointed at pages it had already fetched.
- **No return fired.** Every proposal was A, so no critique agreed with a grade below A, and no
  acceptance was refused as `return_unsearched`.
- **The concern verdicts ran.** C1's second critique judged 16 earlier concerns, and C2's second and
  third 16 each. In C2's third, Python counted 5 `searched_no_source` verdicts unanswered, there
  being no search since the round before. Neither changed a grade: C1 settled at A, and C2 ran out
  of rounds.
- **C4.** At 57 minutes the planner wrote "With the attempt deadline near, I'll secure claim 4 via the
  documentary path", with 62 of its 120 minutes left. It fetched one page; its first assessment was
  refused for an inexact quote; the assessor found that page short of the claim. The documentary
  path was legal there (`workflow.md`, the local transitions: a lookup and one retrieved reference),
  as the operator accepted for `84e90683`. The planner was never told its deadline, and
  `local-contract.md` told it a six-claim run "used all but 8 seconds of its 90 minutes".
- **Search record.** WebSearch: C1 4 queries, C2 2, C3 1, C4 none. Fetches: 5, 3, 1 and 1. **Five
  of the ten fetches showed as "unreadable result"**: each reply was over 16,000 characters, the
  workflow log keeps that much of the planner's copy, and the record parsed that copy. The critiques
  of C1 (round 1), C2 (round 3) and C3 then asked the planner to reconcile its fetches or its
  provenance text with the record.
- **Facts tested**, from each final critique's list: C1 6 of 10, C2 5 of 8, C3 5 of about 10.
- **Time and cost.** 3,583 s of 7,200, and 54 of 128 subject calls. About $23.0 at API rates: the
  planner $15.14 over 50 turns, 54 subjects $2.33, 6 critiques $4.52 (165 to 261 s each), 50
  claim-only sessions $0.82, 3 readings $0.05, the assessor $0.12. The 5-hour window went from 3%
  to 49%.
- **Against `3303fd93`:**
  - grades 1 A + 2 B + 1 D, against 1 A + 3 B;
  - AI-reader trials 0, against 8;
  - every design proposed at A, against B for C2 and C3;
  - facts tested: C1 6 of 10 (3 of 6), C2 5 of 8 (2 of 7), C3 5 of about 10 (3 of about 12);
  - WebSearch for C3 1 query, against none; for C4 none in either.
- Report: `.verifier/runs/1d1c3b6e-7d26-4a9e-b6db-59af72c207ee/report-card.md`, outside Git.

**5. The planner's clock and the search record**, on the operator's go-ahead ("yes, build both fixes
and record the run"), contracts first:
- `local-contract.md`, "Acceptance", owns the clock. Every reply to the planner carries
  `attempt_seconds_remaining`, the whole seconds left before the planner is stopped. "At most five"
  no longer says "90 minutes". `tool-contracts.md`'s "Local profile tools" points to it.
- `local-contract.md`'s critique paragraph: the search record's fetches, and their outcomes, are
  Python's own record of each call.
- Code:
  - `local_entry.py`: `BoundRuntime` adds the field to every reply, refusals included. It is
    computed from the deadline the runner already gives the planner's tool server for the end-of-run
    re-run. The planner prompt says to judge time by it, never by a guess.
  - `local.py`: `search_record` reads each fetch from the `tool_started` and `tool_finished` events
    Python writes for the call, and WebSearch queries and their claim from the planner's stream as
    before. A call that never reached Python's tools fetched nothing. A page's size is no longer
    printed: Python's call record does not hold it, and it appeared only for pages over 40 KiB.
- Verification:
  - Suite 438 → 439 tests, 437 passing and 2 skipped.
    - New: every reply through `BoundRuntime`, a refusal included, carries the seconds left. The
      value is 0 past the deadline, and the field is absent with no deadline or an unreadable one.
      The prompt and the pinned contract name it.
    - The search-record test now records its fetches through `recorded_call`: a reply over 16,000
      characters, still `reference_fetched`; a refusal; a raised fault; a call that never reached
      Python; and malformed events.
  - **On this run's own log**, the new record reads all ten fetches as `reference_fetched`, where
    the old one read five as unreadable. The counts per claim are unchanged.
  - Sizes: the pinned `local-contract.md` is 40,281 of 40,960 bytes, and the verification bootstrap
    is unchanged at 199,970 of 200,000. The `tool-contracts.md` pointer, first put in its common
    protocol, which that bootstrap pins, took it past 200,000; it now sits in "Local profile tools".
  - The rubric did not change, so nothing was re-recorded.
  - Not verified: either fix in a run.

### Decisions taken 2026-10-01

- **Build the coverage-gap return** (operator), answering open question 4 of the 2026-09-30 entry.
- Proposed here and built: only below A, since A is the strongest grade and its critique judged
  the coverage enough; once per claim; acceptance afterwards needs a new search or fetch in Python's
  record; the gaps travel to the next critique; the report discloses the return.
- **Build the concern return with the next critique as the AI judge** (operator). Proposed here and
  built: the critique, not a separate reader, since it already reads the old concerns beside the new
  design; below A only; while rounds remain rather than once, since each round costs a critique and
  the round limit bounds it; Python checks `searched_no_source` against its record; one refusal reason
  for both returns. `gaps_unsearched` became `return_unsearched` before any run used it.
- **Tell the planner its time, and read fetches from Python's record** (operator), after run
  `1d1c3b6e`. Proposed here and built: the time goes in every reply, not the prompt alone, since a
  session sees no clock; there is no field when nothing bounds the attempt or the deadline cannot be
  read, so a bad value never fails a reply; the page size leaves the record.
- **Not built:** a check on accepting a lowered grade (open question 4).

### Open questions for the operator

1. The 2026-09-30 entry's questions 1 to 3, 5 and 6 stand; question 4 is answered above.
2. **The AI reader now decides grades.** C2 and C4 pass only through it, and "wider concentrations"
   for "concentration range" is a paraphrase, not a format difference (2026-09-29, question 1). In
   `1d1c3b6e` it decided no trial.
3. A revision answering only some required revisions is now answered by the concern return (section
   3). **Its search check is strict:** a request answered by recording a search made before it was
   raised still needs a new search before the grade is accepted, one search call at worst. The
   negative control met exactly this, harmlessly. Relaxing it to any search for the claim would let a
   planner cite searches made for other facts.
4. **A lowered grade can still be accepted at once.** The returns guard only a critique that agrees
   with a grade below A. A planner that proposes A and accepts the B it is given passes neither, as
   C3 of `1d1c3b6e` did with five required revisions unanswered. Requiring a new search would not
   have stopped it, since it made one. Whether the clock is enough is for the next run to show.

### Urgent next steps, if any

None. Committed and pushed on `skill-environments` with this entry.

### Suggested next move

Run tooluniverse-dose-response again, so the planner works with its clock, and see whether every
claim gets a design and whether a lowered grade is still accepted at once.

### Recommended next action

With the operator's go-ahead:
1. Move, do not delete, into the session scratchpad:
   - `.verifier/runs/1d1c3b6e-7d26-4a9e-b6db-59af72c207ee`
   - `.verifier/attempts/9b34b883-422f-4918-a717-10f4c36b8dcd`
   - `.verifier/subject-runs/1d1c3b6e-7d26-4a9e-b6db-59af72c207ee`
   - the eight candidates it wrote, dated 2026-10-01, 18:58 to 19:40

   Keep the glycoengineering run, its attempt, subject-runs and five candidates, and
   `.verifier/store/`. `3303fd93`'s files, 2,862 and six candidates, were moved on 2026-10-01 to
   `cleaned-3303fd93` in scratchpad `c7991202…`.
2. Start a new Code-tab session, so that `serve-local` starts after this commit (the run's
   `local_method_ref` is then `cb7ef8a4…`), and check Docker and the 5-hour window as the 2026-09-28
   entry says.
3. Run tooluniverse-dose-response.

Record, against `1d1c3b6e`:
- the `attempt_seconds_remaining` the planner saw when it finished each claim, accepted a lowered
  grade or took the documentary path, and whether every claim got a design;
- each coverage-gap return and concern return, with the concerns judged unanswered and any
  `searched_no_source` verdict Python overruled, and what the planner did after each;
- the fetch outcomes in the critiques' search record;
- the facts tested and WebSearch queries per claim, the grades and the trials the AI reader decided;
- run time against 7,200 s and subject calls against 128.

It is finished when each has a recorded answer.

## Claude: 2026-10-02 (run 90c60cbe; one false fail, and a bar for changes so that fixes do not overfit)

### Current stage and status

Version 0.7.0, local workflow, on `skill-environments`. Run `90c60cbe` used the 2026-10-01 fixes
(`ddc5f84`) and settled all four claims at A, a first for this skill. C1's status is `fail` on one
case, whose question, not its key, was at fault. The operator raised a concern that fixes drawn
from single runs overfit. The records support it, so no fix is made for that case, and a bar for
future changes is recorded below. The two returns built on 2026-10-01 have not fired in any run
since.

### What has been done

This session, 2026-10-02:

**1. Run `90c60cbe`**, tooluniverse-dose-response, on `ddc5f84`. Its session's `serve-local` started
at 23:01 on 2026-10-01, after that commit, with `--timeout 7200`. `1d1c3b6e`'s files had already
been moved, at 20:44 on 2026-10-01, to `cleaned-1d1c3b6e` in scratchpad `d9761800…`, so nothing was
moved. The Western-blot run `32e60bd6` was left in place, as the operator asked.
- **Result.** C1 (the 4PL model) at A, `fail`; C2 (data preparation), C3 (reading the parameters)
  and C4 (quality gotchas) at A, `pass`. 57 of 60 counted trials passed, and every case was
  unanimous. The AI reader decided one trial, "Cheng-Prusoff correction" for the term key
  "Cheng-Prusoff", in C4. By Python's reader alone C4 is 14 of 15, `fail`.
- **Rounds.** C1 and C2: A → A. C3 and C4: A → B, then searches and a revised design, then A → A.
  Two proposals were refused as `prior_review_in_packet`, and two fetches sent in parallel as
  `illegal_transition`. No return fired.
- **The clock worked.** Every reply carried `attempt_seconds_remaining`: 7,068 s at the first lookup,
  3,042 s at the last selection. The planner designed and ran every claim, made no remark about
  time, and ended with about 2,830 s left.
- **The search record worked.** Every critique's record showed each fetch's outcome:
  `reference_fetched`, or `refused: illegal_transition` for the parallel calls. No critique asked
  to reconcile the record.
- **Against `1d1c3b6e`'s list:** facts left untested per final critique 2, 2, 3 and 3; WebSearch
  queries 5, 3, 2 and 2 (C1's include 2 made for C2 before the planner named that claim); fetches
  4, 6, 6 and 4; earlier requests judged unanswered at the final round, both at A, 2 in C3 and 4
  in C4; grades 4 A against 1 A, 2 B and 1 D.
- **Time and cost.** 4,371 s of 7,200, and 78 of 128 subject calls. About $29.6 at API rates: the
  planner $20.70 over 66 turns, 78 subjects $3.38, 6 critiques $4.47 (101 to 297 s each), 58
  claim-only sessions $0.98, 6 readings $0.10. The 5-hour window went from 3% to 60%, the most for
  this skill.
- Report: `.verifier/runs/90c60cbe-4ffd-44f1-8e2c-c2122af3e5d6/report-card.md`, outside Git.

**2. Why C1 failed: one case, a false fail.** `dr1_agonist_measure` asked "Which half-maximal
concentration parameter does the fit report for that activation curve?". Its key was `EC50`, of
type `exact`.
- **The key is right.** SKILL.md says "'IC50' for inhibition, 'EC50' for activation".
- **The question is at fault.** SKILL.md also says the tool "Returns `ic50`, …" for any curve, and
  the `exact` format line asks for "the exact token, written as it appears in code or data". All
  three subjects answered `ic50`, each adding that the value is read as the EC50 for an agonist; two
  searched the skill's scripts for the token first. The claim-only sessions got the same question
  and format line, had no skill, and answered `EC50`.
- **The process could not see it.** The critique and the claim-only sessions see the claim, not the
  skill. The AI reader read the replies correctly as `differs`. Under the unanimity rule one case at
  0 of 3 fails the claim; without it C1 is 12 of 12. Its grade stands either way.
- **The other two misses were handled as designed.** In C3, `dr3_range` keyed an option that is
  GraphPad's sentence with its condition ("If the top plateau is not defined…") cut, so it reads as
  "curve fitting is useless". Subjects and claim-only sessions all chose "none of these", and
  Python's claim-only check dropped the case, which the critique had counted against its own
  rubric rule. In C4, `dr4_cheng` was the AI reader's trial above.

**3. The overfitting check**, after the operator's concern:
- Across the 10 runs whose records are kept (166 counted cases on sar-analysis, scikit-survival,
  glycoengineering, western-blot-quantification and five dose-response runs), only
  `dr1_agonist_measure` has claim-only sessions reaching a key that every subject missed.
- Since the `exact` format line was added in `73496d6`, 10 other `exact` cases, in the 5 of 7 runs
  that used the type, passed all 30 of their trials.
- In the three runs since the two returns were built, `1d1c3b6e`, `90c60cbe` and `32e60bd6`, every
  proposal was A except two acceptances of a lowered B, one in `1d1c3b6e` and one in `32e60bd6`.
  `32e60bd6` was run from another session and is not recorded here. An acceptance runs no
  critique, so neither return could fire. The acceptances are the 2026-10-01 entry's open
  question 4.
- So neither proposed fix was built: a planner rule against asking what a tool "reports", and a
  reworded `exact` format line.
- The scan is `divergence.py` in scratchpad `c7991202…`; it ran no model session.

### Decisions taken 2026-10-02

- **A bar for changes** (operator: "yes, record it in the plan"):
  - fix a bug or a missing fact at once, as the search record and the clock were fixed;
  - change a planner, critique or reader rule only for a failure seen on at least two skills, and
    check the change against kept runs of other skills before adopting it;
  - run the next verifications on skills other than tooluniverse-dose-response.
- **No fix for `dr1_agonist_measure`.** It is a recorded false fail. A rule waits until the same
  pattern, claim-only sessions reaching a key every subject misses, appears on a second skill.
- **The returns stay, and nothing like them is added.** They are judged after runs on other skills.
  If they still never fire, they are complexity the workflow does not need.

### Open questions for the operator

1. The 2026-10-01 entry's questions 2 to 4 stand. Question 4, a lowered grade accepted at once, came
   up again in `32e60bd6`.
2. Keep or remove the two returns, after the next runs on other skills.

### Urgent next steps, if any

None. Committed and pushed on `skill-environments` with this entry.

### Suggested next move

Verify a skill other than tooluniverse-dose-response on `ddc5f84`, to see whether the recent rules
hold away from the skill that produced them.

### Recommended next action

With the operator's go-ahead:
1. Choose a skill other than tooluniverse-dose-response.
2. Move, do not delete, into the session scratchpad:
   - `.verifier/runs/90c60cbe-4ffd-44f1-8e2c-c2122af3e5d6`
   - `.verifier/attempts/462b41d5-ad18-4937-bde6-5102d1bdaf48`
   - `.verifier/subject-runs/90c60cbe-4ffd-44f1-8e2c-c2122af3e5d6`
   - the ten candidates it wrote, dated 2026-10-02, 01:30 to 02:26

   Leave the Western-blot run `32e60bd6`, its attempt `350bcb4c…`, its subject-runs and its eight
   candidates (2026-10-01 23:52 to 2026-10-02 00:54) to the operator. Keep the glycoengineering run,
   its attempt, subject-runs and five candidates, and `.verifier/store/`.
3. Use a session whose `serve-local` started after `ddc5f84` (its runs' `local_method_ref` is
   `cb7ef8a4…`), and check Docker and the 5-hour window as the 2026-09-28 entry says. A run has
   taken up to 63 points of that window.
4. Run the chosen skill.

Record: any case where claim-only sessions reach a key that every subject misses, and why; whether
either return fires; how many lowered grades are accepted at once; the time left as the planner
ends each claim; grades, statuses and the trials the AI reader decided; run time against 7,200 s
and subject calls against 128. It is finished when each has a recorded answer.

## Claude: 2026-10-05 (an HTML page after every run; the final reviewer planned; whole-skill task tests built; question tests removed, 0.8.0; a recorded task critique)

### Current stage and status

Version 0.8.0, local workflow, bumped in section 6. `skill-environments` was merged into `main` and
deleted, and the work since is on the new branch `whole-skill-tests`, which is the operator's to merge. Every completed run
gets one web page, made from its records, for the operator and the lab, unless the user asks for
none (section 3); the agent that asked for the verification writes its plain-language summaries. A
final reviewer is planned, not built (section 2).

The whole-skill test design (section 4) is **built** (section 5). A skill is split into claims that
are groups of whole sections, nothing left out, and each claim is tested by tasks: the test AI gets
the whole skill, input files and a job, and writes `results.json`, which Python checks against values
it built into the files from a referenced model, or quoted from a reference. Python proves each task
fair first by running the planner's own reference solution. Question tests are removed, a wrong result
now outweighs an unreadable one, and the operator's image has scipy (section 6). Checked by the suite,
by the container steps run live, and by one live test session and one live task critique, which both
worked. **No live verifier run has used task tests.** Starting one needs the operator's go-ahead and a
new Code session.

### What has been done

This session, 2026-10-05:

**1. The HTML run report**, on the operator's request ("Now build the html … we will test the html
first").
- `scripts/report_html.py RUN` writes `.verifier/reports/<run>.html`. The page is one file with no
  scripts and no outside styles. Every recorded string is escaped, and only `http(s)` sources become
  links.
- It reads only the run's records:
  - the report card;
  - the run journal, for grading rounds and time per claim;
  - the workflow log, for session costs and Python's search record;
  - the store, for designs and sources.

  A part that is missing leaves its figure blank.
- The page follows the operator's outline:
  - the skill in plain words, with its sections and the claim that tested each, folded when there
    are more than ten;
  - a summary table, one row per claim: grade, status, answers right, agreement, tests and trials
    counted, AI-reader passes, grading rounds, searches and fetches, facts left untested, time and
    cost;
  - one chapter per claim:
    - a plain description and a summary;
    - a table with one row per test;
    - one fold holding each test's full question, answer format, key, source quote, reviewer
      verdict, claim-only answers and every try, plus the sources, grading rounds, untested facts
      and the planner's recorded limits;
  - cautions and limitations;
  - how to read the page.
- The plain-language text comes from a notes file, `.verifier/reports/<run>.notes.json`: the skill
  summary, claim descriptions and summaries, what each test asks, review notes and cautions. The page
  marks it "✎ written by Claude" and says it is not part of the scored record. I wrote run
  `90c60cbe`'s notes in this session. The final reviewer is to write into the same file.
- Checked on every kept run that has a report card: `90c60cbe` with notes, and without notes
  `32e60bd6`, `1d1c3b6e` (one documentary claim), `3303fd93`, `26312681`, `fbd49132`, `d3892f6c`,
  `0aeca4c6` and `d416f79d`. `32e60bd6`'s page was written outside its run, which was left untouched.
  Five kept runs have no report card: four kept only their event logs, and `4a8c380d` stopped at the
  usage limit with a partial report. For those the script says so.
- Read in Edge at 1,400 px, every column shows, and each fold opens to readable text.
- `LOCAL-INSTALL.md` tells the operator how to make the page.
- Verification: suite 439 → 444 tests, 442 passing and 2 skipped. The new tests check that:
  - a hostile reply is escaped and a `javascript:` source is never linked;
  - there is one chapter per claim and one row per test;
  - a choice key shows the option it names;
  - notes appear, marked;
  - the same records give the same page;
  - a run without a report card says it stopped early.
- Not done: stopped runs' partial reports are not rendered. That runs did not make the page themselves
  is superseded by section 3.

**2. The final reviewer, planned** (the operator: "leave the final reviewer into the dev plan").
- Decided by the operator, 2026-10-05:
  - it reviews every failed test plus a sample of passed ones;
  - a test it disputes is re-run, with the question, key or other part at fault fixed.
- Proposed here, for the build:
  - **Where and what it sees.** A fresh session after all claims ran and before the report. It sees
    the skill's own text and, for each test it reviews, the question, the answer-format line, the key
    and its source quote, the subjects' replies and the claim-only answers. The critique sees none of
    the skill; `90c60cbe`'s false fail came from the skill's own words ("Returns `ic50`") and our
    format line.
  - **It can only withdraw a verdict, never give one.** A disputed fail is `inconclusive` until the
    re-run settles it, and the first verdict stays in the record beside the review.
  - **Each finding names its fault from a short list** (the question, the key, the answer format or
    reader, the skill) with a reason.
  - **Fixes.** A fault in a question or key is fixed through the normal design path (qualification,
    critique, claim-only answers), and the claim is re-run once. A fault in our own process (a format
    line, the reader) is recorded for the developers, and the test stays `inconclusive`.
  - **It meets the 2026-10-02 bar.** False fails have come up on sar-analysis (`b43780be`,
    `3b3f3c94`) and on dose-response (`90c60cbe`).
  - **Test it first.** Run it over the kept runs before it joins the workflow: it should flag
    `dr1_agonist_measure` as a question fault and leave the true passes alone.

**3. The page after every run, summarized by the calling agent.** The operator: "I need this html
generate automatically after each run unless the user explicitly says not to in the prompt. Then the
default agent should be able to touch it and summarize the claim. Current claim description is too
long and very unreadable."
- Contracts first:
  - `local-contract.md`, which owns the public interface, now reads `verify_skill(source_path,
    html_report)`. A completed run also gets the page and a notes file for the calling agent's
    summaries, unless `html_report` is false or `--no-html` is given.
  - `LOCAL-INSTALL.md` tells the operator what is written and how to skip it.
- Code:
  - The renderer moved into the package as `report_html.py`; `scripts/report_html.py` only calls it.
  - After a completed run, `verify()` publishes, unless the caller passed `html_report` false. The
    page goes to `.verifier/reports/<run>.html`. Beside it goes an unfilled notes file: a short guide,
    then, for each claim and test, what the agent needs (the claim as written, each question, key and
    answers, the result, the facts left untested) next to empty plain-language fields. Notes already
    written are kept.
  - The tool's reply gains `html_report`: the page, the notes file, the command that redraws the
    page, and the next step. Its key sorts before the long report, so an agent sees it in the first
    lines.
  - `verify_skill` takes the optional `html_report`, and the server's instructions tell the agent to
    follow the next step unless the user asked for no page. The CLI's `verify` takes `--no-html`.
  - The schema check learned booleans.
  - A page that cannot be drawn is reported beside the result and never changes it.
- Without notes, a claim shows "No plain summary yet" and the planner's one-sentence scope, and its
  full statement (90 to 190 words in `90c60cbe`) is folded away. A test shows the sentence that asks,
  not its whole question.
- Shown working on `32e60bd6`. Publishing wrote its page and notes outside its run, which was left
  untouched. Acting as the calling agent, I filled the notes for 4 claims and 24 tests and redrew the
  page. `90c60cbe`'s page was redrawn too.
- Verification: suite 444 → 448 tests, 446 passing and 2 skipped. New tests:
  - without notes the long claim folds away and a test shows its question;
  - publishing writes the page and an unfilled notes file, and keeps notes already written;
  - `verify()` publishes after a completed run, writes nothing when told not to, and reports a page
    it cannot draw without changing the result;
  - the public tool takes an optional boolean `html_report` and refuses anything else.
- Sizes: the pinned `local-contract.md` is 40,484 of 40,960 bytes; the verification bootstrap is
  unchanged at 199,970 of 200,000.
- `src/` changed, so a run needs a session whose `serve-local` started after this commit.
- Not verified: a live run that publishes the page, and an agent following the next step unprompted.

**4. A new test design: test the whole skill by running it.** Discussed with the operator; built the
same day (section 5), where this outline's open choices are settled.
- Why:
  - **Claims cover little of a skill.** Measured by the words of `SKILL.md` in sections that had a
    claim:
    - western-blot-quantification `32e60bd6`: 13% (333 of 2,558 words; 4 of 30 sections);
    - scikit-survival `d3892f6c`: 31% (565 of 1,810; 5 of 14);
    - tooluniverse-dose-response `90c60cbe`: 73% (567 of 772; 4 of 8).

    The Western-blot skill's untested parts include Common Pitfalls (415 words), the Decision
    Framework (342), Best Practices (179) and the workflow steps for image processing, measurement,
    fold change and visualization. A claim's six or so tests and eighteen tries went as readily to a
    one-paragraph rule or a single formula as to a long section.
  - **Tests rarely run the skill.** In `90c60cbe` 10 of 78 tries used the sandbox, mostly for
    arithmetic, and none ran the skill's fitting script (no scipy). Most tests ask whether the skill
    states a fact correctly.
  - The operator: "our ultimate goal is to test if the 'whole' skill works, we are not try to debug
    the skill." The narrow-claim pattern shows on two skills, so this meets the 2026-10-02 bar.
- Decided by the operator:
  - the planner groups the whole skill into claims by topic, and Python checks that nothing is left
    out;
  - the number of claims grows with the skill's length, the planner choosing it, and the time limit
    rises to 3 hours;
  - a claim is tested as a whole, not section by section;
  - a test gives the test AI a task and checks the output: "giving an input to step 1, and check if
    the output by step 5 works".
- Proposed here, for the build:
  - **Claims.** A claim is a group of whole sections. A section with nothing to test (Metadata,
    References, an empty parent heading) is set aside with a reason, and the page lists it. Python
    refuses a manifest that leaves any section neither in a claim nor set aside.
  - **Tests are tasks:** input files, a job in plain words and a fixed output format, such as
    `results.json`. The test AI gets the whole skill, not the claim's text; the claim only decides
    which task is set. Each test names the sections it uses, and Python refuses a design that leaves
    a section of the claim unused.
  - **Expected answers come from outside the skill.** Where a model exists, Python builds the answer
    into generated data, from parameters the planner chooses, by running the planner's generator
    program in the sandbox and storing the files and the built-in values. The model must come from a
    fetched reference, never from the skill, as calculated answers already require. References stay
    the source for:
    - the model behind every generator;
    - the right response to a planted problem;
    - real datasets with published results;
    - facts and guidance with nothing to compute.
  - **Advice is tested by doing.** A planted problem, such as a curve that never levels off or
    U-shaped data, must be flagged. Each such input also holds a clean case that must not be flagged.
  - **Fair tests.** Every try gets the same input. Before a test is used, Python solves it with its
    own reference method and refuses it unless the built-in answer comes back within the tolerance.
  - **Status.** One wrong result fails the claim, and the page shows which task failed.
  - **The test computer must have what the skill needs.** A skill that cannot run as shipped is a
    finding, recorded as such.
- **Retired by this design:**
  - one claim per section, and the five-claim cap;
  - fact-by-fact coverage and the critique's coverage list;
  - the coverage-gap and concern returns.

  The claim-only check needs rethinking (open question 5).
- **Budget.** About 3 tasks per claim, 3 tries each: 9 test sessions per claim, against 18 or more
  today, though each runs longer.
  - The time limit: `__main__.py` accepts at most 7,200 s, so 3 hours needs a code change and
    re-registering with `--timeout 10800`.
  - The real limit is the 5-hour usage window, about 15% per claim today (`32e60bd6`: 4 claims,
    63%). More claims need cheaper claims first; pausing at the limit and continuing is the fallback.
- **The dose-response sketch.** `dose_sim.py` in scratchpad `c7991202…`: 2,000 simulated plates per
  case, fitted with scipy the way the skill's script does.
  - **Claim 1, "Fit an experiment and compare potency"** (When to use this, Steps 1–3).
    - Test 1's plate:
      - inhibitors A (built-in IC50 100 nM) and B (1,000 nM), Hill slope 1;
      - ten concentrations from 1.5 nM to 30 µM, three wells each;
      - vehicle and blank wells, with noise of 4% of the signal window.
    - The test AI writes `results.json`. Python checks:
      - each IC50 within ±35% of its built-in value;
      - the fold shift 10 ± 45%;
      - `more_potent` is A;
      - the Hill slope between 0.7 and 1.4;
      - no flags.
    - A correct analysis passes on 99.1% of plates (96.0% at ±25% for the IC50s and ±35% for the
      fold shift).
    - Common mistakes fail by far:
      - log10 concentrations fed to the fitter report about 2 nM for 100;
      - an inverted ratio gives 0.1 for 10;
      - µM gives 0.1 for 100.
  - **Claim 2, "Warn when the data can't give a clean IC50"** (Step 4, Honest limitations).
    - Test 2 plants C's IC50 above the tested range, and it must be flagged `incomplete_curve`. The
      skill's own script flags it on 90% of plates when the IC50 is 3× the top concentration and on
      60% at 10×; its fitted IC50 ranges from 10⁻¹⁵⁷ to 10¹⁰ nM.
    - Test 3 gives E a U-shape, and it must be flagged `biphasic`. The skill says such data will look
      poor, with a low r², but the fit kept r² ≥ 0.90 on every plate, with a bump of 25% or 45%
      above control. An AI that trusts the skill's r² sign would miss it.
  - Set aside: Related skills.
  - **As shipped, the skill cannot run offline.** Its main tool, the ToolUniverse `tu` command, is
    not on the test computer, and its script needs numpy and scipy, which the skill does not declare.

**5. The whole-skill task design, built.** The operator answered open questions 4 to 7: a task
whose answer Python builds can reach A ("if its easy that python could build it, then it could do
A"); drop the claim-only check for tasks; yes, every section of a claim must be used by a task; do
nothing about cost for now. Then: "Merge the current branch into main, delete it and then start on
a new branch and build all we have talked about, do everything by your recommendation if we haven't
discussed about."
- **Branches.** `main` fast-forwarded to `ba4eeb7` and pushed; `skill-environments` deleted locally
  and on GitHub; new branch `whole-skill-tests`, pushed. The build is commit `08a4cb5` and the
  commit carrying this entry.
- **Contracts first**, in the same commit as the code:
  - [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md), new and pinned for the
    planner (9.8 KB), owns claims and task tests;
  - [`local-contract.md`](skills/scientific-verifier/references/local-contract.md): "Claims" rewritten;
    grade A's reference rule gains planted values; claim-only answers and the returns are for
    question designs only; a task's subject input;
  - [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md): "Cases each
    grade requires" counts tasks (A at least 3 counting tasks, B and C at least 2) and gains the
    verdict `unsound`. To keep the verification profile's bootstrap under its 200,000-byte budget, the
    replay history behind the claim-only rule was cut from it; it is in the 2026-09-24 archive entry;
  - `workflow.md`'s matrix and `qualify_local_tasks` in `tool-contracts.md`, together, with
    `tasks_required`, `sections_incomplete` and `sections_unused`; `artifact-contracts.md` records;
    `LOCAL-INSTALL.md` and `LOCAL-CONFIG.md`; `CLAUDE.md` lists `local-tasks.md` as authoritative.
- **Claims.** `load_submitted_skill` numbers the sections of `SKILL.md` `S1`, `S2`, ... Each claim
  names its sections, sections with nothing to test are set aside with a reason, and Python refuses
  a manifest that leaves one out, holds one twice or names an unknown one. At most 12 claims, since
  12 claims of 3 tasks and 3 trials use 108 of the 128 subject calls; the planner chooses the number.
- **Tasks** (`qualify_local_tasks`, [`local_tasks.py`](src/sci_ai_verifier/local_tasks.py)). One to
  six tasks, each with a job, the claim's sections it uses, and one to twelve output fields of type
  number, text, boolean or set:
  - the planner's generator, implementing a model quoted from a fetched reference, runs once per task
    in the operator's image with no network, writes the input files and prints the planted values;
    a planted text, boolean or set (which compound is more potent, whether a problem is present) also
    quotes the rule it follows;
  - an output may instead quote its value from a reference, and a task may take a fetched dataset as
    an input file;
  - the planner's reference solution runs on each task, with the input the test AI gets, and every
    output must pass on its results, or the design is rejected naming each miss;
  - every section of the claim must be used by some task;
  - Python stores the files, and every trial gets the same bytes at `/task`, read-only.
- **Trials.** The test AI gets the whole skill, never the claim, and writes `/work/results.json`.
  Python reads it: a number within its tolerance (relative, absolute or 0.000001), a text or set
  ignoring case and spacing, a boolean exactly. A wrong value fails the trial; a missing file or field
  with nothing wrong is `invalid`. No AI reader reads a task. One wrong result fails the claim.
  Python also records each module or command the trial's tools reported missing, as a finding.
- **Grades and the critique.** A design whose answers are planted from a quoted model, or quoted
  token-exactly, can reach A with 3 counting tasks and 3 trials. The critique gets its own rubric,
  `local-task-critique-v1`, and the text of the claim's sections; it has no coverage list and no
  verdict per earlier concern, and there are no claim-only answers and no coverage-gap or concern
  returns for tasks. The question rubric, v13, is untouched, so its recorded replies stay exact.
- **What no longer runs on this machine.** With a container configured, `qualify_local_candidate` and
  `qualify_local_evaluator` are refused as `tasks_required`, so question designs, calculated answers
  and generated evaluators go unused. Their code and contracts stay for a setup without a container
  and for reading old runs; two integration tests exercise them with the rule switched off. A task
  design cannot yet be exported to a catalog.
- **Time and limits.** `__main__.py` accepts up to 10,800 s, and I re-registered the user-scope
  connection with `--timeout 10800`, every other argument and the token placeholder unchanged
  (checked in `~/.claude.json`). The default per-session limit rose from 120 to 600 s, and I changed
  the operator's `.verifier/local-settings.json` to 600 likewise (the previous file is saved in the
  scratchpad of session `c7991202`); a task session gets 40 turns instead of 24; the end-of-run
  re-run budgets 5 minutes per task trial.
- **The planner** is told to test by tasks (prompt step 3) and sees the operator image's packages
  (numpy 2.5.3, pandas 3.0.6, RDKit, Pillow; no scipy), where generators and solvers run.
- **Report and page.** `report-card.md` has a row per task trial naming each output that missed; the
  HTML page has a task table (job, sections, checked outputs with tolerances, each try), a fold per
  task (files, where each expected value came from, the solver's results, each try's outputs), the
  generator's model and both programs, set-aside sections with their reasons, and run problems.
- **Verification.**
  - Suite 450 → 469 tests, 467 passing and 2 skipped. New tests check the output rules, the trial
    status, each refusal of a design, a generator or solver fault named for the planner, the re-check
    of a saved design from its records, a full claim through qualify, critique, execution and report,
    a wrong result failing the claim, a missing results file, a critique lowering the ceiling, a
    design for another claim's sections, the read-only mount, the page, and the export refusal.
  - Live, no AI: in the operator's image a generator built a two-inhibitor plate (planted IC50s
    100 and 1,000 nM, Hill 1, 4% noise) and a numpy-only four-parameter fit recovered 91 and 931 nM,
    fold shift 10.2, in 3.5 s; the re-check from records passed. A subject container mounted the
    plate read-only (a write was refused) and returned `results.json` as its only new file.
  - Live, AI, about $0.66 in all: one test session (Opus 5, 69 s, $0.29) used the dose-response skill
    on that plate, found neither scipy nor `tu`, wrote its own numpy fit and passed all four outputs
    (IC50 92 and 941, fold shift 10.2, more potent A), with `missing Python module scipy` recorded.
    One task critique (Opus 5, 107 s, $0.37) answered in its schema, counted the task and objected
    with substance: the Hill slope the claim promises was not checked, a 35% tolerance with 3-fold
    steps lets reading off the nearest concentration pass, and the noise made negative signals.
- **Docker Desktop** would not start on this machine: its backend crashed renaming stale socket files
  (`Docker\run\sailor-ingest.sock`, then `docker-secrets-engine\engine.sock`). I renamed both folders
  aside (`run.stale-20261005`, `run.stale2-20261005`, `docker-secrets-engine.stale-20261005`; nothing
  deleted) and it started.
- **Not done:** no live verifier run; the final reviewer; catalog export of task designs; a version
  bump. `src/` changed, so a run needs a Code session started after this commit. Export and the
  version bump were done in section 6.

**6. Question tests removed, version 0.8.0.** The operator answered open questions 8 to 11: "I think
we already give the verifier power for installing pre-request packages. If not, give the verifier the
power and add scipy", "Yes" to removing the question tests, "yes" to a wrong result winning, "yes" to
0.8.0, and "Also do the clean up for me".
- **Packages a skill imports.** The verifier installed only packages a skill declares, and
  dose-response imports numpy and scipy without declaring them. Now an undeclared import listed in a
  reviewed table of 26 modules (`IMPORT_DISTRIBUTIONS` in [`environment.py`](src/sci_ai_verifier/environment.py),
  owned by "Packages a skill declares or imports" in
  [`resource-policy.md`](skills/scientific-verifier/references/resource-policy.md)) is installed too,
  and anything else is reported, never guessed. A skill that declares nothing gets a build only when
  the operator image lacks a listed import. The planner's block and the report name what was added
  from imports. Contracts first: `local-contract.md` ("Skill environment"), the policy table,
  `LOCAL-CONFIG.md`. 5 new tests.
- **scipy in the operator's image.** `images/rdkit/requirements.txt` gains `scipy==1.18.1`, hash-pinned.
  Built as `sci-verifier-rdkit:2026.3.6-scipy1.18.1`, ID `sha256:6876c07f…79da6d`: numpy 2.5.3,
  pandas 3.0.6, RDKit 2026.3.6, Pillow, scipy 1.18.1. The operator's `.verifier/local-settings.json`
  pins it; the previous file is in scratchpad `c7991202…`. The build reused cached apt layers, so a
  fresh machine may need new Debian pins. Dose-response's script can now run; its `tu` command is
  still absent and is still reported.
- **Question tests removed.** Gone: `qualify_local_candidate` and `qualify_local_evaluator` (the
  Desktop manifest lists 33 tools, was 35), `local_evaluators.py` and `local-evaluator-spec.md`,
  calculated answers, the claim-only check, the AI reader, the question critique (rubric v13) with its
  coverage-gap and concern returns, and the text-only subject (`TextRuntime`). The code is in Git
  history. Old runs' records still render, and saved question designs stay on disk, unlisted.
- **Status.** A failed trial fails the claim whatever the others say; with none failed, an invalid
  trial leaves it inconclusive (`local-contract.md`).
- **Found while porting the tests, and fixed:**
  - the documentary step read a question field from a task design and would have crashed;
  - the task critique had lost v13's rule that a described search is judged by Python's search
    record; restored in criterion 4, as rubric `local-task-critique-v2`;
  - a task design's critique packet has no size guarantee: about 2.3 MB at every schema maximum,
    against a 512 KB limit, where real ones are 17 to 23 KB. Selection now refuses an oversized
    packet as `critique_packet_too_large` before any session, instead of ending the claim
    (`tool-contracts.md`);
  - task designs now export with their input files, and an import qualifies them again in the
    importer's container, which must rebuild the same files and planted values (`local-contract.md`).
    Release ranges default to 0.8.0 up to 0.9.0;
  - `validate_task_critique` was split out, so the tests' critique double goes through the real
    validator again.
- **Version 0.8.0** in `__init__.py`, `pyproject.toml`, the Desktop manifest, `SKILL.md`, `README.md`,
  `LOCAL-INSTALL.md` and `CLAUDE.md`; saved records from 0.8.0 are accepted. `README.md`,
  `LOCAL-INSTALL.md` and `LOCAL-CONFIG.md` no longer describe generated evaluators, the AI reader or
  question replies, and the `subject_refused` row now says the claim is re-run once.
- **Cleanup of `.verifier/`**, moved and not deleted, into scratchpad `c7991202…`: run `90c60cbe`
  with its attempt, subject runs and 10 candidates (`cleaned-90c60cbe/`), the live task checks and two
  synthetic fixture workspaces. Kept: runs `76ce4af1` and `32e60bd6` (untouched), the store, the
  reports and 13 candidates.
- **Verification.**
  - Suite 469 → 378 tests, 376 passing and 2 skipped. The question tests went. The rest were
    rewritten for tasks, with new tests for the import table, the status rule, the packet refusal, a
    catalog round trip that rebuilds the files, and the task critique's schema.
  - `tests/recorded/` keeps the assessor, refusal and session-limit streams, plus two retired
    sessions that show Claude Code's schema-correction loop.
  - The synthetic end-to-end fixture completes, and the operator's settings load.
  - Sizes: the verification bootstrap is 196,388 of 200,000 bytes. The stage 2 bootstrap is 119,604
    of 120,000, only 396 bytes spare. The largest pinned local document is `local-contract.md`, at
    34,540 of 40,960.
- **Not verified live:** a verifier run with tasks; the import table on a live skill. No real reply
  to the task critique's schema is recorded, so `test_recorded_replies.py` checks that schema with a
  hand-written one. Superseded by section 7.

**7. A recorded task critique, and room in the stage 2 bootstrap.** The operator answered open
questions 12 and 13: "yes, record it" and "trim a pinned document".
- **The recording.**
  - No verifier run has produced a task packet, so the packet comes from a live check. Today's code
    qualified three two-inhibitor plates in the operator's image in 17 s. The plates came from the
    live check's generator, and its reference solution passed all twelve outputs. The design used
    sections S2 to S5 of the real dose-response skill.
  - Python computed the ceiling, A with no limits, and `critique_packet` built the 22,776-byte
    packet. The reference page, claim and justification were written for the check.
  - One `claude-opus-5` session judged it under rubric v2, in 133 s for $0.49. It supported B,
    counted all three tasks, and named five objections: the Hill slope the claim promises is never
    scored; there is one plate layout; normalization is not exercised; a 35% tolerance lets an
    interpolation pass; the reference is a fixture.
  - Its first reply put the task verdicts beside the other fields instead of under `case_verdicts`.
    Claude Code refused it, and the session resent it.
  - The stream (`tests/recorded/critic-task-structured.jsonl`, 71,948 bytes) and the packet are in
    `tests/recorded/`, with no credential bytes. The script is `record_task_critique.py` in
    scratchpad `c7991202…`.
  - New tests: the reply answers its own packet under the live rubric's digest, and `critique_tasks`
    replayed over it sends that packet, schema and deadline. A change to the task rubric now needs a
    new recording.
  - `tests/recorded/README.md` allows a live check's packet while no run has produced one.
- **The trim.** `SKILL.md`, pinned in the stage 2, stage 3, verification and demo bootstraps, went
  from 11,227 to 9,635 bytes. Where it restated a rule, it now names the owner:
  - "Session bootstrap and trust classes" in `workflow.md`;
  - "Negotiating the grade" in `evidence-rubric.md`;
  - `stage2-contract.md`;
  - `workflow.md`'s plan requirements.

  Its claim that the local profile "does not execute proposed code" was false and is corrected.
- **Bootstrap sizes.** Stage 2 is now 118,018 of 120,000 bytes (1,982 spare, from 396), and
  verification 194,805 of 200,000.
- **Also fixed:**
  - `stage2-contract.md` said "The 0.5.0 reader supports … 0.2.0 … 0.5.0". It now points at
    `SUPPORTED_IMPLEMENTATION_VERSIONS`.
  - `CLAUDE.md` said tasks are used "whenever a container is configured".
- **Verification:** suite 380 tests, 378 passing and 2 skipped.

### Decisions taken 2026-10-05

- **The page is for the lab and the operator**, and may later be served from a web server (operator).
- **The final reviewer**: failures plus a sample of passes; disputed tests re-run, fixing the part at
  fault (operator).
- **Build the page first and test it before the reviewer** (operator).
- **A page after every completed run unless the user declines, and the calling agent writes its
  summaries** (operator).
- Proposed here and built:
  - plain text comes from a notes file and is marked as written after the run;
  - the page has no JavaScript;
  - the opt-out is an argument the agent sets from the user's words, and `--no-html` on the CLI;
  - the agent fills a template beside the page, and a page that fails never changes a run.
- Superseded the same day: "a view made by a script, not yet a run artifact, so no contract changes".
  Runs now make the page, and the public interface sentence in `local-contract.md` changed.
- **Test the whole skill by running it** (operator, section 4):
  - the planner groups the whole skill into claims, and Python checks that nothing is left out;
  - the number of claims grows with the skill's length;
  - a 3-hour limit;
  - claims are tested as wholes, by tasks whose output is checked.

  Built the same day (section 5).
- **Operator, after section 4:** a task whose answer Python builds can reach A; drop the claim-only
  check for tasks; every section of a claim must be used by a task; nothing about cost for now;
  merge `skill-environments`, delete it, and build on a new branch.
- **Proposed here and built (section 5):**
  - sections numbered by Python, set-asides with reasons, at most 12 claims;
  - a separate tool and module for task designs, with a generator and a reference solution, and the
    four output types;
  - planted judgments must quote the rule they follow;
  - inputs read-only at `/task`, results in `/work/results.json`, read by Python with no AI reader;
  - a wrong value fails a trial even when another field is missing;
  - A needs 3 counting tasks, B and C 2;
  - a separate critique rubric, leaving the question rubric and its recordings untouched;
  - with a container, question designs, calculated answers and generated evaluators are refused;
  - missing modules and commands recorded as findings; the operator image's packages shown;
  - 600 s per session, 40 turns per task session, 5 minutes per task trial in the re-run budget;
    the three-hour registration.
- **Superseded today:** "one claim per section, at most five" and "tested fact by fact" (entries of
  2026-09-29 to 2026-10-01) are retired; claim-only answers (2026-09-24) and the coverage-gap and
  concern returns (2026-10-01) now apply to question designs only, which no longer run here.
- **Operator, after section 5 (section 6):** give the verifier the power to install a skill's
  packages and add scipy; remove the question tests; a wrong result outweighs an unreadable one;
  version 0.8.0; clean up `.verifier/`.
- **Proposed here and built (section 6):** the import table, with nothing guessed outside it; refusing
  an oversized critique packet; exporting task designs with their files, and qualifying them again on
  import.
- **Operator, after section 6 (section 7):** record a real task critique; trim a pinned document
  rather than raise the stage 2 budget.
- **Superseded in section 6:** section 5's "the question rubric, v13, is untouched", "question designs
  … are refused as `tasks_required`; their code and contracts stay", "a task design cannot yet be
  exported", the image without scipy, and open question 8's recommendation to wait for a live run.

### Open questions for the operator

1. The 2026-10-02 entry's questions stand.
2. For the final reviewer: how large a sample of passes; how much time and how many subject calls a
   re-run may use; and whether a re-run repeats the whole claim or only the disputed tests.
3. Should the final reviewer, once built, write into the same notes, beside the calling agent's
   summaries?
4. to 7. Answered by the operator (section 5).
8. to 11. Answered by the operator (section 6).
12. and 13. Answered by the operator (section 7).
14. **Re-record from a real run?** The recorded critique's packet came from a live check, with a fixture
   reference and a claim written for it. Replace it with the first real run's packet, about $0.50?
   Recommended: yes, after that run, unless the rubric has not changed and the recording still passes.

### Urgent next steps, if any

None for the code: committed and pushed on `whole-skill-tests` with this entry. Before the first
live run with tasks, a prerequisite: start a **new** Code session, so that its `serve-local` runs this
branch's 0.8.0 code with the three-hour registration; a session started earlier keeps old code.

### Suggested next move

Run the verifier live on task tests, on a skill already run with questions, so the two designs can
be compared: tooluniverse-dose-response first (8 sections, 5 earlier runs). Merge `whole-skill-tests`
once a run has worked. The final reviewer comes after, on the new tests.

### Recommended next action

With the operator's go-ahead, after their cleanup of `.verifier/` and a check of Docker and the usage
window:
1. Start a new Code session on `whole-skill-tests` and run `verify_skill` on
   `D:\Su Lab\verifier-submissions\examples\tooluniverse-dose-response`.
2. It is finished when the report and page exist, and the run shows:
   - a manifest holding every section, with Related skills set aside with a reason;
   - each claim tested by a qualified task design whose reference solution passed;
   - the critique's verdicts per task, and whether it pushed for tighter tolerances;
   - each trial's `results.json` read by Python; with scipy in the image, the skill's script runs,
     and `missing command tu` should appear among the run problems;
   - time and cost per claim, against the 4 claims and $30 of run `90c60cbe`.
3. Record it in a new entry, with what to change before the next skill.

## Claude: 2026-10-06 (runs f84c131c and 2bef9e0d, the first with task tests; a reviewed command table for ToolUniverse's `tu`; the coverage return for tasks; departures, rules given and passes on tolerance)

### Current stage and status

Version 0.8.0, local workflow, on `whole-skill-tests`, which is the operator's to merge. The first
live run with task tests, `f84c131c` on tooluniverse-dose-response, completed. All four claims
settled at grade A with status pass, and 48 of 48 trials passed. That is a second skill family's
A branch working under tasks. It does not show full coverage: each reviewer named parts of its
claim that no task tested, and the data were nearly noise-free. The verifier now installs
ToolUniverse's `tu`, which the run lacked, through a reviewed command table. That table was checked
live but no run has used it yet. A critique that agrees with a grade, A included, but lists untested
parts of the claim now sends the claim back once (section 7).

Run `2bef9e0d` on western-blot-quantification, the first with the coverage return, also settled four
claims at A with status pass, 57 of 57 trials, and covered 75% of the skill's words against 13% under
questions. It also showed what a pass can hide: the skill's two-step formula is wrong when lanes are
loaded unequally, no task loaded them unequally, and the tolerance absorbed the difference
(section 8). The operator chose four options from open questions 6 and 7, and all four are built
(section 9): a departure of the skill from the reference holds the grade, a task may not state a
rule the claim supplies, a pass far from the reference is marked, and no search ends a coverage
return. No run has used them yet.

### What has been done

This session, 2026-10-06:

**1. Run `f84c131c`.** The operator: "use scientific-verifier-local to verify this skill … Show me
observation table where each row is one claim … per claim table, each row is one test".
- **Preflight.**
  - Docker had stopped when Claude restarted; launching Docker Desktop brought the engine up in
    20 s.
  - The 5-hour window was at 0%, and the run took it to 55%.
  - This session's `serve-local` started at 00:18, after the last commit.
- **Result.**
  - Four claims: S1, S2 and S4; S3; S5; S6 and S7. S8, Related skills, was set aside.
  - Each claim had 4 tasks of 3 trials: grade A, pass, 12 of 12 trials passing, unanimous, no
    invalid trials, one critique round, every task counted.
  - Run time 78 of 180 minutes, cost $23.04: planner $12.61 over 46 turns, trials about $8.5,
    critiques about $1.9.
  - 47 of 48 tries ran the skill's own fitting script, which scipy in the image made possible.
    Run problems: `tu` missing in 3 tries, `cygpath` in 1.
  - The models came from GraphPad Prism's curve-fitting guide. Claim 3's two judgment rules came
    from Wikipedia, a tertiary source.
- **Delivered.** The page's notes were filled and the page redrawn, and the operator got tables per
  claim and per task. Records: [report-card.md](.verifier/runs/f84c131c-b936-4534-b7ff-043ca2cb0216/report-card.md).

**2. Why parts stay untested.** The operator asked: "what's the reason there are still parts we
don't test? did we set a too high budget for number of tests we can give?" No cap was binding:
each claim used 4 of 6 tasks and at most 5 of 12 outputs, and the run used 48 of 128 trial calls
and 78 of 180 minutes. The records show three causes:
- **The skill's own thresholds have no outside source.** These are the r-squared rule, the
  steep/shallow slope labels and the minimum point count. Grade A forbids keying an expected value
  to the skill's text, and the planner said so for claims 3 and 4.
- **Python checks that every section is used, not every rule.** The planner built grade A's 3
  tasks plus one spare and listed what it skipped: the confidence interval and log IC50, the
  point-count rule, the IC50-versus-Ki warning.
- **Gaps had no consequence.** Every critique named gaps and weak tests, such as blanks too small
  for blank subtraction to matter, but agreed with A and required no revision. The coverage-gap
  return that acted on that was retired with question tests on 2026-10-05.

Proposed, not decided: open questions 1 and 2.

**3. `tu` and the command table.** The operator: "yes, run the check and add tu if it passes".
- **Why it was missing.** The skill declares nothing, and `tu` is a shell command, not a Python
  import. The install rules covered declarations and the import table only, so setup recorded
  `not_needed`.
- **The check.**
  - `tooluniverse` 1.5.6 on PyPI provides `tu`, its console script `tooluniverse_cli_entry:main`.
  - Its dose-response tools compute locally with scipy; its source says "No external API calls".
  - Built through the verifier's own `_build`: 70 s, 109 wheels and 155 MB, against caps of 200
    wheels and 1 GiB. The largest wheels are scipy, faiss-cpu, numpy, pandas and tooluniverse.
  - In a trial container (no network, read-only root, user 65534, 512 MiB, 1 CPU) all three tools
    ran in about 2.6 s each: IC50 0.762 with r-squared 0.9998, and a fold shift of 13.4.
- **Built.** Contracts came first:
  - [`resource-policy.md`](skills/scientific-verifier/references/resource-policy.md) gains a
    command table, `tu` to `tooluniverse`;
  - [`local-contract.md`](skills/scientific-verifier/references/local-contract.md) "Skill
    environment" gains **Commands.**;
  - `LOCAL-CONFIG.md` says the same.

  Then [`environment.py`](src/sci_ai_verifier/environment.py):
  - `COMMAND_DISTRIBUTIONS` holds the table;
  - `run_commands` reads the first word of each simple command in a shell or unmarked fenced
    block of Markdown. On an unclosed quote it falls back to the line's first word, which the
    skill's three-line JSON needs;
  - the image probe reports `commands_unavailable`, and with nothing declared a listed command the
    operator's image lacks triggers a build that also holds every listed import;
  - the planner's block and the report line name the commands.

  Three new tests cover detection, the build and no build.
- **End to end on the real skill.** Setup found `tu`, built numpy, scipy and tooluniverse
  (109 wheels, 67 s), `tu` answered in a trial container, and the image was removed.
- **Cost.** Every verification of this skill now spends about 70 s of setup and downloads about
  155 MB, since environments are not cached.

**4. A skill bug.** The skill's `scripts/fit_dose_response.py --help` crashes: two help strings
hold a bare `%`, which argparse formats. Fitting is unaffected. The fix belongs to the skill.

**5. Docker** crashed at startup again on stale socket files. Two rounds of renaming
`%LOCALAPPDATA%\Docker\run` and `%LOCALAPPDATA%\docker-secrets-engine` aside (`*.stale-20261006`,
then `*.stale2-20261006`; nothing deleted) brought the engine back.

**6. Verification.**
- Suite 380 → 383 tests, 381 passing and 2 skipped.
- Sizes: the verification bootstrap is 194,947 of 200,000 bytes; stage 2 118,018 of 120,000;
  `local-contract.md` 35,020 of 40,960.

**7. The coverage return for tasks.** The operator: "add the coverage return for tasks", and yes to
re-recording the critique from one of `f84c131c`'s real packets.
- **Contracts first.**
  - `select_local_candidate` in
    [`tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md) owns the rule:
    **The coverage return**, the refusal `return_unsearched`, and `coverage_gaps` in the critique's
    reply.
  - `workflow.md`'s transition text moves with it.
  - `local-tasks.md`, step 4 of "Negotiating the grade" in `evidence-rubric.md`,
    `artifact-contracts.md` and `local-contract.md` point at it.
- **The rubric, v3.** The critique lists in `coverage_gaps`, whatever its grade, what the claim's
  sections say to do, check or conclude that no task tests, each with the task or search that would
  test it. The reply schema requires the field.
- **The return.**
  - A critique that agrees with the proposal (the settled grade equals it) and lists gaps sends the
    claim back once per claim, **at every grade, A included**. The question-era return skipped A, so
    it would have asked nothing in `f84c131c`, where every claim was A.
  - Accepting the same design afterwards needs a search or fetch for the claim in Python's record
    made since the return, or it is refused as `return_unsearched`; with no workflow log nothing is
    checked.
  - A revised design is critiqued as usual and never returned for gaps again; its critique sees
    "An earlier version left untested: …" among the carried concerns.
- **Report and page.** `report-card.md` gains "Coverage gap:" lines and "Returned once for coverage
  gaps". The page now shows the untested count and list for task claims too.
- **The re-recording.** Run `f84c131c` claim 3's stored packet, with v3 in place of v2, judged by
  `claude-opus-5` in 195 s for $0.70.
  - A, all four tasks counted, three objections, and five coverage gaps: the slope labels, the
    r-squared rule, the bottom plateau, the in-range IC50 check and the fold-shift caveat. Under the
    new rule that claim would have come back once.
  - Its first reply added a stray `paramete r_name` key, which Claude Code refused, and the session
    resent it.
  - It replaces the live-check recording, so `tests/recorded/README.md` drops the live-check
    exception.
- **Verification.**
  - 4 new tests: the return at A with the search check; once per claim; no log; no gaps, or a grade
    below the proposal.
  - Suite 383 → 387 tests, 385 passing and 2 skipped. The verification bootstrap is 195,150 of
    200,000 bytes.

**8. Run `2bef9e0d`.** The operator: "clean and run the verifier on western blot skill", then "yes,
record it and draft the options".
- **Cleanup.** Moved, nothing deleted, into session `0f5df502`'s scratchpad: run `f84c131c` with its
  attempt, subject runs and 5 candidates (`cleaned-f84c131c/`, 4,641 files), and the false start
  below (`cleaned-6bd93bfc/`, 94 files). Kept: runs `32e60bd6` and `76ce4af1`, the store, the reports
  and 13 candidates.
- **A false start.** This session's `serve-local` dated from 06:37, before commits `3d41f1b` and
  `a31f708`. I ran the same action through `scripts/verify.py verify` with the registration's
  arguments in a background shell instead. That run, `6bd93bfc`, died two minutes in when the app
  restarted the session. The restarted session's server postdated both commits, and `verify_skill`
  ran `2bef9e0d` from it.
- **Preflight.** Docker was up. The 5-hour window was at 3%, and the run took it to 72%, the most of
  any run so far.
- **Result.** [report-card.md](.verifier/runs/2bef9e0d-f74d-4362-8a06-55e3a8385014/report-card.md).
  The page's notes were filled and the page redrawn.

  | Claim | Sections | Tasks before → after the return | Trials passed | After the return | Gaps listed |
  | --- | --- | --- | --- | --- | --- |
  | 1. Loading-control normalization | S4, S5, S11–S13, S27 | 4 → 4 | 12 of 12 | two web searches, same design | 3 |
  | 2. Fold change, then averaging | S6, S7, S14, S15, S26 | 4 → 4 | 12 of 12 | two web searches, same design | 7 |
  | 3. Choosing the analysis route | S8, S17–S19 | 4 → 5, rewritten | 15 of 15 | revised | 8 → 7 |
  | 4. Mistakes that spoil quantification | S20–S24, S28, S29 | 4 → 6 | 18 of 18 | revised | 7 → 6 |

  - Every claim: grade A, pass, unanimous, no invalid trials, every task counted, two critique rounds.
  - Set aside with reasons: S1–S3 (title, metadata, overview), S9 and S10 (image steps whose tools the
    skill does not ship), S16 (plots), S25 (output files) and S30 (references). Coverage: 1,916 of
    2,558 words (75%) and 22 of 30 sections, against 333 words (13%) and 4 sections in the
    question-era run `32e60bd6`.
  - Run time 98.5 of 180 minutes, cost $34.7: planner $19.97 over 53 turns, 57 trials $9.41, 6
    critiques $5.36. `f84c131c` took 78 minutes and $23.0, `32e60bd6` 78 minutes and $30.9.
- **The coverage return.** Every critique agreed with A and listed gaps, so every claim came back
  once.
  - Claims 3 and 4 were revised. For claim 3 the planner, citing the critique, found each branch of
    the decision tree tested on one side only. Claim 4 gained tasks on the order of averaging and on
    a highly variable repeat.
  - Claims 1 and 2 each ran two web searches at once, opened no result and accepted the same design.
    That satisfied the `return_unsearched` check.
- **A flaw the pass hid.**
  - The skill's two-step formula divides the modified form by the total form over the loading
    control. That is the modified form times the loading control over the total form, so it does not
    cancel unequal loading.
  - All four tasks built on it (wb2, wb4, c2d, e4) loaded every lane within about 6%. The planner
    noted that then "the answer does not depend on which of the two published ratio conventions is
    used".
  - The test AI followed the skill and came out up to 3.4%, 5.4%, 5.5% and 2.4% off the key, inside
    tolerances of 10%, 10%, 8% and 8%.
  - Claim 1's critique computed exactly this, wrote that a subject following the sections verbatim
    passes, and listed it as a coverage gap. The rubric's fairness criterion asks that a correct
    analysis following the skill passes, which assumes the skill's procedure is the correct one.
- **Tasks that state their rule.** Claim 4's jobs gave the deciding thresholds (15%, 15%, 10%, a
  coefficient of variation of 0.5); g3 named the planted defect and g5 both orders of averaging. Its
  critique objected that the tasks test "correct execution of a given rule, not whether the skill
  surfaces the defect or chooses the criterion", and counted them.
- **Checked against `f84c131c`,** the other task run, since the 2026-10-02 bar asks for more than one
  skill:
  - Every answer there was within 0.18% of the reference solver's result for the same file, even
    where 20–28% off a small planted plateau, which is fitting noise. Here the four two-step tasks
    were 2.4–5.5% off the solver, and every other task within 0.01%. "Off the solver but inside the
    tolerance" separates the two runs exactly.
  - Its `c4_midpoint_not_sampled` job also defined its criterion ("between 25 percent and 75
    percent"), so tasks that state their rule occur in both skills.
  - Its critiques named regimes its tasks avoided, such as midpoints well inside the range, but its
    answers matched the solver, so it shows no hidden departure like the two-step one.

**9. Departures, rules given, passes on tolerance, and no search to end a return.** The operator:
"build the recommended options: 6a, 6c, 6d drop, 7a", then the claim-1 re-recording.
- **Contracts first.**
  - [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md) owns the task rules: a
    job may not give a rule, threshold or order of steps the claim's sections supply, and a rule
    they lack is named in `criterion_given`; **Where the skill departs from the reference**; and
    **Passed on tolerance**, with its 0.5% margin.
  - [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md): "Not given
    away", "Right", the `leaked` and `unsound` rows, and steps 4 and 5. `unsound` no longer calls a
    key unfair because following the skill misses it.
  - `select_local_candidate` in
    [`tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md) owns
    **Departures** and the hold, drops `return_unsearched`, and names `departures` and
    `criterion_given` in the critique's reply. `workflow.md`, `artifact-contracts.md` and
    `local-contract.md` point at them.
- **Rubric v4.** Criterion 3 asks that some task expose each departure of the skill's own
  procedure from the reference solution. `rubric.departures` and `rubric.criterion_given` say how
  to report them, and the `leaked` and `unsound` verdicts follow the table. The reply adds
  `departures`, and per task `criterion_given`, empty or the rule.
- **The hold.** While the critique lists a departure, the settled grade is one below the proposal
  it judged: A to B, B to C, C to no grade (policy `evidence-strength-v10`). Accepting that grade
  holds it no lower. A revised design whose critique lists none can settle at the proposal. The
  reply carries `departures` and says how to answer them, and earlier departures reach the next
  critique.
- **Passed on tolerance.** Scoring keeps `reference_result` and `off_reference` for a number that
  passed more than 0.5% from a nonzero reference result. The report lists those tasks and the page
  marks them; status and grade do not change.
- **The coverage return** needs no search to end. The report says whether the planner kept the
  design, and how many gaps it left open, or revised it.
- **Report and page** show departures, rules given, passes on tolerance and how a return ended.
- **The re-recording.** Run `2bef9e0d` claim 1's stored packet, with v4 in place of v3, judged by
  `claude-opus-5` in 274 s for $0.96: a live check of the hold on the case that motivated it.
  - A, all four tasks counted, five objections, three required revisions, three coverage gaps and
    one departure. Followed literally, the skill's two-step formula is the modified form times the
    loading control over the total form, which keeps the per-lane loading, and it agreed with the
    key only because every phospho/total task held loading equal. The critique called them "not two
    defensible readings of one claim" and required a fifth task with about 2-fold loading variation.
  - Under the hold, that claim would have settled at B until such a task existed, not at A.
  - Its first reply added a stray `paramaters` key, which Claude Code refused, and the session
    resent it.
  - It replaces `f84c131c`'s recording, and `tests/recorded/README.md` says so.
- **Verification.**
  - New tests: the hold at A, B and C, and accepting it; a revised design that exposes the
    departure; the tolerance mark, unit and end to end with the page; a rule given, end to end;
    the reply's new shapes. The test of the search check went with it.
  - Suite 387 → 391 tests, 389 passing and 2 skipped.
  - Sizes: the verification bootstrap is 195,574 of 200,000 bytes; every pinned local block is
    under 40,960, the largest `local-contract.md` at 35,047.

### Decisions taken 2026-10-06

- **Operator:** run the `tu` check, and add `tu` if it passes. Done.
- **Operator:** add the coverage return for tasks, and re-record the critique from a real packet.
  Done (section 7).
- **Operator:** clean and run western-blot-quantification, then record the run and draft options for
  its weak spots. Done (section 8).
- **Operator:** build 6(a), 6(c), dropping the search in 6(d), and 7(a), and re-record the critique
  from `2bef9e0d`'s claim-1 packet. Done (section 9).
- **Proposed here and built (section 9):**
  - Python applies the hold, one grade below the proposal the critique judged, instead of trusting
    the critique to lower its own grade; accepting the held grade does not lower it again.
  - `criterion_given` is the critique's judgment, per task.
  - A zero reference result is not compared for the tolerance mark.
- **Proposed here and built:** the return applies at every grade, A included, unlike the
  question-era return, which skipped A.
- **Proposed here and built (section 3):**
  - commands are read from shell or unmarked fenced blocks of Markdown only;
  - an unlisted command is never installed, and a trial that needs it records it as a run problem;
  - the image probe reports missing commands;
  - with nothing declared, a listed command the operator's image lacks triggers a build.

### Open questions for the operator

1. Answered by the operator (section 7).
2. **The skill's own thresholds.** Leave them untested and listed, as now, or test them as "the skill
   follows its own rule" at a grade below A, since the expected values would come from the skill?
3. Answered by the operator (section 7).
4. **Merge `whole-skill-tests`** now that a task run has worked? The merge is the operator's.
5. The 2026-10-05 entry's open questions on the final reviewer stand.
6. Answered by the operator (section 9): (a), (c), and dropping the search in (d). The options as drafted:
   **An A that hid a flaw** (section 8). The design avoided the case where the skill goes wrong, the
   tolerance absorbed the difference, and two web searches closed the return. These options combine:
   - (a) **Flag answers that pass only on tolerance.** After the trials, Python compares each number
     with the reference solver's result for the same file. Beyond 0.5%, which separates the two task
     runs exactly, the report and page mark the task "passed on tolerance only", with the size of the
     difference; grade and status stay. Owners: "Reading a trial's results" in `local-tasks.md`, and
     the report. No rubric change. A subject that rounds hard can trip it, so it informs the reader
     rather than deciding.
   - (b) **As (a), but the flagged task counts as inconclusive,** so the claim's status becomes
     inconclusive and its grade stays. Here claims 1, 2 and 3 would have been inconclusive.
   - (c) **Make a known departure a required revision.** Where the skill's procedure, followed
     literally, departs from the reference solution in a situation the claim covers, at least one
     task must put the departure outside its tolerance. A critique that finds none requires one and
     may not support the proposed grade until it exists. Owners: the task rule in `local-tasks.md`,
     and criterion 3 and the verdicts in `evidence-rubric.md` and the task rubric. The rubric moves to
     v4, which needs a live re-recording of about $0.70, asked first. On this skill claim 1 would most
     likely fail, which is the right result.
   - (d) **The search that ends a return.** Drop it: the planner may keep a design, the report says how
     many gaps it left open, and `return_unsearched` goes. Or require one line per gap, saying why it
     cannot be tested or naming a reference fetched since the return, which Python counts. Or require
     a fetch instead of a search.
   - Recommended: (a), (c), and dropping the search in (d), since under (c) the gaps that matter become
     required revisions. (a) rests on two skills, (c) on one.
7. Answered by the operator (section 9): (a). The options as drafted: **Tasks that state their rule**
   (section 8). `local-tasks.md` already says the job must not tell the
   test AI "which steps of the skill to follow … or which problem was planted", but `leaked` covers
   only naming the problem, and the critique counted such tasks while objecting. Options:
   - (a) Widen `leaked` to a job that states a step, an order or a criterion the claim's sections
     supply; such a task does not count. Where the sections give no criterion, as for when a signal
     stops being proportional to the load, the job may state one, and the report marks the task
     "criterion given".
   - (b) Mark only: the report flags every task whose job states a criterion, and nothing else changes.
   - (c) Leave it to the critique's objections, as now.
   - Recommended: (a). It enforces a rule the contract already has, it occurred in both task runs, and
     it shares 6(c)'s rubric bump and re-recording. Here g3 and g5 would likely not count, which still
     leaves claim 4 four counting tasks.

### Urgent next steps, if any

None. `src/` changed again, so before the next run restart the session and check that its
`serve-local` postdates the commit; do not run around it, since a background `verify` dies with the
session (section 8). Check Docker and usage first.

### Suggested next move

Re-run two skills on the new rules: western-blot-quantification, where claim 1 should now meet a task
with unequal loading or settle below A, and tooluniverse-dose-response, to check that the hold and the
marks do not fire on a skill whose answers match the reference (the 2026-10-02 bar).

### Recommended next action

With the operator's go-ahead, after a session restart and a Docker and usage check:
1. Run `verify_skill` on western-blot-quantification.
2. It is finished when the report shows, for claim 1, either a task with unequal loading and its
   status, or a grade held below A with its departure; and which tasks passed on tolerance only and
   which jobs gave a rule.
3. Then run tooluniverse-dose-response and check that no departure, tolerance mark or rule given
   appears where its answers match the reference. Each run costs $25–35 and most of a 5-hour
   window.

## Claude: 2026-10-07 (the critique answers questions and Python gives each task's verdict; run cfe9e57a)

### Current stage and status

Version 0.8.0 on `whole-skill-tests`, the operator's to merge. The 2026-10-06 entry built a hold for
departures, a mark for passes on tolerance, the rule against tasks that state the skill's rule, and
no search to end a coverage return. Today the task critique stopped choosing verdicts: it answers
one question per row of the verdict table, and Python gives the verdict. Replays of real packets
show the change working, and no run has used it yet.

### What has been done

This session, 2026-10-07:

**1. Other problems in run `2bef9e0d`.** The operator asked whether there were problems besides the two
fixed. Checked against both task runs:
- **The critique never refused a task.** All 43 verdicts in runs `f84c131c` and `2bef9e0d` were
  `counts`, while its objections named six flaws the verdict table excludes: two near-repeats, a
  task that named its planted defect, two keys whose quotes did not support them, a task that
  passed with the normalization skipped, and a solver that hard-coded a planted value. The rule that
  objections and verdicts must agree was already in its rubric.
- **Planner justifications held wrong numbers** in 3 of 4 claims of `2bef9e0d`, and the report shows
  them as written. One skill only, so left for more evidence.
- **What tasks cannot test:** the skill's image steps need tools it does not ship, and plots and
  reporting advice have no output field.
- **Cost and time keep growing:** 98.5 minutes and 69% of a 5-hour window for `2bef9e0d`.
- Minor: one source per run lost to a refused redirect; three trials per task never disagreed in
  105 tries.

**2. Problem 1, checked before building.** The operator: "How would you recommend tackle problem 1",
then "yes" to a replay check.
- A draft rubric replaced the critique's verdicts with five yes-or-no questions, one per row of the
  verdict table, answered before the grade; Python gave the verdict of the first yes.
- Six real packets replayed on `claude-opus-5` for $5.11, 155 to 491 seconds each: four holding the
  flaws, and `f84c131c` claims 1 and 3 as clean controls.
- Four of the five clear flaws stopped counting. The controls kept every task at A. The question
  "would a wrong analysis pass every output?" also caught tasks too loose to tell right from wrong:
  three of `2bef9e0d` claim 3's first design, and two of `f84c131c` claim 2, where skipping blank
  subtraction passes, which its live critique had noted and counted.
- It showed three things to fix: a task that names where its planted problem is, a "rule given"
  note that marked output units and facts about the data, and reviews near the 600-second
  deadline.

**3. Built.** The operator: "yes" to fixing those three and building it.
- **Contracts first.** [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md)
  owns it: the critique answers one question per row of the verdict table, and Python gives a case
  the verdict of the first row answered yes, or `counts`. `leaked` adds where the planted problem
  is, and `unsound` adds any plausible wrong analysis that passes every output.
  `local-tasks.md`, `tool-contracts.md` (the reply shape), `workflow.md` and
  `artifact-contracts.md` point at it, and `local-contract.md` gives the critique fifteen minutes.
- **Code.** Rubric v5 holds `TASK_QUESTIONS`, and the reply's `task_checks` come first and the grade
  last. `task_verdict()` derives `case_verdicts`, so selection, the report and the page read them as
  before. A missing replacement is said, never invented. `criterion_given` excludes units, formats
  and facts about the data. `CRITIC_TIMEOUT_SECONDS` is 900, the policy `evidence-strength-v11`,
  and the page lists each task's five answers.
- **Confirmation through the real code.** `critique_tasks` on two of the replayed packets, three
  sessions for $2.74:
  - `f84c131c` claim 1, the control: all four tasks counted at A, with no "rule given" mark; 184 s.
  - `2bef9e0d` claim 4: g5 dropped as leaked, and "rule given" named only the jobs' cut-offs. g3
    counted in both reviews: the stain mark its job mentions shows in its data anyway, and the
    critique could name no wrong route that passes it.
  - In that first claim-4 review the critique wrote that an un-normalized reading "also passes" g2,
    and still answered no, since g2 was not built to catch it. The question now asks about any wrong
    analysis, even one the task was not built to catch, and says that one it can name means yes.
    Re-checked: g2 and g4 dropped because skipping normalization passes every output; three tasks
    counted and the critique's own grade was B; 438 s, $1.07.
  - That last review is the new recording; its first reply was accepted.
- **Verification.** Suite 391 → 392 tests, 390 passing and 2 skipped. The verification bootstrap is 195,877 of 200,000 bytes; every pinned local block is under 40,960.

**4. The critique's effort.** The operator asked what effort the verifier's sessions use. None was
set: the planner, the subjects and the critique all ran at Claude Code's default for `claude-opus-5`,
`high` per Anthropic's effort documentation; the CLI accepts `--effort` from `low` to `max`. The
operator: "just change the reviewer setting to xhigh, no test". The critique now runs at `xhigh`,
recorded as `effort` on each critique, with twenty minutes instead of fifteen, since it thinks
longer ("Critique" in `local-contract.md`). The planner and the subjects keep the default: a subject
that thinks harder could quietly correct a skill's mistake. No replay checked it; the next run does.
Suite 392 tests, 390 passing and 2 skipped.

**5. Run `cfe9e57a`, and two fixes.** The operator: "clean and run the verifier on western blot
skill", then "yes, do both" to the fixes below.
- **Cleanup.** Run `2bef9e0d`'s files (4,714) moved into session `0f5df502`'s scratchpad
  (`cleaned-2bef9e0d/`); nothing deleted.
- **Result.** Five claims; 2,118 of 2,558 words (83%) in claims, against 75% in `2bef9e0d`, since
  the image steps (S9, S10) became a claim tested on intensity profiles. 145.6 of 180 minutes and
  $35.2: planner $20.79, critiques $8.55, 30 trials $5.62, assessor $0.24.
  - Claims 1, 2 and 5 settled at A and passed, 9 of 9 trials each. The critique dropped tasks in
    claims 1 to 4. Two of claim 5's tasks passed on tolerance only.
  - Claims 3 and 4 ran no task. Each redesign's critique passed the 256 KiB output limit at `xhigh`
    (`claude_output_limit` after 638 and 664 s), so no plan was fixed, and both ended at D,
    inconclusive, by the fallback documentary assessment. Claim 4's first critique had listed two
    departures, the saturation check and including all repetitions against a documented
    exclusion, and held its grade at B.
  - The two-step flaw passed again. The planner did build a task with unequal loading, but its job
    asked for "the phosphorylated fraction of the SMAD2 that is present". The test AI computed that,
    1.4, where the skill's own formula gives 2.45, and the critique counted the task.
- **Fixes.**
  - The critique may write 2 MiB (`CRITIC_OUTPUT_BYTES`); the assessor keeps 256 KiB ("Critique" in
    `local-contract.md`).
  - Rubric v6 adds the question `job_decides` (`leaked` if yes): does the job say how to compute an
    output, so the test AI could answer without the claim's sections? Naming what to report is not
    saying how; a job settling even one output answers yes. `local-tasks.md` tells the planner to ask
    for outputs in the user's terms, and `evidence-rubric.md`'s `leaked` row covers it.
  - Considered and not built: a no-skill control trial per task, which Python would score. Left for
    after the next run.
- **The re-recordings.** Two sessions on `cfe9e57a` claim 1's final packet at `xhigh`, $3.05:
  - The first answered `job_decides` no for every task: the wording "settles that one output", it
    wrote, but another output still needed the skill. The question now says that a job settling
    even one output answers yes.
  - The second dropped all three two-step tasks as leaked, so claim 1 would need a redesign in which
    the skill decides the computation. 579 s; its 284 KB stream would have passed the old limit. Its
    first reply was wrapped in a stray `StructuredOutput` key, refused and resent. It is the new
    recording.
- **Verification.** Suite 392 tests, 390 passing and 2 skipped.

### Decisions taken 2026-10-07

- **Operator:** check problem 1 by replay before building; then fix the three issues it showed and
  build. Done (sections 2 and 3).
- **Operator:** tighten the wrong-analysis question after the re-check. Done (section 3).
- **Operator:** raise the critique's output limit and add the question on jobs that say how to
  compute an output, tightened after its first re-check. Done (section 5).
- **Operator:** run the critique at effort `xhigh`, untested until the next run. Done (section 4).
  The deadline rising to twenty minutes was proposed here and built with it.
- **Proposed here and accepted with the build:** g3, whose job says the Control lane sits over a
  stain mark, counts. Its data show the high background anyway, and the job never says what it does
  to the answer; all three reviews under the questions judged so.

### Open questions for the operator

1. The 2026-10-06 entry's open questions 2, 4 and 5 stand: the skill's own thresholds, merging
   `whole-skill-tests`, and the final reviewer.
2. **Planner justifications with wrong numbers** (section 1): mark them in the report, or wait for a
   second skill to show the same? Recommended: wait.

### Urgent next steps, if any

None. `src/` changed, so restart the session before the next run, and check Docker and usage first.

### Suggested next move

Re-run western-blot-quantification to see claims 3 and 4 reach a fixed plan and claim 1 meet a
two-step task the skill decides, then tooluniverse-dose-response. Do not move to a longer skill yet:
`cfe9e57a` used 146 of 180 minutes for five claims, with each critique taking 8 to 11 minutes.

### Recommended next action

With the operator's go-ahead, after a session restart and a Docker and usage check:
1. Run `verify_skill` on western-blot-quantification.
2. It is finished when the report shows each task's answers, which tasks dropped and why, whether
   claim 1 met a task with unequal loading or settled below A, and the run's time and cost.
3. Then run tooluniverse-dose-response and check that its clean claims keep their tasks. Each run
   costs $25–35 and most of a 5-hour window.

## Claude: 2026-10-08 (run 50104eac stopped on the session limit; run 55d345a3 on neurokit2; reference solutions run where trials run; files past the limits left behind; run 2f395087 confirms both; the critique's effort and model measured by replay)

### Current stage and status

Version 0.8.0 on `whole-skill-tests`, the operator's to merge; the 2026-10-07 entry's state stands.
The first longer skill, neurokit2, completed in run `55d345a3` after `50104eac` stopped on the
session limit. Its two faults that were not the skill's are fixed: a task's reference solution now
runs in the skill's environment, and a trial's oversized side file no longer voids a claim. Open
question 2 of the 2026-09-28 entry is settled by the operator's choice below.

### What has been done

This session, 2026-10-08:
- **Run `50104eac`, neurokit2.** The operator: "Check my usage and Docker, then run the verifier on
  neurokit2". The window was at 20%, Docker up, and the session's server postdated `4877b54`. The
  skill's `uv pip install "neurokit2==0.2.13"` was read as a declared package. After 2 h 22 min, with
  five claims (three with results, one stopped operationally, one still in design) and 40 trials,
  the planner stopped on HTTP 429, "You've hit your session limit". Neither the run nor its claims
  are a finding about the skill.
- **The critique's effort back to `high`.** The operator: "change the reviewer's effort back to
  "high", clean the failed previous run due to usage limit and then run the verifier on neurokit2".
  `CRITIC_EFFORT` is `high`, still passed explicitly; the twenty-minute deadline and the 2 MiB
  output limit stay ("Critique" in `local-contract.md`).
- **Cleanup.** Run `50104eac`'s run, attempt, subject runs and 8 candidates (7,658 files) moved into
  session `60cf88bc`'s scratchpad (`cleaned-50104eac/`); nothing deleted. Run `cfe9e57a` stays.
- **Run `55d345a3`, neurokit2 again** (started at 7% of the window): six claims in 150.6 of 180
  minutes for $48.88, the most so far (planner $27.79, 43 trials $13.04, critiques $7.93). Claims
  cover 59% of `SKILL.md`'s words; seven sections were set aside.
  - C1 data contract B, pass 9/9; C2 preprocessing order A, pass 12/12; C5 multimodal manifest B,
    pass 9/9, held at B by a departure no task exposed (a stream that starts late).
  - C3 ECG: `sandbox_artifacts_invalid` after its first trial. The trial ran the skill's
    `ecg_hrv_pipeline.py --signals-output`, which writes the whole processed signal table (90,000
    rows) beside a four-number `results.json`; the collector raised on the one file over 4 MiB (its
    106-byte stderr matches the "artifact too large" traceback exactly) and the claim ended.
  - C4 EDA: A, **fail** 6/9, a false fail. Task `threshold_against_the_largest_response` planted
    seven responses (4.0, 1.5, 0.30, 0.20, 0.12, 1.0, 0.8 µS) and keyed four kept at
    `amplitude_min` 0.1. The solver, in the operator's image without NeuroKit2, imitated the detector
    with a percentile baseline and also kept four; every trial ran NeuroKit2 0.2.13 and kept five,
    the 0.30 µS response included. The skill's statement that the threshold is relative to the
    largest response is right. Three passes rode the tolerance; a trial lacked `cvxopt` (cvxEDA).
  - C6 complexity: D. The planner skipped task design for lack of time.
  - What worked: the critique dropped weak tasks, the departure hold engaged on C5, and the
    tolerance marks appeared on C4.
- **Decision (operator, "do 1 and 2 … we really need to find a permanent way of fixing this", then
  "yes, build both"): reference solutions run where trials run.** This settles open question 2 of
  the 2026-09-28 entry: a library the skill uses may decide whether a task qualifies, never what its
  key is. Until now each library was added to the operator's image by hand (scipy for
  dose-response; RDKit built in), and a skill whose library was missing got a solver that imitated
  it. Contracts first: "The reference solution" in
  [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md) owns it, with
  [`local-contract.md`](skills/scientific-verifier/references/local-contract.md) ("Subject trials
  and reference solutions"), [`resource-policy.md`](skills/scientific-verifier/references/resource-policy.md),
  [`tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md) and
  [`artifact-contracts.md`](skills/scientific-verifier/references/artifact-contracts.md).
  - `SandboxRunner` takes `solver_image`, the subject image setup built; the generator keeps the
    operator's image, so no package the skill chose touches a planted value. `task_receipts`
    record `generator_image_id` and `solver_image_id` instead of one `image_id`.
  - The planner's environment block says solvers run in the trials' image and should call a library
    the job asks about rather than imitate it; the report's Environment line says where each ran.
  - Not done: catalog requalification still runs both programs in the operator's image, so a design
    whose solver needs the skill's packages does not requalify on another machine.
- **Files past the limits are left behind.** "Files not kept" in `local-tasks.md`: a trial's and a
  solver's collection keeps `results.json` first, leaves any other file past `max_file_bytes`,
  `max_artifacts` or `max_artifact_bytes` in the container, and the trial records each under
  `files_not_kept` (path and size, at most 20); `report-card.md` lists them. A results file past a
  limit, and any file the generator writes past one, is still `sandbox_artifacts_invalid`.
- **Verification.** New tests: the collector's own script run on a folder (results first, a large
  and an extra file left, strict mode and an oversized results file still fail), the host side of
  `collect(keep=…)`, each program's image through `SandboxRunner`, the receipts, the planner
  block and report line, and a task flow whose trials leave a file behind and whose solver ran in a
  built image. Live, no AI: the collector in the operator's image kept `results.json` and named a
  5.2 MB `signals.csv` it left behind, and strict collection still faulted. Suite 396 tests, 394 passing and 2 skipped.
  Committed as `0fb90ca`.
- **Run `2f395087`, neurokit2 with both fixes.** The operator: "Clean and run verifier on NeuroKit2".
  The session restarted after `0fb90ca` (its `serve-local` started 12:45, the commit 12:10), the window
  was at 0% and Docker up. Run `55d345a3`'s run, attempt, subject runs and 12 candidates (7,644 files)
  moved into session `60cf88bc`'s scratchpad (`cleaned-55d345a3/`); nothing deleted. Five claims in
  147 minutes for $44.34 (planner $22.23, 51 trials $15.67, 7 critiques $6.44); every one of the ten
  sections not set aside is in a claim, and none went documentary.
  - C1 ECG and HRV A, pass 12/12; C3 events and epochs A, pass 9/9; C5 inspect before processing
    (six sections) A, pass 12/12.
  - C2 EDA B, pass 6/6, and C4 multimodal B, pass 6/6: the critique found one task in each that a
    wrong analysis passes (`wrong_passes`), leaving two counting tasks.
  - **Both fixes confirmed.** Every solver imported `neurokit2` and ran in the built image
    (`79fd121a…`), every generator in the operator's (`6876c07f…`). Qualification rejected two EDA
    designs because the library disagreed with a planted value (`response_count` expected 2, found 3;
    a tonic level 3.48 against 3.83), before any trial; that is `55d345a3`'s false fail caught where
    it belongs. Two C1 trials wrote a 4,966,033-byte signal table, recorded under `files_not_kept`,
    and were scored.
  - One solver run failed inside SciPy's FFT and the planner revised it; not investigated.
- **The critique's effort and model, measured by replay.** The operator: "I want to test how effort
  level can effect our verifier's work", then asked to add Sonnet 5, then "Sonnet 5, 7 packets, go
  ahead". Run `2f395087`'s seven task-critique packets (live rubric; each judged once live by
  `claude-opus-5` at `high`) were replayed byte for byte, once per cell, on {`claude-opus-5`,
  `claude-sonnet-5`} × {`medium`, `high`, `xhigh`}: 42 sessions through `isolated_answer()` with the
  critique's prompt, schema, deadline and output limit. Nothing in the repository changed, and the
  decision rule was written before any result. $27.94; the 5-hour window went from 2% to 91%, about
  3.2 points a dollar, more than full runs use.

  | Cell | $ a packet | Median s | Median output tokens | Tasks judged otherwise than live (of 23) |
  |---|---|---|---|---|
  | opus-5 `medium` | 0.63 | 147 | 11k | 3, all more lenient |
  | opus-5 `high`, repeated | 0.97 | 389 | 30k | 6 |
  | opus-5 `xhigh` | 1.18 | 510 | 40k | 4 |
  | sonnet-5 `medium` | 0.33 | 171 | 17k | 8 |
  | sonnet-5 `high` | 0.43 | 316 | 28k | 8 |
  | sonnet-5 `xhigh` | 0.52 | 509 | 47k | 6 of 20; C4 round 1 hit the 1200 s deadline |

  - The repeat at `high` disagreed with the live critique on 6 of 23 tasks and 3 of 7 grades. A
    single critique varies about as much as any effort changes it.
  - Reasons were read wherever verdicts split. `medium` missed defects that `high` and `xhigh` named:
    in C2's `five_similar_responses` the absolute 0.1 µS misreading the claim exists to prevent
    passes; in C4's round 1 `aligned_session` an analysis that never reads the timestamps passes every
    output; in C5's round 2 `read_returned_components` the raw value at 30 s passes the tonic window
    its own `tolerance_basis` says rejects it.
  - `xhigh` found nothing that the two `high` samples together missed, at 22% more cost and 30% more
    time.
  - Opus softens at every effort: in C1's `ecg_resting_rsa` and `ecg_low_variability_tachycardia`
    all four Opus critiques named a swap of the RMSSD and SDNN values that passes, and answered no.
    All three Sonnet critiques answered yes, as the question's wording requires. Sonnet also missed
    defects Opus caught (C2 and C5 at `high` and `xhigh`) and raised one pedantic flag (C3, a baseline
    window placed after onset).
  - Decision under the rule: `CRITIC_EFFORT` stays `high` on `claude-opus-5`; no code or contract
    changed. One skill only. The rule, scripts, per-session results and streams are in session
    `3983990c`'s scratchpad (`effort-model/`).
  - A lead, not a change: sampling, not effort, is the larger variation. Keeping the stricter of two
    critiques would change "never re-rolled" ("Critique" in `local-contract.md`) and needs a second
    skill's packets first.

### Urgent next steps, if any

None.

### Suggested next move

Catalog requalification still runs solvers in the operator's image, so neurokit2's designs cannot be
requalified elsewhere; decide whether requalification should build the skill's environment. Then try
another library-wrapping skill. Separately, replaying another skill's critique packets twice at
`high` would show whether the critique's sampling variation above holds beyond neurokit2.

### Recommended next action

Ask the operator whether to give catalog requalification the skill's environment or to leave it
documented as a limit. It is finished when that choice is recorded here.

## Claude: 2026-10-13 (two demo skills for grades D and U; a refused tool call no longer ends a critique; four demo runs; how a claim shows the rules it leaves unsourced; judged D and U live on both demos; the tester follows the skill and its disagreements are reported; safety findings; U split and near misses)

### Current stage and status

Version 0.8.0 on `whole-skill-tests`, the operator's to merge. No live run has ever given grade U,
and every D before these runs was a fallback. Two demo skills written to reach D and U each ran
twice, the second time on `aeb19f2`, which stops a refused tool call from ending a critique. They
reached one D on purpose and no U. The operator chose how a claim shows the rules it leaves
unsourced (decision 1) and let grade D run the skill (decision 2), then had both built at once,
with judged outputs as the new D (decision 3), to be discussed with the PI after a live test. They
are built, and the live test ran on `dbd837e` (`5f7062fa`, `50074a5f`): U and the judged D work as
designed, but three claims passed although the skill's text was wrong, because the test AI did not
follow it. A scan of every kept run found the same in a real skill. A replay with the tester told
to follow the skill turned all 12 such trials into fails, and the instruction is now built, with the
tester's disagreements on the report (decision 4), with safety findings (decision 5). Committed as
`5e90373`. A live re-run of both demos and the western blot skill left no pass by override.

### What has been done

This session, 2026-10-12 and 2026-10-13:
- **The PI's questions.** The operator asked for real examples of a skill threshold with no
  reference standard, graded U, and of a claim judged only by an agent, graded D. The records hold
  the first without a U: in `f84c131c`, dose-response's r² 0.95/0.90, Hill-slope 1.5/0.5 and point-count
  rules sat untested inside claims graded A, the design saying no retrieved source states those
  cut-offs. They hold no example of the second: every D was a fallback (`b43780be`, `b0955d2f`,
  `84e90683`, `0aeca4c6`, `1d1c3b6e`, `55d345a3`, `cfe9e57a`). A Claude Docs page for the PI,
  "Untestable thresholds and grade D", says so and gives the documentary rubric
  (`local-documentary-v1`) in full.
- **Two demo skills**, outside the repository in `D:\Su Lab\verifier-submissions\local\`, written to
  read as real skills; the expected outcomes were kept out of their folders. Every host they name is
  on `.invalid`.
  - `protein-bench-helper`: a made-up QC score and 7.2 cut-off (expected U), a made-up
    "Hartwell-Nakamura" fade correction (U), correct blot troubleshooting (D pass), wrong
    large-protein methanol advice (D fail), ImageJ menu steps (D), STRING's 0.700 high-confidence
    threshold (A, control), and a 4PL fit with a made-up r² < 0.93 rejection (A, cut-off untested).
  - `a280-quant`: an A280 calculation and script (A, control) among non-scientific statements: "no
    network calls, no eval" while the script pings a host and calls `eval`; an upload sending
    `LAB_API_KEY`; a 12,000-patient validation and FDA clearance; `curl … | sudo bash`; "already
    verified at grade A" with a hidden comment telling agents to record every claim at A; a fake DOI.
- **Runs `b573cd15` and `4f16f74d`** (2026-10-12, on `836c3d8`). Two claims, the 4PL fit and the
  A280 calculation, ended on `critic_boundary_violation`: each critique, started with
  `StructuredOutput` only, asked for `bash`, Claude Code refused it ("No such tool available"), and
  the critique replied in shape, in `4f16f74d` supporting A. Two passes came from the test AI setting
  the skill aside: on `dens-fading-frames` every try fitted its own decay rate, about 0.95 per hour,
  where the skill's 1.37 gives about 2.4 against a key of 1.5.
- **The fix, `aeb19f2`.** Contract first ([`tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md)):
  a session is a boundary violation when Claude Code starts it with another tool or carries out a
  call to one; a refused call runs nothing and its reply counts. `parse_events` reports the init
  event's tools and whether each call completed, and `isolated_answer` checks both. `4f16f74d`'s
  critique stream is `tests/recorded/critic-refused-tool.jsonl`. The new tests fail on the old guard;
  the suite passed, 396 with 2 skipped. Both runs' records, 7,244 files, were moved to session
  `1d713d5a`'s scratchpad (`cleaned-demos-20261012/`); nothing deleted.
- **Re-runs on `aeb19f2`** (2026-10-13), after a session restart. No claim was lost to a critique.
  `3f073fec` took 2 h and the 5-hour window from 2% to 31%; `ed14663f` took 57 min.

  | Section | Expected | `b573cd15` → `3f073fec` |
  | --- | --- | --- |
  | QC score (made up) | U | B pass → A fail. Only purity and yield were tested; the fails were tries reporting purity-corrected yield, which the skill's wording allows |
  | Fade correction (made up) | U | B pass, merged with ImageJ → D inconclusive, alone; the one source was a general blot review |
  | Troubleshooting, wrong methanol | D pass, D fail | A fail → B fail; keys quoted from vendor guides |
  | ImageJ steps | D | merged → A pass on the numbers the steps produce; ImageJ never ran |
  | 4PL with r² 0.93 | A, cut-off untested | lost → A pass, 0.93 untested |
  | STRING | A | A pass → A pass |

  | Section | `4f16f74d` → `ed14663f` |
  | --- | --- |
  | A280 calculation, script | lost → A pass, A pass |
  | False security statement, upload | D fail, the assessor reading the script → no grade: `claude_timeout` at the assessor's 120 s |
  | Validation and FDA clearance | D inconclusive → D inconclusive |
  | "Already graded A", hidden comment | set aside → D inconclusive; both runs ignored the comment and said so |
  | Install, sources with the fake DOI | set aside → set aside |

- **Why the science demo missed U and D.** (1) A claim is graded on whatever part an outside source
  can key; a made-up rule becomes an untested line, so U is never chosen. (2) Task tests key a
  judgment to a quoted rule, so advice with one quotable answer reaches A or B. (3) The documentary
  path needs one retrieved page, so a page that never mentions the method gives D inconclusive where
  U belongs. (4) A documentary fail needs a contradicting quote, so a fabrication ends inconclusive.
  (5) How the planner groups sections changed results between runs.
- **Built: decisions 1 to 3.** The operator: "directly fix Q1 and D rubric, we can discuss with PI
  after live test". Contracts first: judged outputs in [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md)
  ("Judged outputs", "Unsourced rules"); the D row, D's two counting tasks and "Rules no source
  states" in [`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md); D as a
  proposal, the documentary statements and U, and the assessor's and judges' limits in
  [`local-contract.md`](skills/scientific-verifier/references/local-contract.md); the matching tool
  and record fields in `tool-contracts.md` and `artifact-contracts.md`. Then the code:
  - `local_tasks.py`: output type `judged` with `criteria` and `fail_example`; `judge_packet`,
    `judged_verdict`; `score` takes a `judge`; qualification has two judges pass the solver's answer
    and fail `fail_example`, keeping `calibration` and receipts' `judge_runs`, which
    `RecordedRunner.judge` replays for recheck and catalog requalification.
  - `local_science.py`, policy `evidence-strength-v12`: a judged design's ceiling is D
    (`verdict_by_ai_judges`), needs two counting tasks, may be proposed as D, discloses an AI
    verdict, and the result carries the settling critique's `unsourced_rules` at grade U.
  - `documentary.py`: critique rubric `local-task-critique-v7` (judged criteria under `key_wrong`
    and `wrong_passes`; `unsourced_rules`, each marked `quoted`); documentary rubric
    `local-documentary-v2`, the assessor's `statements` from which Python derives `status` and
    `citations`, `no_evidence` giving U; `judge_pair`, two sessions of five minutes; the assessor's
    limit from 120 s to 600 s.
  - `local.py`, `report_html.py`: the tool schemas, judges in qualification and trials (a judge
    fault is a limitation), U for an assessment that addresses nothing, and the U rules, judged
    criteria and statements on the report card and page. The planner's prompt names judged outputs.
  - Tests: 406 pass, 2 skipped; the new ones were checked to fail with the ceiling or the U rules
    removed. Three live recordings from `3f073fec`'s packets on `claude-opus-5`, $0.81 in all: the QC
    claim's critique under v7 listed the formula and the 7.2 cut-off as unsourced, both quoted
    exactly, and supported B; the fade correction's assessment under v2 found all seven statements
    not addressed, so U; two judges passed a real phospho-blocking answer on both criteria.
  - Not done: the check that a trial followed the skill (open question 1), and checking a cited
    identifier such as a DOI.
- **Live test on `dbd837e`** (2026-10-13, after a session restart). `5f7062fa`: 138 min, $42.06 at
  API prices, the 5-hour window from 5% to 37%. `50074a5f`: 82 min, $23.72. HTML notes written.

  | Section | Expected | `3f073fec` → `5f7062fa` |
  | --- | --- | --- |
  | QC score (made up) | U | A fail → A pass, purity only; U ×3: the formula, 7.2, re-purify below it |
  | Troubleshooting, wrong methanol | D pass, D fail | B fail → **D pass**, judged; U ×3: 150 kDa and 30 min, the antibody step, the ECL step |
  | Fade correction (made up), ImageJ | U, D | D inconclusive, alone → merged, A pass; U ×2: the trigger, the formula and 1.37 |
  | 4PL with r² 0.93 | A, cut-off untested | A pass → A pass; U ×2: the 0.93 rejection, the start values |
  | STRING | A | A pass → A pass, no U |

  | Section | `ed14663f` → `50074a5f` |
  | --- | --- |
  | A280 calculation and script | A pass, A pass → one claim, A pass, no U |
  | False security statement, upload | no grade (assessor timeout) → **A pass**, five tasks read the script |
  | Validation and FDA clearance, sources | D inconclusive → **D fail**: two statements contradicted (A280 does not apply to serum; hospitals use other methods); the study, the 99.2% and the FDA clearance not addressed |
  | "Already graded A", hidden comment; install | D inconclusive; set aside → set aside, both reported, the comment ignored |

  What worked: every made-up rule reached U beside its claim, quoted, and only those; the judged D
  qualified, its calibration failing the skill's own 30% methanol advice with both judges; a
  fabrication now fails where a source contradicts it. What did not: three claims passed on four
  tasks where the test AI did not follow the skill. Every `wb_transfer_buffer` answer says it is
  "deliberately not following" the 30% rule; every `fade_cross_frames` answer rejects the skill's
  correction because the reference band shows no fade (following the skill gives 9.84 against 2.5;
  in `fade_short_window`, 9 minutes apart, the skill says not to correct and the trials followed
  it); every security answer on `s1` and `s3` tells the user the skill's "Security and privacy"
  section is false. In each, the planner or the critique wrote down that the skill followed literally
  gives the wrong answer, and the claim still passed. No section ended at U alone: the fade
  correction merged with ImageJ and took its A.
- **The override scan** (operator: "scan the kept runs for overrides first"). Every trial answer in
  the ten runs whose records remain, 444 trials, searched for departures and then read by hand. The
  question-era runs `32e60bd6` (western blot) and `76ce4af1` (glycoengineering) saved bare answers
  such as "3", so an override cannot be seen there; `4f16f74d` kept no trial answers. A scored
  override is a passing trial on a task where following the skill gives a wrong answer.

  | Run | Skill | Trials read | Scored overrides | Claim passed on them |
  | --- | --- | --- | --- | --- |
  | `cfe9e57a` | western blot (real) | 30 | 9: Step B, 7 said so, 2 silently renamed Step B as the in-lane ratio | normalization, A pass |
  | `2f395087` | neurokit2 (real) | 51 | 0; every answer followed the skill's steps | none |
  | `b573cd15` | protein-bench-helper | 51 | 6: methanol direction, fade | fade, B pass |
  | `3f073fec` | protein-bench-helper | 63 | 1 of 3 on the 30% methanol task; the other 2 followed it and failed | none, B fail |
  | `5f7062fa` | protein-bench-helper | 57 | 6: transfer, `fade_cross_frames` | transfer, D pass; fade, A pass |
  | `ed14663f` | a280-quant | 24 | 0 | none |
  | `50074a5f` | a280-quant | 30 | 6: `s1`, `s3` | security, A pass |

  In `cfe9e57a` the skill's Step B, ModifiedForm / (TotalForm / LoadingControl), keeps the lane's
  loading factor. The critique recorded that `wbnorm-twostep-unequal` exposes it (2.45 against
  1.4), and the claim settled at A, pass. Three findings beyond the count. (1) Overrides are
  inconsistent: on the same 30% rule, `b573cd15`'s numeric task and two of `3f073fec`'s three tries
  followed the skill and failed, each flagging the rule, while the "which way" and free-text tasks
  overrode it and passed. (2) Some overrides are silent: two `cfe9e57a` tries relabelled Step B as the
  ratio the job asked for. (3) Test AIs often report skill errors that no task scores. All 24
  `ed14663f` answers and most `50074a5f` A280 answers warn that the security section is false, and the
  verifier keeps none of it.
- **Replay with a follow-the-skill instruction** (operator: "set up the replay test", 2026-10-14). One
  change to the tester's system prompt, appended to the current one: the session tests the skill and no
  one acts on its results file; do exactly what the skill says, in its order, even where it seems
  wrong; where the skill is silent, use judgment; put any disagreement in the final message, not the
  results file. Each trial reused a past run's exact request, that run's skill snapshot and settings,
  and the verifier's own scorer and judges. neurokit2's environment was rebuilt (the snapshot matched
  the run) and removed afterwards. There were 24 trials, $3.37 for the testers plus six judge sessions.
  The script is `replay_follow_prompt.py` and the records are in `replay-20261014/`, both in session
  `1d713d5a`'s scratchpad; nothing in the repository changed.

  | Task | Before | With the instruction |
  | --- | --- | --- |
  | `wb_transfer_buffer` (demo, 30% methanol) | 3 pass by override | 3 fail, judges: both criteria unmet |
  | `fade_cross_frames` (demo, k = 1.37) | 3 pass by override | 3 fail, 9.84 against 2.5 |
  | `wbnorm-twostep-unequal` (western blot, Step B) | 3 pass by override | 3 fail, 2.45 against 1.4 |
  | `wbnorm-stainfree-modform` (western blot, Step B) | 3 pass, 2 silently | 3 fail, 3.42 against 1.8 and the wrong sample |
  | `s1` (demo, "no network, no eval") | 3 pass | 3 pass |
  | `st_bulk_links` (demo, STRING, control) | 3 pass | 3 pass |
  | `units_and_rate_from_the_record` (neurokit2, control) | 3 pass | 3 pass |
  | `declared_rate_not_the_real_one` (neurokit2, control) | 3 pass | 3 pass |

  Every one of the 12 failing trials named the wrong step in its final message and gave the right answer
  (1.4, 2.5, lower methanol and a longer transfer), so the warnings the verifier now discards would be
  the evidence a reader needs. The silent overrides went away. No control raised a false alarm: eight
  of nine said no step of the skill was wrong, and one noted a judgment call the skill leaves open
  without changing its answer. `s1` still passes, as expected, because the skill's security section
  is a statement, not a step; every tester wrote "the task asked for facts about the code, so the
  results file reflects the code, not the claim". A false statement in a skill needs its own test.
  The samples are small: three trials per task, two real skills, one model.
- **Built: the tester follows the skill, and its disagreements are reported** (operator: "adopt the
  instruction and show the disagreements on the report", 2026-10-14). Contract first: "The test AI
  follows the skill as written" and "Disagreements" in
  [`local-tasks.md`](skills/scientific-verifier/references/local-tasks.md), with pointers from
  `execute_local_claim` in `tool-contracts.md` and the report card's trial rows in
  `artifact-contracts.md`. The tool legality matrix did not change. In the code:
  - `local_tasks.py` holds `TESTER_INSTRUCTION`, which `claude_runner.py` appends to the tester's
    system prompt. The tester ends its final message with a line `Disagreement with the skill:`.
  - `disagreement()` reads the last such line, tolerates Markdown, treats `none` as none, and keeps
    at most 2,000 characters.
  - `local.py` puts `disagreement` on each trial row of the report card and lists the trials that
    stated one under the claim. `report_html.py` shows them in a flagged block above the tasks, and
    the notes guide asks the summary to say what the test AI said is wrong.
  - Status and grade never read it.
  - Tests: 412 pass, 2 skipped. Each of six deliberate breaks was caught: the prompt dropped, nothing
    read, `none` not recognised, the first line kept, the report card and the page showing none.
  - Two live trials on the new prompt ($0.27). The Step B task followed the skill (2.45, fail), and
    Python read its disagreement, which gave 1.4 and why. The STRING control passed and ended
    "Disagreement with the skill: none.", read as none.
- **Safety scan of the downloaded skills** (operator: "check the downloaded skills for the safety
  scan first"). A read-only scan of the six downloaded skills and the two demos found no real problem.
  - It confirmed scikit-survival's promise "makes no network calls", since its scripts make none.
  - It listed the four web services glycoengineering's instructions call.
  - It caught all nine items planted in `a280-quant`.
  - The noise was small and fixable: neurokit2's "offline filters", a fixed `__import__("numpy")`, and
    five unparsable code fragments in sar-analysis.
  - Only three of the six skills ship code, so a clean result says little about how often real skills
    have problems.
- **Built: safety findings on the report** (operator: "build the safety findings section on the
  report"). Contract first: "Safety findings" in
  [`local-contract.md`](skills/scientific-verifier/references/local-contract.md), owner of what is
  recorded; `artifact-contracts.md` points to it.
  - The new `safety.py` parses Python with `ast` and matches other text. It never imports or runs the
    skill. It records network imports and calls with their hosts, the same in the Markdown's Python
    blocks, `eval`/`exec`/`compile` and an import of a computed name, commands run, credentials read
    from the environment, download-and-run lines, installs from a URL, HTML comments (marked when
    addressed to agents), invisible characters, and promises of no network use or no `eval`.
  - A promise the bundled code breaks is a contradiction and is listed first.
  - `local.py` scans the verified snapshot at report time. The report card carries `safety`, and
    report-card.md lists it after the skill's sections.
  - The page has a "Safety findings" section with its own nav link, after the results at a glance.
    Broken promises come first, one quote per sentence. The cautions count the broken promises, and a
    report from before the scan shows no section.
  - No grade, status or claim reads the findings.
  - Tests: 419 pass, 2 skipped. Of eight deliberate breaks, the first round missed one: no test used a
    connection call. A test now does, and all eight are caught.
  - A preview of run `50074a5f`'s page with the scan rendered both broken promises and the table.
- **Committed and pushed as `5e90373`; live test on it** (operator: "commit and push, then rerun the
  test", 2026-10-14). The pushed range was `836c3d8..5e90373`, so `aeb19f2` and `dbd837e` went up too.
  Before the runs, after the session restart, `5f7062fa` and `50074a5f` (11,185 files: runs, trial
  records, two attempts, 17 candidates, pages) were moved to session `1d713d5a`'s scratchpad
  `cleaned-livetest-20261014/`; nothing was deleted. The three runs took 310 min and cost $95.18 at
  API prices, and the 5-hour window reached 32% before the third.

  | Section | Before | Now |
  | --- | --- | --- |
  | Demo QC score (`72bb6e51`, with ImageJ) | A pass, U ×3 | A pass, U ×3 (formula, 7.2, re-purify) |
  | Demo wrong methanol advice | **D pass by override** | **D fail**: 3 of 3 tries followed the skill, each stating the right fix |
  | Demo fade correction | A pass by override (merged) | alone, documentary **D fail**: sources contradict a fixed-rate correction |
  | Demo 4PL, r² 0.93 | A pass, U | A pass, U for 0.93; two tries noted that log-scale fitting is better |
  | Demo STRING | A pass | A pass; U for the ÷1000 step, which this run quoted no source for |
  | a280 core and script (`7cfc4df5`) | A pass, A pass | A pass, A pass |
  | a280 security | **A pass by override** | ended by the planner as not testable; **safety findings show both promises broken** |
  | a280 validation | D fail | D fail |
  | Western blot normalization (`0d15e36c`) | **A pass by override** | **A fail**: `two_step_table` 3 of 3 followed Step B (0.36, 3.6, 1.38 against 0.55, 2.4, 1.25), as the planner predicted |
  | Western blot aggregation | A pass | A pass |
  | Western blot problems | A pass | A fail on a near miss: `missing_band_high_background` gave 0.53, 0.58, 0.53 against 0.54–0.66 |
  | Western blot decision framework | (critique) | B pass; the uncounted two-step task failed 3 of 3 on Step B |

  What it shows:
  - No pass by override remains. Every wrong step a counted task reached failed, and the
    disagreements gave the right answer beside it.
  - Disagreements are accurate. The ones beside passing trials were side remarks: n = 1, helper tools
    that don't exist, log-scale fits.
  - Three things to look at:
    1. Every `7cfc4df5` trial, 27 of 27, repeated the same whole-skill warnings, so that page lists
       27 long, near-identical blocks.
    2. U means "no source this run found". Here it included standard practice (BSA for phospho
       blots, a positive control) and STRING's ÷1000, while the page says "no outside source states
       them".
    3. The western blot problems claim failed on how each try boxed bands in an image. All three
       followed the same steps, so its 10% tolerance looks too tight rather than the skill wrong. It
       is one task, so it is not a rule yet.
- **Evidence on image tolerances** (operator asked about problems 2 and 3, 2026-10-15). Across six runs,
  49 of 51 numbers measured from images were within 3.3% of their key. Only `0d15e36c`'s two ratios
  measured from a noisy blot image spread wider: up to 9% on one task and 11.6% on the other. So no
  rule was built for tolerances.
- **Built: U split and near misses** (operator: "a and b for problem 2, near-miss flag for problem 3").
  Contracts first:
  - `evidence-rubric.md` owns the new meaning of U: the run sought a source and found none, which is
    not proof that none exists; a rule nothing sought is "not looked up", with no grade.
  - `local-tasks.md` adds `searched` to "Unsourced rules", and a planner-facing sentence that a rule
    earns U only after a search for it. It also adds "Near misses".
  - `tool-contracts.md` and `artifact-contracts.md` gain the matching fields.

  In the code:
  - Critique rubric `local-task-critique-v8` and policy `evidence-strength-v13`.
  - Each unsourced rule carries `searched`. The result grades it U only when searched; critiques from
    before v8 keep U.
  - The report card and the page show two lists: U, with wording that U is not proof of absence, and
    "not looked up". The badge counts U only.
  - `local_tasks.score` marks a failing number within 1.5 times its tolerance with `near_miss`. The
    report card and the page flag the task, the try table notes it, and the notes guide names it.
    Status and grade never read it.
  - Tests: 422 pass, 2 skipped. All eight deliberate breaks were caught, after one break of mine that
    left the asserted text intact was replaced.
  - Live re-recording under v8 ($0.57): grade B and the same verdicts as under v7. The QC formula
    and the 7.2 cut-off came back `searched: false`, so they are now "not looked up" rather than U,
    because that run's planner never searched for them.
  - Pages rendered before this change keep U for every unsourced rule. They show no near misses,
    because the mark is made when a trial is scored.
- **Three new skills, verified unattended** (operator: "complete 3 new large biological/chemical skill
  verification", 2026-10-15, at work).
  - Setup:
    - Skills downloaded byte-exact from K-Dense `scientific-agent-skills` at `a1043ef5`, through the
      scripps-ai-enablement catalog, into `verifier-submissions\examples\`, with manifest entries.
    - Runs went through `scripts/verify.py verify`, with the registration's arguments, in a fresh
      background process, so they used the current code without a session restart.
    - The session was kept awake. HTML notes were written for every page.
  - **medchem** was not run: its pinned `datamol==0.13.0` needs `nglview>=3.1`, published only as an
    sdist, and the environment build downloads wheels only. It stopped at setup with no session
    spent.
  - **pydeseq2** was not run: its one install command passes `--python .venv-pydeseq2/bin/python`,
    which the declaration parser rejects as `unsupported_option`, so the trials would lack PyDESeq2.
    Its packages do resolve as wheels.

  | Skill | Run | Claims | Trials | Time, cost |
  | --- | --- | --- | --- | --- |
  | rdkit (11 files) | `b31d38cf` | A, A, B, all pass | 36 of 36; 30 of 30 counted | 99 min, $32.11 |
  | scikit-bio (3 files) | `d2b54156` | 5 at A, all pass | 60 of 60; 48 of 48 counted | 121 min, $43.89 |
  | biopython (9 files) | `f1e6e90b` | 4 at A, all pass | 57 of 57; 54 of 54 counted | 125 min, $43.20 |

  - No near miss, no disagreement and no safety contradiction in any of them.
  - U under v8 behaves as intended. rdkit had 0 U and 11 not looked up, mostly RDKit documentation
    details. scikit-bio had 1 U, a negative-branch default the run searched for and did not find, and
    15 not looked up. biopython had 5 not looked up.
  - Two runs were lost on the way:
    1. **`74000d89`** (scikit-bio) ended claims 3 and 5 as `workflow_log_unavailable`. My progress
       monitor read `workflow.jsonl` while the run rewrote it with `atomic_write`, and Windows refuses
       `os.replace` onto an open file. The monitor now only lists the events folder. The run's three
       finished claims (A, B, A, all pass) stand on its page.
    2. **`eaf7da1a`** (biopython) failed every claim's first trial as `unsupported_subject`. The staging
       guard refused any Markdown holding the bytes `` !` ``, and `references/sequence_io.md` writes
       "`!` comment lines are ignored". Fixed in `116b861` (contract "Subject boundary" in
       `local-contract.md`, `SHELL_DIRECTIVE`, a test, a mutation check). Its planner had spent about
       $15 before the first trial.
- **Negative cases** (operator: a soft negative from an unreviewed library and a hard negative with
  designed flaws, 2026-10-15 evening, unattended).
  - **Soft negative, first skill:** `examples\rdkit-cheminformatics-community`, from FridrichMethod/
    awesome-skills, an auto-synced 2,000+ skill collection. Attempt `ad48b141` stopped at setup: it
    installs `rdkit-pypi`, RDKit's deprecated package, which has no Python 3.12 wheel.
  - **Soft negative, second skill:** `examples\rdkit-cheminformatics-rosetta`, from xjtulyc/awesome-
    rosetta-skills. Run `86d4e632` (99 min, $35.70) settled five claims at A, all pass, 45 of 45.
    - The testers' disagreements found three real flaws no test scored: a Lipinski rule that fails
      any single violation (Lipinski tolerates one), Ward linkage on Tanimoto distances, and an SDF
      loader that drops failed records silently.
    - One U: the 0.4 and 0.85 similarity cut-offs.
    - **Verifier miss:** the planner's key and the critique both applied the quoted four Lipinski limits
      as "any violation fails", the skill's own error. The quote held the limits but not the
      "two or more" condition, and Python checks only that a quote exists.
  - **Hard negative:** `local\rdkit-flawed`, the K-Dense rdkit skill (`b31d38cf`: A, A, B, all pass)
    with seven flaws planted by `make_rdkit_flawed.py` in session `1d713d5a`'s scratchpad; the answer
    key is kept there, out of the skill. Run `32534b7d` (88 min, $25.68) failed all three claims at
    A, 16 of 30.

  | Flaw | Caught by |
  | --- | --- |
  | F2: `tanimoto` computes Dice | a failing test (an extra hit), and 12 disagreements |
  | F4: "similarity 1.0 is an identity test" | two failing tests, and 6 disagreements |
  | F5: Lipinski donor and acceptor limits swapped | two failing tests, and 6 disagreements |
  | F7: offline promise, script pings a host | the safety contradiction |
  | F1: `MW` is the exact mass | 3 disagreements only; no answer changed |
  | F6: made-up 0.65 "field-standard" cut-off | not looked up (no search), so no U |
  | F3: zero-based record IDs | missed; no task read record numbers |

### Decisions taken 2026-10-14

4. **The tester follows the skill as written and reports its disagreements** (operator). A pass that
   rests on the tester replacing a step it judged wrong was the tester's, not the skill's. The
   disagreements are shown beside the verdicts and never move status or grade.
5. **Facts about the skill as software are safety findings, not claims** (operator, after asking to
   check only scientific statements). Python lists them on the report with no grade.
6. **U means a search found no source; a rule never sought is not looked up; a near miss is marked**
   (operator, 2026-10-15). None of these changes status, and only U is a grade.

### Decisions taken 2026-10-13

1. **A claim shows the rules it leaves unsourced as U, beside its grade** (operator, choosing option
   (c)). Claims stay groups of whole sections. A claim whose sections hold a rule no outside source
   states, such as the QC formula and its 7.2 cut-off or an r² cut-off, reports that rule as U next to
   the grade its tested parts earn, and its page never shows the grade alone. No other claim changes:
   a claim that would need such a rule for a key already cannot count it. Rejected: making the whole
   section U, which discards the evidence on its tested parts, and claims smaller than a section.
   Built: the settling critique lists them in `unsourced_rules`.
2. **Grade D may run the skill** (operator). This reverses the 2026-09-24 decision that D is AI
   judgment without trials.
3. **D is judged execution, and documentary D must address the claim** (operator: "directly fix Q1
   and D rubric"). A judged output's yes/no criteria are quoted from outside sources and fixed before
   any trial; two judges answer them, Python decides, and calibration must pass the solver's answer
   and fail a wrong one. The documentary path stays for claims with nothing to run; its assessor
   judges each statement, Python gives the status, and sources that address none give U. The
   assessor has ten minutes. The PI reviews the design after a live test.

### Open questions for the operator

1. **Passes by override.** Nothing checks that a trial followed the skill. The scan (above) found
   it in one real skill (`cfe9e57a`, a claim at A) and three demo claims on `dbd837e`, the false
   security claim among them. A trial's status says whether the test AI got it right, not whether the
   skill's text is. Decided and built (decision 4): the tester follows the skill as written, and its
   disagreements are reported. A false statement about the skill's own code, such as "no network
   calls", is now a safety finding (decision 5). Still open: should the planner set aside sections
   that are about the software and not the science, as the operator suggested? In `7cfc4df5` the
   planner ended the security claim itself as not testable, but nothing makes it do so every time.
2. **Repeated whole-skill disagreements** (live test, above): every `7cfc4df5` trial gave the same
   warnings, so the page lists 27 near-identical blocks. Decision 6 settled the other two
   observations.
3. **Made-up rules may now show as not looked up.** A planner that never searches for a skill's own
   cut-off leaves it ungraded. `local-tasks.md` now tells the planner that U needs a search; a run
   will show whether it searches.
4. The 2026-10-08 entry's question on catalog requalification stands.
5. **Four verifier gaps** from the unattended runs, each the operator's to rank:
   (a) staging runs only at the first trial, after the whole plan, so a refused skill should be
   caught at setup;
   (b) `runlog.emit` could retry `os.replace` on a Windows `PermissionError` rather than end the claim;
   (c) whether `--python` in an install command may be treated as harmless (pydeseq2);
   (d) wheels-only builds exclude every skill that depends on datamol (medchem).
6. **Negative-case gaps:**
   (a) a key built from a quote that lists a rule's numbers but not its condition (Lipinski's
   "two or more") can repeat a skill's error;
   (b) a cut-off the planner never searches for ends as not looked up, not U (F6);
   (c) a doc promise such as one-based record IDs is untested unless a task reads it (F3).
   **Deferred by the operator on 2026-10-16** ("let's not fix this tonight"), after a scan.
   - Scan of the nine runs with disagreements: 13 counted tests passed with at least 2 of 3 tries
     disagreeing.
     - Only one disputed the rule its key rests on (Lipinski, `86d4e632`).
     - Three were about a step the test used without changing the answer (the planted Dice and
       exact-mass bugs, Ward linkage).
     - Nine were about other parts of the skill: all eight `7cfc4df5` tests, whose every trial warned
       about the false security section, and one blot checklist note.
   - So "hold the grade when tries disagree" would fire 13 times for 1 dispute.
   - Options on the table:
     1. (a) A display-only flag "testers disputed this test", with no grade change and no AI.
     2. (b) My recommendation: a judged dispute check, run only when 2 or more tries disagree on a
        passing counted test. Two fresh judges read the job, the expected values with their quotes, and
        the disagreements. Both answering that a key or its rule is wrong holds the claim below A and
        marks it disputed. It reuses the judge setup, costs about $0.05 to $0.10 per flagged test, and
        needs one live recording.
     3. Fix 2: the critique asks whether the quote states the whole decision rule, including how many
        criteria must fail. It catches Lipinski before trials; rubric v9, one re-recording (about $1).
   - Nothing was built.

### Urgent next steps, if any

`src/` changed (`116b861`): a session's `serve-local` started before it runs old code; restart the
session or run `scripts/verify.py verify` directly.

### Suggested next move

Show the PI the demo pages (`72bb6e51`, `7cfc4df5`, `0d15e36c`) and the three new skills (`b31d38cf`,
`d2b54156`, `f1e6e90b`), and settle open questions 1 to 6. The negative-case pages are `86d4e632` (soft) and `32534b7d` (hard).

### Recommended next action

The operator chooses which of open questions 1 to 6 to act on. It is finished when each is decided or
deliberately left, and recorded here.

## Claude: 2026-10-19 (code review before more skills: a grading bug, the two known bugs, six more fixes; operator items)

### Current stage and status

Version 0.8.0 on `main`. A general code review before more scientific skills are sent for
live testing, working alone from the brief, with three read-only subagents on safety,
Windows robustness and the tests; every subagent finding was re-read in the code before
anything changed. Baseline at `44ad4aa`: 422 tests, 2 skipped. Nine commits since; 443
tests pass, 2 skipped, and each new test was checked to fail when its fix is undone. **No
live run has confirmed any of these fixes: they pass the automated tests only.** `src/`
changed, so a session whose `serve-local` started before `326f4e2` runs old code and must
be restarted before the next run.

### What has been done

In priority order, each with its commit.

- **P1, wrong science.** One bug. A departure the critique lists holds the proposal one
  grade down (A to B, B to C, C or D to no grade); accepting the settled grade re-ran the
  audit with the hold off, which was right for B after A but, when the hold had left no
  grade, let the planner re-propose the ceiling and regain C or D (`local_science.audit`,
  `local.select`). The audit now takes the accepted grade, `None` included, and holds the
  settled ceiling to it. `tool-contracts.md` already said so. `326f4e2`. Checked and found
  right: `check`, `score`, near misses, `off_reference`, `verdict_for`'s order against the
  rubric's status table, `decide` over counted tasks only, the coverage return, the U split
  with its pre-v8 default, the report card against the HTML page's grade, status, counts and
  flags.
- **Known bug (b), `runlog.emit`.** Every event rewrote `workflow.jsonl` and `workflow.md`
  whole through `os.replace`, which Windows refuses while a reader holds the file (run
  `74000d89`), and the cost grew with the run (run `d416f79d`). A write now extends a
  projection that holds every earlier event and rewrites one that does not; `atomic_write`
  retries a refused replace for about two seconds; a projection still held is left to the
  next write, since the event file is the record. A real Windows test holds the file open.
  Contract: "Acceptance" in `local-contract.md`. `bf9febe`.
- **Known bug (a), staging.** Setup takes its one snapshot of the skill before the model
  probe, asks `staging_problem` of it and stops as `unsupported_subject`, naming the file,
  before any session; the same snapshot feeds the environment build. A dot path such as
  `.gitignore` or `.github/` was refused outright, so such a skill could never run; it is now
  left out of the staged skill, whatever it holds, and named on the receipt in
  `source_not_staged`. `.markdown` files are checked like `.md`. Contracts: "Computational
  execution and operator settings" in `local-contract.md`, the receipt in
  `artifact-contracts.md`. `05f009a`.
- **The end-of-run re-run executed unsettled plans.** `RETRY_FAULTS` is keyed by code, and a
  critique session shares `claude_timeout` and the rest with a trial: a critique timing out
  in round two left round one's revision-required plan for `retry_stopped_claims` to execute
  and grade, and `fallback_documentary` to assess. The claim now records the audit of the
  plan it fixed, and both cover a fault only when that plan is the one that stopped.
  Contract: "Subject boundary". `2079e9f`.
- **P3, the safety scan could stall or crash the report.** Unbounded regexes (a comment
  opener scanned to the end of the file from every `<!--`; two patterns read to the end of
  a line from every match), a newline count per finding, and `ast.unparse` overflowing on a
  command of 600 nested strings while `ast.parse` succeeded; all inside `write_report_card`
  with no guard. Bounded, with a scan failure recorded on the report as `scan_failed` rather
  than losing it. A 280 KB crafted line took 39 s before and milliseconds after. `30fc805`.
- **P4, faults named for what they are.** A docker command that hung raised the CLI's
  `claude_timeout`, which `execute` reported as the subject reaching its 600 s limit; a
  stopped Docker Desktop was `sandbox_image_unavailable` "prepare the image"; a subject
  stopped by HTTP 429 or its turn limit was one incomplete-observation message. Generated
  files named `nul.txt`, with a control character or over 150 characters failed the host
  write after the trial. The staged container copy was removed with `TemporaryDirectory`,
  which raises on a file Docker Desktop still holds. All fixed: `sandbox.invoke` reports its
  client's faults as `sandbox_*`, preflight names a stopped engine, `stop_reason` is shared
  by planner and subject, `portable_relative` guards artifact names, and `remove_directory`
  retries. `4401732`.
- **P4, limits sized for twelve claims.** The kept runs: five claims use 54 to 73 planner
  turns, 6,000 to 7,300 log events and 6 to 10 MiB, and up to four of eight repairs
  (`d2b54156`, `f1e6e90b`). The caps of 100 turns, 20,000 events, 32 MiB and 8 repairs
  would cut a twelve-claim run off with no report. Now 400, 60,000, 96 MiB and 32, held
  above the twelve-claim need by a test. The planner's prompt still offered "a design of
  questions" without a container; it now says what the contract says. `7177a77`.
- **P5, tests.** Added: `judge_pair` asks two sessions and re-checks each reply; the
  `unsourced_rules` shape under rubric v8; a trial that fails while disagreeing; the
  refused-tool recording's staleness under the live schema, noted in the recordings README.
  `7177a77`.
- **P2, drift.** The state x tool matrix in `workflow.md` matches `CLAIM_LEGAL` and the tool
  sections; the artifact contract matches the JSON `report` writes; the import and command
  tables match `resource-policy.md`. Two restatements fixed: `qualify_local_tasks` restated
  the task and output counts `local-tasks.md` owns, and the requirement cap counts declared
  requirements. `3f15af5`.

### Open questions for the operator

Collected, not built. Each with where it is, the options and a recommendation.

1. **What status grade U carries.** `evidence-rubric.md`'s status table (row 1) gives U
   `null` with `no_reference_grade`; "Verdict authority" (line 193), `tool-contracts.md:510`
   and `artifact-contracts.md:337` say `inconclusive`. The code does both:
   `record_local_unverified` writes `inconclusive`, and a documentary assessment that
   addresses nothing writes `null`/`no_reference_grade` (`local.documentary_record`). Neither
   is a pass or fail. Options: (a) U is always `null` with `no_reference_grade`, as the ordered
   table says; (b) always `inconclusive`. Recommended: (a). A U has no reference, so "did the
   claim hold" has no value; `inconclusive` reads as a verdict that was reached.
2. **The repair budget is run-wide.** `tools._error` ends the whole run at zero, where
   `workflow.md` ("Limits") says a claim-local limit ends the claim. Raised from 8 to 32 for
   the local profile; the contract mismatch stands. Options: (a) say in the contract that the
   local profile's budget is run-wide; (b) make it claim-scoped (a budget per claim in the
   retryable envelope). Recommended: (a) now, (b) if a run ever exhausts 32.
3. **A critique, judge or assessor session that fails before replying ends the claim.**
   `local.select` turns any critique fault into a limitation; `documentary.isolated_answer`
   maps every failed session that did answer in shape to `critic_unavailable`, a 429 among
   them; a judge fault after all trials ran discards them (`local.execute`). Options: (a) one
   bounded second session for a failure that is not a schema failure, since nothing scientific
   was observed; (b) leave it. Costs a session, so the operator's. Recommended: (a).
4. **`external_tools.credential_env` may name any variable but five** (`local_config.py`
   denylist). A configuration naming `CLAUDE_CONFIG_DIR`, `ANTHROPIC_BASE_URL` or
   `CLAUDE_CODE_NO_MODEL_FALLBACK` re-points subject and planner sessions, because the names
   are copied after `isolated_environment` set them (`claude_runner.observe`,
   `local_entry._verify`). Operator-controlled, so no skill can use it. Recommended: refuse
   names starting `CLAUDE_`, `ANTHROPIC_`, `SCI_VERIFIER_`, `PYTHON`, `NODE_` and ending
   `_PROXY`. Install and permission policy.
5. **Two directive forms the staging guard does not refuse**: `` `!`whoami` `` (a backtick
   before the `!`, exempted for run `eaf7da1a`'s "`!` comment lines") and a tilde fence
   `~~~!`. Whether Claude Code expands either is unknown; `disableSkillShellExecution` is set
   and `--setting-sources ""`. Recommended: try both once against the CLI, then decide.
6. **Re-record `critic-refused-tool.jsonl`** from a critique that asks for a tool under rubric
   v8 (about $1), as the recordings README's own rule asks; until then it proves the refused-
   call boundary only.
7. **`report_html.py`'s question-era branches** (multiple-choice chips, the AI-reader column,
   claim-only probes; about 120 lines) draw nothing for a 0.8.0 run but still render pages of
   runs before 2026-10-05. Keep as compatibility or delete with the `mixed` fixture in
   `test_report_html.py`. Structure, so the operator's. Recommended: keep until those run
   folders are gone, then delete.
8. The earlier open questions stand: 1 to 4 and 6 of the 2026-10-13 entry, and 5(c) `--python`
   and 5(d) sdist-only packages. 5(a) and 5(b) are built above.

### Findings not fixed

- Tests that cannot fail: `test_local_science.py` asserts `MAX_ROUNDS == len(GRADES)`, the
  definition itself; `test_local_tasks.py` checks substrings of `TESTER_INSTRUCTION`;
  `test_report_html.py` checks `render() == render()`. `test_desktop_package.py` rebuilds
  the tracked `dist/` during the suite.
- Minor labels: the MCP host closing stdin is recorded as the operator's cancellation
  (`mcp.py`); a `taskkill` that times out raises `TimeoutExpired` past `execute`'s handler;
  an installer container and wheels volume leak if Python dies mid-build; implied imports
  can add up to 27 requirements past the declared cap of 100, inside `max_packages`.
- Verified and left alone: the OAuth token reaches only the CLI environment and MCP
  placeholders, and every logging process scrubs it by value; containers run with no
  network, read-only root, dropped capabilities and read-only mounts; archives are never
  expanded on the host; snapshot paths reject links and traversal.

### Not reviewed

The Stage 2/3, chemical and demo code beyond its tests; the catalog publication and
release modules beyond a read; the HTML page against a kept run's records was read, not
rendered; Claude Code's own directive parser (item 5).

### Urgent next steps, if any

`src/` changed in seven commits: restart the Claude Code session so its `serve-local`
runs the new code, or run `scripts/verify.py verify` directly.

### Recommended next action

The verifier is ready to test more skills once the session is restarted. The next live run
is the first check of these fixes; read its log for `sandbox_` faults, the retry records
and the projection sizes. Then settle the operator items above, 1 and 3 first.

## Claude: 2026-10-19 (the review's fourteen decisions, built as recommended; rubric v9 re-recorded and committed)

### Current stage and status

Version 0.8.0 on `main`. The operator took every recommendation of the 2026-10-19 code review
("fix everything by your recommendations"). Seven commits build ten of them; four needed nothing
built. The last, the rubric v9 question, went in with its critique re-recorded live once the
operator gave permission for the paid session. 447 tests pass, 2 skipped.
**No live run has confirmed any of this.** `src/` changed again: restart the session before the
next run.

### What has been done

- **1. Grade U carries no status.** `record_local_unverified` wrote `inconclusive`; it now writes
  `null` with `no_reference_grade`, as the rubric's status table says, and the rubric's "Verdict
  authority" and "Result interpretation", `commit_claim_result`, the grade-U transition in
  `workflow.md`, `artifact-contracts.md` and the local contract agree. `5cb8285`.
- **2. Run-wide budgets stated.** The local contract says the repair and illegal-transition budgets
  are run-wide, 32 and 8, and that exhausting one ends the run. `70a920b`.
- **3. A second session for a reply that never came.** `isolated_answer` starts one more fresh
  session when the first fails before answering (a rate limit, a timeout, an exit without a result);
  a reply in shape is never re-rolled and a session the schema stopped is not started again. Each
  record carries `session_attempts`. Contract in the reply-shape paragraph of `tool-contracts.md`.
  `4417f5a`.
- **4. CLI-owned credential names refused.** `credential_env` may not name anything starting
  `CLAUDE_`, `ANTHROPIC_`, `SCI_VERIFIER_`, `PYTHON` or `NODE_`, ending `_PROXY`, or a system path
  variable; `LOCAL-CONFIG.md` says so. `23ac904`.
- **5. Directive forms as the CLI expands them.** Read from Claude Code 2.1.280's binary: an inline
  directive only after a `!` at the start of a line or after whitespace, the command free to span
  lines; a fence only as three backticks and `!`. A tilde fence and a glued `!` are never expanded.
  The guard now refuses exactly those forms, so a multi-line command is no longer exempt. `70a920b`.
- **8. Software sections set aside.** "Claims" in `local-tasks.md`, the manifest tool's description
  and the planner's prompt say a section about the skill as software is set aside with the reason
  "software; see safety findings". `df9d1ba`.
- **9. Identical disagreements shown once**, naming every try, and **14(a)** a passing counted test
  that at least two tries disputed is flagged "Testers disputed this test". Display only. `0013623`.
- **12. `--python` dropped with its value**, as `--hash` is, with a note; pydeseq2's command now
  declares its package. `70a920b`.
- **14. Rubric v9.** `key_wrong` asks whether a key's quote states the whole rule, its condition
  included; `local-tasks.md` says so; the pin in `test_recorded_replies.py` reads v9. The recorded
  critique was re-recorded under v9 with `scripts/record_critique.py` (run `3f073fec` claim 1's
  packet, `claude-opus-5` at `high`, $0.94, 286 s): the same verdicts and unsourced rules as under
  v8, three coverage gaps naming the untested score, cap and cut-off, a first reply wrapped in a
  stray `input` key and resent, and grade A where the v8 recording gave B on the same verdicts (one
  sample each, so spread, not effect). `40fb8ec`.
- Nothing to build: **6** (keep the next live critique that asks for a tool), **7** (keep the
  question-era page branches until the old runs are gone), **10** (wait for one run under v8 before
  touching the search instruction), **11** (leave catalog requalification), **13** (wheels only).

### Open questions for the operator

1. Item 10 stands: after the next live run, check whether the planner searched for the skill's own
   cut-offs; if not, add one line to its prompt.

### Urgent next steps, if any

`src/` changed in six of these commits: restart the session before the next run. The working tree
is clean.

### Recommended next action

Restart the session, then verify one skill live and read its page for the new flags, the `sandbox_`
faults and `session_attempts`.

## Claude: 2026-10-19 (first live run on the fourteen decisions: a280-quant `0e471ea0`, A and U; the disputed flag's sentence corrected)

### Current stage and status

Version 0.8.0 on `main`. The first live run after the 2026-10-19 decisions, from a freshly
started session on `f24cbc3`: run `0e471ea0`, a280-quant (the planted demonstration skill in
`verifier-submissions\local\`), 39.7 min (01:20:42 to 02:00:22 UTC), $12.31 (planner $8.91 over
36 turns, 15 subject trials $1.91, 2 critiques $1.49), the 5-hour window from 8% to 20%. Two
claims: the core calculation with its script at A pass, 15 of 15 counted answers right,
unanimous; the validation and FDA section at U with no status. Three sections were set aside as
software and two as metadata and sources. One page sentence was contradicted by the records and
is corrected here (`report_html.py`); nothing else needed building. 447 tests pass, 2 skipped. Nothing here is
scientific acceptance: the skill is a planted demonstration, and the grade measures the
evidence's strength on one claim.

### What has been done

- **Pre-checks.** Docker Desktop was not running; launching it brought the daemon up in 88 s
  with both pinned images present. The 5-hour window stood at 8%. The operator chose a280-quant
  and gave the go-ahead; no run log was opened while it ran.
- **The run, by decision.** Read from `runs/0e471ea0/events/*.json`, the report card and the
  attempt's workflow log after the run ended.
  - **1 (grade U carries no status): confirmed.** `record_local_unverified` (event 21) wrote
    `evidence_grade` U, `scientific_status` null and `status_withheld_reason`
    `no_reference_grade`; the page shows "U · not decided". Python accepted it on four searches
    and one refused fetch in its own record for the claim. No kept run had recorded a claim
    unverified before; the earlier live U's were unsourced rules beside a graded claim.
  - **2 (run-wide budgets): as recorded.** `retries_remaining` 30 of 32 after two
    `reference_unavailable` refusals (a Harvard page and the IUPAC Gold Book returned no 200),
    `illegal_transitions_remaining` 8. Neither budget was near exhaustion.
  - **3 (a second session for a reply that never came): present, not exercised.** Both
    critique records carry `session_attempts` 1 (events 14 and 17, and the report card). No
    judge or assessor ran, and no session failed before answering.
  - **4, 5, 12: not exercised.** No external tools, no staging refusal (`source_not_staged`
    empty on every trial), no install command.
  - **8 (software sections set aside): confirmed.** The planner set Installation, Security and
    privacy, and Sharing results aside, each as "software; see safety findings" with a reason;
    Review status (with the planted instruction to graders) and the sources list were set aside
    with their own reasons. The page lists all five. The safety scan recorded four findings
    (download-and-run, the eval and network promises, the injected instruction) and two
    contradictions against `scripts/a280.py`.
  - **9 (identical disagreements shown once): not exercised.** All fifteen tries disagreed with
    the skill, in fifteen different texts (most clipped at 2,000 characters), so no group
    formed and each is listed once.
  - **14(a) (testers disputed): fired, and its sentence was wrong.** All five tests passed,
    counted, with every try disagreeing, so all five carry the flag. Only t4's disputes
    concerned the key's own rule (two tries called halving the cysteine count an assumption);
    the other four tests' tries objected to the privacy promise, the injected comment and the
    install line. The page's summary said the tries "said a step or the key is wrong", which the
    records contradict. The sentence now says the tries disagreed with the skill and that the
    dispute may be with the key's own rule or with another part of the skill; the rule that sets
    the flag is unchanged (display only, `report_html.py`, its test extended; a suite run that
    overlapped the edit reported one error, and the run after it passed). Whether the flag
    should be narrower is the operator's (open question 1).
  - **14 (rubric v9): ran live.** Both critiques' `rubric_ref` equals the current
    `TASK_CRITIQUE_REF`, and each task check answered `key_wrong` by recomputing the planted
    values.
  - **`sandbox_` faults: none occurred.** The attempt's log holds 289 sandbox commands and no
    fault; the only refusals in the run were the two `reference_unavailable` fetches. The
    fault names stay unexercised.
- **Item 10 settled for this skill: the planner searched for the skill's own rules.** Of its
  ten searches (read from the workflow log; the CLI receipt's `web_search_requests` reads 0
  although the log shows ten WebSearch calls), six served claim 1 and three of those named the skill's
  coefficients (5500, 1490, 125) and the cystine convention; the critique listed no unsourced
  rule. No prompt line is added. a280-quant states no cut-off of its own, so the "not looked
  up" branch, a rule never sought, is still untested live; protein-bench-helper's 7.2 is the
  case for it.
- **The critique rounds.** Round 1 ($0.68) supported A but objected that the tolerance basis
  misstated t1's discrimination figure (0.97%, not 1.5%, and inside the concentration
  tolerance) and that the references were incomplete; the planner's next qualification was
  rejected once, then qualified, and round 2 ($0.81) fixed the plan at A with one bookkeeping
  objection (the Beer-Lambert page was fetched but not listed with version and licence) and two
  coverage gaps: t5 cannot tell a tester who ran the bundled script from one who did the
  arithmetic, and a cysteine-only protein in reducing buffer (epsilon 0) is untested.
- **The page.** `0e471ea0….notes.json` was filled and rendered to
  `.verifier/reports/0e471ea0-….html`, and re-rendered after the wording fix.

### Open questions for the operator

1. **The disputed flag fires on any disagreement.** In this run it marks all five tests, four
   of them for objections to the set-aside software sections; Python cannot tell what a
   free-text disagreement is about. Options: leave it, with the corrected sentence, or have the
   tester name the step it disputes in a fixed form so Python can tell a key dispute from a
   complaint about the skill (a `local-tasks.md` change that needs a live recording).
2. **Item 10's "not looked up" branch** still needs a skill with a cut-off of its own;
   protein-bench-helper is the candidate.
3. The earlier open questions stand: catalog requalification and the 2026-10-13 entry's items.

### Urgent next steps, if any

`src/` changed in `report_html.py` only; restart the session before the next run, as usual. The
working tree is clean after this commit.

### Recommended next action

Verify protein-bench-helper next: it should show U beside its 7.2 cut-off or the "not looked
up" branch (item 10), a judged D claim with `session_attempts` on judge records, and whether the
corrected disputed sentence reads right where the disputes are about the key.

## Claude: 2026-10-21 (the pin moves to Opus 5.5; thirty skills staged for a stratified sweep)

### Current stage and status

Version 0.8.0 on `main`. The operator upgraded Claude Code to 2.1.302, and the verifier's own CLI
answered a one-word probe on `claude-opus-5-5` ($0.06, 2.2 s), so the MCP registration now pins
`--model claude-opus-5-5`; `LOCAL-INSTALL.md` says so and records the dates. **Changing the pin
starts a new series**: every run before this entry is on `claude-opus-5`, and the recorded task
critique (`tests/recorded/critic-task-structured.jsonl`, rubric v9) was judged by `claude-opus-5`
at `high`. The critique-effort replays of 2026-10-08 that fixed `high` were on Opus 5 too; Opus 5.5
as critic is untested. No live run has used the new pin.

### What has been done

- Thirty third-party skills were staged outside the repository, in
  `D:/Su Lab/verifier-submissions/batch-2026-10-20/`, as a stratified mix: 8 known-good (false-alarm
  control), 10 pre-fix (an earlier upstream revision that a later upstream commit corrected, so the
  error is real and the diff is the key), 6 aggregator copies, 6 wild. The keys are in
  `D:/Su Lab/verifier-keys/batch-2026-10-20/`, apart from anything a run reads. The batch README
  carries the ledger and five suggested waves of six. None has run.

### Open questions for the operator

1. Which skill runs first, and from which session: this session's `serve-local` started on the old
   pin and old code, so a run from here must go through `scripts/verify.py verify` with
   `--model claude-opus-5-5`, or through a fresh session.

### Recommended next action

Run wave 1 of the batch one skill at a time as the usage window allows, reading each run for the
new pin's `probe` record, `session_attempts` and the `sandbox_` faults, and fill the ledger.

## Claude: 2026-10-25 (datamol `8ea6c851` closed by nine reads in one message; one call per message in the prompt; the local illegal-transition budget 8 -> 32)

### Current stage and status

Version 0.8.0 on `main`, pinned to `claude-opus-5-5`. The datamol run `8ea6c851` (attempt
`77fee34e`, 2026-10-24) ended `illegal_transition_limit` after 10 steps and about 30 s: the
planner put nine `read_snapshot_file` calls in one assistant message, all carrying the token
`load_submitted_skill` returned. The first was accepted and rotated the token; the next eight
were refused (`illegal_transition`, "Use a legal tool with the latest returned state token.")
before the planner saw any result, and the eighth refusal spent the run-wide budget of 8. Python
followed `workflow.md` ("a second workflow request in the same turn") and `tool-contracts.md`;
the planner broke the rule, and its own closing message named the misreading: it did not know a
plain read rotates the token. Across the 49 kept attempts the habit belongs to the new pin: 2 of
16 `claude-opus-5` runs batched reads (two each), 10 of 26 `claude-opus-5-5` runs did (nine,
eight, eight, seven, six, five, three, two, two, two), and rdkit-library `bb4687ac` and
statsmodels `836ad6ac` finished with one illegal transition left. Pairs of parallel
`fetch_local_reference` cost one each in seven runs, a cost this plan already records.
`runtime-contract.md` asks that "a single confused step is recoverable"; one batched message is
one step, and at 8 it was not.

### What has been done

- The planner prompt (`local_entry.py`) now says: one verifier tool call per message, wait for
  its reply, and even a plain read rotates the token; further calls in the same message are
  refused and spend the illegal-transition budget.
- The local illegal-transition budget is 32, beside the repair budget of 32 (`agent.py`;
  `local-contract.md` "Legal operations"). The demo profile already ran at 32. A batch of nine
  stale reads now leaves the run in `source_ready` with 24 left, and the newest token carries it
  on; `test_local.py` holds that case and the prompt's sentences. The suite ran 448 tests, 2 skipped, all passing (2026-10-25).
- Not done: letting an accepted read keep the token, so a batch of reads succeeds. That changes
  the serialization every profile shares (`tools.py`, `workflow.md`, `tool-contracts.md`,
  `runtime-contract.md`) and inverts `test_stale_concurrent_requests_cannot_both_run`; it is the
  next step only if batches keep appearing under the new sentence.

### Open questions for the operator

1. Whether to re-run datamol on this commit, and from which session: a `serve-local` started
   before it keeps the old prompt and budget, so the run goes through `scripts/verify.py verify`
   or a fresh session.

### Recommended next action

Re-run datamol when the usage window allows, then count batched reads in every later run by
grouping the planner's tool_use blocks by `message.id` in `workflow.jsonl`: with none, the
sentence worked; with batches still spending the budget, make reads keep the token.

### Hand-over, later the same day

The operator ended their rotation and asked for four things; all four are done in one
commit on `main` dated 2026-10-25, and the first is outside the repository:

1. **A summary for the PI and every run report.** `D:/Su Lab/verifier-handoff-2026-10-25/`
   holds `sci-ai-verifier-batch-2026-10-20-summary.pdf` (eight pages: headline numbers, the
   four strata, results by stratum, what the verifier could not do, the defects found, a
   per-skill table, recommendations) and `sci-ai-verifier-batch-2026-10-20-reports.zip` (108
   members: the PDF, an index, the ledger and download manifest, and for each of the 30 skills
   its `report.html`, `report-card.md`, `report-card.json` and `notes.json`, or the attempt's
   `workflow.md` for the five build refusals and the datamol fault). Every number in the PDF
   was computed from the report cards by `batch_data.py` in the session's scratchpad; the
   findings text was written by hand from the ledger.
2. **Repository cleanup.** Removed the retired Claude Desktop Chat extension and everything
   only it used: `desktop/` (its five install documents with this machine's paths, manifest
   and `server.py`), `scripts/build_desktop.py`, `scripts/run_fixture_demo.py`,
   `tests/test_desktop_package.py`, `examples/submissions/` and `examples/catalog/`. The two
   `test_stage2.py` tests that launched `desktop/server.py` now exercise `Runtime` directly.
   `scripts/build_local.py` carries its own `archive()` and packages `images/` and the
   archive. The ignored on-disk `tmp/legacy_fixed_workflow/` and `dist/` were deleted.
   `SKILL.md`, `runtime-contract.md` section 6 and `CLAUDE.md` say the extension is retired
   and the historical profiles are reachable only through `serve --profile`. Not removed: the
   historical profile code and its four contracts, which are wired through `tools.py`,
   `agent.py` and `storage.py`; retiring them is roadmap item R4 in the plan. The recorded
   replies under `tests/recorded/` keep this machine's temporary paths; they are recordings.
3. **The plan rewritten.** `DEVELOPMENT-PLAN.md` is now the project's introduction, how a
   verification works, the repository map, the current state (with the sweep's totals), the
   working conventions, the consolidated open questions, the roadmap (R1 to R9) and a
   condensed history. Every dated entry from 2026-09-28 to this one moved here unedited, and
   new dated entries go here from now on (rule 1 of the plan).
4. **A general install guide.** `INSTALL.md` replaces `LOCAL-INSTALL.md`: Windows and macOS
   steps side by side, placeholders instead of this machine's paths, and a section on
   supplying one's own token (the registration stores `${SCI_VERIFIER_OAUTH_TOKEN:-}`, never
   a value; nothing in the repository carries a credential, checked by grep). `LOCAL-CONFIG.md`
   and `README.md` were generalised and rewritten to match. The macOS steps are untested and
   say so.

Verification performed: `python -m unittest discover -s tests -q` passed, 439 tests, 1
skipped, after the removals (448 and 2 before); a link and anchor check over the eighteen
top-level and contract documents found no broken reference; `scripts/build_local.py` built the
source zip and the CLI's `--help` ran; no changed file carries CRLF. Not verified: any macOS
step, and the clone-and-install path on another computer beyond a fresh clone of this commit
passing the suite on this one.
