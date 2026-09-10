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
