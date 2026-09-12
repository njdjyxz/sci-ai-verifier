# Development plan and log

## Rules for maintaining this file

1. Read the latest entry before planning or implementing project changes. Treat it as development context; the reviewed workflow and contracts remain authoritative.
2. Each agent may create only one log entry per calendar day by default. After substantial work, a review that changes the plan, or an agreed change of direction, first look for that agent's entry for today and edit it in place. Create a new daily entry only when none exists. Use a consistent author name across sessions; another session is not a reason to create another entry. Keep entries in chronological order, oldest first.
3. Begin each entry with `## <Author>: YYYY-MM-DD`, for example `## Codex: 2026-09-08`. Use the actual author and the date in `America/Los_Angeles`. Preserve earlier days' entries and record later corrections in the current day's entry. When editing today's entry, briefly identify significant superseded decisions and their replacements. If a significant change would benefit from a separate same-day entry, the agent may ask the user for approval, explaining why; create that additional entry only after explicit approval, and include a time and the approval reference. Otherwise, continue updating the existing daily entry.
4. Include these five fields in every entry:
   - **Current stage and status:** where development stands and what completion means.
   - **What has been done:** completed work, relevant files or commits, verification performed, and material limitations. Distinguish work done in this session from earlier work being summarized.
   - **Urgent next steps, if any:** blockers or prerequisites that must be addressed before dependent work. Write `None` when there are none; distinguish immediate urgency from a prerequisite for later work.
   - **Suggested next move:** the next development direction and its intended outcome.
   - **Recommended next action:** the specific, bounded task to begin next, including how to recognize that it is finished.
5. Keep entries concise and use plain English. Separate confirmed facts, approved decisions, and recommendations. Do not present a proposed task as implemented, approved, or tested.
6. Record unresolved choices that could change scientific meaning or development scope. Recommendations in this log do not themselves authorize implementation or override user decisions.
7. Link relevant repository files with relative paths. Record meaningful validation limits and distinguish local changes from work committed or pushed to GitHub.
8. This file records project development. The future runtime must separately record tool calls, results, state changes, and evidence references for individual verification runs.

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
- Added the [review guide](reviews/REVIEW-GUIDE.md), covering document purposes, loading stages, review order, and scenarios to check.
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
- Independently checked **four runs, 15 events, and 21 distinct committed objects**: event linkage/digests, token/state/budget consistency, immutable source bytes, prior delivery of exact quotes, claim/manifest identities, projections, finalization, and resume context. All mechanical checks pass, with claim counts 1/0/1/1 for reference/no-claims/conflict/resume. All runs stop at `stage2_complete` with `verification_complete: false`. The audit preserved all 52 managed-data files byte-for-byte and called no runtime controls. See [the machine-readable audit](reviews/stage2-acceptance-2026-09-10.json) for run IDs, paths, event digests, and precise scope. No developer suite rerun or substitute model run was needed for this inspection.
- Recorded one extraction-fidelity follow-up: resumed run `125ceb03-30a0-446a-841c-84138ed0718b` adds an isotope-selection definition to `expected_behavior` that the fixture does not provide. The primary claim and quotation remain correct; this is a source-grounding observation, not a judgment of the definition's scientific truth or a resume/storage failure. Preserve the original manifest and tighten guidance before treating that extra definition as a submitted requirement. The conflict manifest's self-report that no outside tools were used is not independent evidence; the user is unsure how to identify such calls, and no matching local transcript was available. That one app-behavior check remains pending.
- Product direction clarified in the intervening discussion: the user wants one public **verify this skill** action, with claim extraction and other stages kept internal rather than offered as standalone features. The long prompts are development acceptance instructions. Restart-first recovery was discussed as a simplification; no resume/cancel function was removed and no public-interface redesign was implemented. The existing Stage 3 scope covers routing and catalog lookup only; evaluation planning/execution, assessment, and reporting require additional implementation phases before full verification is available.

- Implemented the dedicated [Stage 3 contract](skills/scientific-verifier/references/stage3-contract.md) with matching state/tool and artifact updates. New desktop runs use Stage 3; Stage 2 remains an explicit operator profile and older completed runs are never reopened. Tightened extraction guidance so absent behavior/scope stays `Not specified`, including isotope conventions; preserved all original app manifests.
- Added [catalog verification](src/sci_ai_verifier/catalog.py), [routing](src/sci_ai_verifier/routing.py) and the [release utility](scripts/catalog_release.py). Downloads use this project's fixed GitHub repository, exact commit and independently supplied manifest digest; assets/interfaces are verified before activation, offline caches require exact receipts, and active runs use immutable objects. No model-triggered downloads or runtime writes to reviewed registries exist. Initial `catalog/` mirrors the empty reviewed registries; it is local and unpublished.
- Added three routing tools, atomic complete-manifest assignment, run-local provisional types, strongest-grade lookup, registered preference, A-C interface pairing and D fallback without a runner. Missing implementations/runners produce distinct claim-local operational artifacts while other claims continue. Lookup results are bounded, carry exact version/resource pins and never produce a scientific verdict.
- Prepared [the chemical mass pilot](reviews/CHEMICAL-MASS-PILOT.md), three provisional type definitions, two provisional capability descriptions, NIST isotope reference values, a narrow candidate formula parser and per-trial numeric scorer. Boundary, known-answer and deliberately wrong-observation tests pass. These helpers are not installed, approved or connected to a subject runner; no submitted skill has been evaluated by them.
- Added [the full-project completion checklist](https://github.com/njdjyxz/sci-ai-verifier/blob/a8d6045657c5a2a10fdfb4f9ec139f60b73e31f2/reviews/PROJECT-COMPLETION.md) and [0.3.0 installation guide](desktop/STAGE3-INSTALL.md), refreshed README and built the MCPB/skill ZIP. The single public action remains **verify this skill**; extraction and routing are internal steps. No installed app settings, original app data or legacy files were changed.
- Validation: the expanded suite contains **77 tests; 75 passed and two skipped** on Python 3.14 and bundled Python 3.12. The skips remain actual Python 3.11 availability and privileged symlink creation. Both extracted-package profiles and archive reproducibility pass. The new reader's compatibility validator also accepts the four original 0.2.0 app journal states through a read-only inspection; this is not a new live resume test. See [Stage 3 validation](reviews/stage3-validation-2026-09-10.json) for precise evidence and limits.
- All Stage 3 source and documentation changes remain local, uncommitted and unpushed. Remote transport success is fixture-tested; no newly published GitHub catalog or live 0.3.0 app test is claimed. Maintainer/scientific review of the seed collection remains required before promotion.

### Contract organization and lifecycle

Claude's note recommends keeping **the Stage 2 profile itself as one file**; it does not recommend merging every contract. Retain separate workflow, tool, runtime, artifact, resource, and evidence documents because they answer different questions. Link shared rules instead of copying them. The Stage 2 contract is the active implementation profile, including scope, exceptions, limits, persistence, and compatibility; it is not a throwaway development file.

Clarification of Claude's proposed deletion condition: a restricted host alone does not make this contract disposable. Revise or replace it only when the next reviewed profile covers its still-applicable guarantees and explicitly handles existing saved runs. Stage 3 planning belongs in a dedicated reviewed catalog/routing contract once that work starts; move the existing dependency paragraph then. There is no benefit to a broad document merge during final Stage 2 repair.

### Urgent next steps, if any

No local routing implementation blocker. Before claiming a complete scientific verifier, review/promote the candidate chemical catalog, identify the actual submitted skill and approved subject invocation boundary, and implement planning, resource locks, audit, isolated execution, independent assessment where required, and reporting. The reviewed registries currently contain no evaluator or subject runner. The initial catalog is not published, and 0.3.0 has not been installed/tested live.

Preserve the earlier limitations: instruction-conflict Chat tool activity remains uninspected; exact model identity is unavailable; cancellation/personal submissions were not tested live; Python 3.11 and an independent MCP client remain unverified. No automatic retransmission idempotency or full power-loss durability is claimed.

### Suggested next move

Review the [chemical mass pilot](reviews/CHEMICAL-MASS-PILOT.md) and [completion checklist](https://github.com/njdjyxz/sci-ai-verifier/blob/a8d6045657c5a2a10fdfb4f9ec139f60b73e31f2/reviews/PROJECT-COMPLETION.md), then connect the first scientifically reviewed evaluator to a controlled subject runner through the existing plan/audit contracts. Keep Stage 3 acceptance separate from scientific performance. The earlier suggestion to rerun Stage 2 fixtures remains superseded by their recorded evidence.

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
[local validation](reviews/local-validation-2026-09-11.json).

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
