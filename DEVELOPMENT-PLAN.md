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
