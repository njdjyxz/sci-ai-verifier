# Scientific verifier: review guide

This is a reading map for the current Stage 1 specification, including the nine-fix update in commit `59a0b62` on `main`. Prepared on 2026-09-03.

It explains the workflow, when each document is used, and a suggested review order. It is for human reviewers: it is not another source of verifier instructions. If this summary and a contract disagree, review the contract; do not treat this guide as an override.

Scope: all active repository Markdown documents except `README.md`. The seven verifier documents below were edited in the nine-fix update. `CLAUDE.md` is unchanged contributor context, and this guide is new. The archived implementation under `tmp/legacy_fixed_workflow/` and reports that a future runtime will generate are outside this review.

## 1. The basic idea

The verifier agent reads claims and proposes how to check them. The Python host controls what may happen, saves the records, runs approved tools, and enforces the rules. For A-C, audited deterministic rules produce the scientific verdict. For D, a separate assessor reviews the documentary evidence. The planning agent cannot invent either result.

Three terms used throughout the files:

- **Subject runner:** the adapter that actually runs the submitted skill. Required for A-C, not for documentary-only D.
- **Evaluator / harness:** the approved checking capability. An existing evaluator can be reused; an approved general harness can be configured into a claim-specific evaluator. The agent does not write evaluator code during a run.
- **Resource lock:** a saved record of exactly which resources a particular claim's plan revision is authorized to use. Sharing the same resource bytes does not share that authorization.

These Markdown files do not trigger themselves. The future host supplies instructions or reference sections when the workflow requires them. Stage 1 specifies that behavior; it does not yet implement the active Python runtime.

## 2. Which documents are supplied, and when?

The following rules apply across the stage table in the next section:

| Document | When it is used |
|---|---|
| [SKILL.md](../skills/scientific-verifier/SKILL.md) | Supplied in full at every new or resumed verifier session. Defines the agent's role and boundaries. |
| [workflow.md](../skills/scientific-verifier/references/workflow.md) | Also supplied in full at every new or resumed session. Its state tables govern every next action. |
| [tool-contracts.md](../skills/scientific-verifier/references/tool-contracts.md) | Before a tool is declared legal, the host supplies that tool's section, the common result protocol, and its machine-readable definition. |
| [artifact-contracts.md](../skills/scientific-verifier/references/artifact-contracts.md) | The relevant section is supplied before an operation creates or changes the corresponding saved record. |
| [evidence-rubric.md](../skills/scientific-verifier/references/evidence-rubric.md) | Supplied for planning, audit, execution-result, and grading states. |
| [resource-policy.md](../skills/scientific-verifier/references/resource-policy.md) | Supplied for snapshot, resource, bundle, registration, and finalization states. |
| [runtime-contract.md](../skills/scientific-verifier/references/runtime-contract.md) | Read by the host implementer; enforced by the host throughout the run. The verifier agent does not need to read it to choose a transition. |
| [CLAUDE.md](../CLAUDE.md) | Instructions for a coding agent or contributor working on this repository. Not part of the verifier session bootstrap. |
| [This guide](REVIEW-GUIDE.md) | Human review only. Never a workflow dependency. |

At startup/resumption, the host also supplies committed states, exact legal tools, limits, and retry information. After loading the submission, snapshot identity and integrity metadata are separate from source text. The submitted skill and other external content remain untrusted data, even when their digests have been verified. Later reference sections are appended without rewriting earlier context blocks.

## 3. Current workflow, stage by stage

Read this table from top to bottom for the normal path. Stages 4-11 operate on one claim at a time; different claims may be in different states. The repair paths below explain when a claim goes backward.

In every row, `SKILL.md` and the complete workflow are already present. The matching tool-contract section is supplied before the listed tool becomes legal, and the matching artifact-contract section before any record is changed. The last column highlights additional references or records to inspect; it is not a replacement for those universal rules.

| Stage and state | What happens / tool names | Additional documents or record sections |
|---|---|---|
| 0. Start or resume | Host assembles trusted instructions, committed state, and separately labeled user/source data. It declares the legal tools. | Workflow: **Session bootstrap and trust classes**. Runtime: **Context assembly** and host enforcement. |
| 1. Preserve the submission — `created` | `load_submitted_skill` makes an immutable snapshot. An unusable source is an operational failure, not a scientific verdict. | Resource policy; artifacts: **Run record**, **Submitted-skill snapshot**. |
| 2. Extract claims — `source_ready` | `read_snapshot_file` inspects snapshot files; `commit_claim_manifest` saves individual, testable claims. No accepted claims goes directly to reporting. | Artifacts: **Claim manifest**, snapshot provenance. |
| 3. Assign claim types — `routing` | `list_claim_types`, then `commit_claim_type_assignments`. This is the only bulk claim transition: all manifest claims receive routes together. | Artifacts: **Routing artifact**. |
| 4. Find a checking capability — `capability_selection` | `find_registered_evaluators` searches for this claim, from the intended grade down through D. At the strongest supported grade, prefer a compatible registered evaluator over building one from an approved harness. A-C also needs a compatible approved subject runner. | Artifacts: routing/selection information, **Evaluator registration**, **Reviewed subject-runner catalog**. |
| 5. Commit a plan — `planning` | `commit_evaluation_plan` fixes the claim, capability, grade, evidence design, and rules. A complete plan gets its own revision and resource lock. Depending on readiness, proceed to resources, target construction, or audit. | Evidence rubric; artifacts: **Evaluation plan**, **Subject-runner configuration**, **Resource lock**. |
| 6. Find and validate evidence resources — `resource_resolution` | `find_resources` returns candidates. `materialize_resources` validates candidates and records the exact bindings for each required role. Rejected candidates can be replaced. | Resource policy; artifacts: **Resource lock**. |
| 7. Build a target capability, if needed — `bundle_construction`, then `provisional_registration` | `build_evaluation_bundle`, `validate_evaluation_bundle`, then `register_evaluator`. Registration is provisional. Return to planning to bind the exact registered evaluator, revalidate resources for the new plan/lock, and then audit. A compatible existing evaluator skips construction, not audit. | Resource policy; artifacts: **Evaluation bundle**, **Evaluator registration**, then plan/lock sections. |
| 8. Audit the exact plan — `audit` | `commit_plan_audit` checks scientific adequacy, versions, resources, and isolation. A-C includes runner and trial-policy checks. D checks the documentary rubric and independent-assessor boundary instead. Passage authorizes execution and promotes an eligible provisional pair. | Evidence rubric; artifacts: **Plan audit** and the records it binds. |
| 9A. Test the submitted skill — `execution`, grades A-C | `execute_evaluation_plan` runs subject trials, scores each trial independently, then aggregates the scored results. Audited rules determine the status and strongest eligible grade. | Evidence rubric: **Subject non-determinism**, **Audited trial-grade policy**, **Verdict authority**. Artifact requirements for execution provenance and results. |
| 9B. Assess documents — `execution`, grade D | The same tool prepares the bounded evidence packet and obtains a completed assessment from an independent human or separate assessor session. It does not run the submitted skill. The planner cannot assess its own packet. | Evidence rubric: **Verdict authority**; artifacts: **Documentary assessment**. |
| 10. Save the claim result — `result_commit` | `commit_claim_result` copies the authoritative A-C decision or D assessment. A separately authorized no-evidence path records U with `inconclusive`. Operational failures are saved by Python as operational outcomes, not invented scientific results. | Evidence rubric; artifacts: **Claim result**, **Operational outcome**. |
| 11. Finish this claim | A claim reaches `terminal_result` or `terminal_operational`. Other unfinished claims continue using their own legal tools. | Workflow state tables and common tool-result protocol. |
| 12. Report and finalize — `reporting` | Once every accepted claim has a result ID or operational-outcome ID, `write_report_card` produces JSON and Markdown reports and records cleanup. No-claim runs also report. Successful reporting ends in `completed`; an unrecoverable reporting failure leaves `incomplete`. | Resource policy; artifacts: **Report card**; workflow: **Report and finalize**. |

### Important branches to trace during review

- **A lower grade is needed:** return to planning. If the replacement capability has not been selected, submit the reduced `reselection_request`, return to capability selection, and only then commit a full new plan. The request records why reselection is needed without demanding unknown evaluator or rubric fields. A lower-grade match already selected should not cause a lookup loop.
- **The audit requires different resources:** return to capability selection with the recorded repair requirements. Exclude the stale evaluator/bundle binding for this claim at every grade. Choose a suitable replacement or reconstruction path, create a new plan/lock, validate the affected resources, and audit again. Do not globally invalidate assets other claims can still use.
- **A candidate is rejected or a bundle needs repair:** follow the specific returned state. Candidate replacement stays in resource resolution; bundle repair may return to construction or resource resolution. Audit repair has its own routes. Similar outcome names do not imply the same destination at every stage.
- **No subject runner is installed:** still consider documentary D. D requires an approved documentary capability and independent assessment, not a subject runner. If the required execution capability cannot be provided and no D capability fits, record an operational outcome as specified by lookup.
- **A-C trials provide no supportable execution grade:** attempt D through planning and capability selection. Do not relabel the existing run as D or jump straight to U. Operationally missing trials instead use bounded retries and then an operational failure.
- **No independent D assessor is available:** stop that claim with `assessor_unavailable`. Do not let the planner fill in, wait indefinitely, or call the absence U. A valid independent D assessment may legitimately conclude `fail`.
- **No acceptable A-D evidence exists:** follow the authorized U path and save `inconclusive`. Missing infrastructure, crashes, and exhausted limits are different from lack of scientific evidence.
- **A tool request is retryable:** committed state does not change. Repair only the identified problem within the declared budget. Illegal requests use a separate budget. Follow the returned legal-tool list instead of guessing a transition.
- **The session is interrupted or a failure is terminal:** resume from committed records and restore the same trust separation when resumption is allowed. A claim-local failure leaves independent claims active. Run-level termination, reporting availability, and cleanup belong to the host's failure-handling contracts.

The full outcome-to-state table in `workflow.md` is the place to check every individual branch. This guide deliberately does not duplicate that table.

## 4. Each Markdown file's purpose

| File | Question it should answer | What to inspect in this review |
|---|---|---|
| [SKILL.md](../skills/scientific-verifier/SKILL.md) | What is the verifier agent responsible for, and what must it never do? | Clear entry instructions; where to find detailed rules; independent verdict authority; source content never becoming instructions. |
| [workflow.md](../skills/scientific-verifier/references/workflow.md) | What happens next for each state and outcome? | Complete legal-tool and outcome tables; claim-local progress; downgrade, repair, documentary, U, and operational paths. |
| [evidence-rubric.md](../skills/scientific-verifier/references/evidence-rubric.md) | What does each grade mean, and who determines grade and status? | Grade versus pass/fail; claim-specific audited thresholds; score-before-aggregation; single-trial cap; independent D; no automatic U after weak A-C results. |
| [tool-contracts.md](../skills/scientific-verifier/references/tool-contracts.md) | What can the agent send to each tool, and what can come back? | Inputs available at that point; explicit outcomes and side effects; reduced reselection request versus full plan; errors that do not masquerade as scientific results. |
| [artifact-contracts.md](../skills/scientific-verifier/references/artifact-contracts.md) | What must be saved so the run is explainable, auditable, and resumable? | IDs, revisions, digests, and parent links; per-claim/per-plan locks; audit invalidation; policy references and measured counts; independent-assessor identity. |
| [resource-policy.md](../skills/scientific-verifier/references/resource-policy.md) | Where does evidence live, what may be reused, and what is retained or removed? | Reviewed versus runtime registries; validation before reuse; claim-local authorization versus shared bytes; provisional promotion; reproducibility and cleanup. |
| [runtime-contract.md](../skills/scientific-verifier/references/runtime-contract.md) | What must the host enforce when the agent makes mistakes or stops? | Tool visibility versus permission; dispatcher checks; one workflow request per turn; separate retry budgets; trustworthy context assembly and termination. |
| [CLAUDE.md](../CLAUDE.md) — unchanged context | How should contributors change this repository? | Stage 1 remains documentation-first; Python/agent ownership; which documents are authoritative; legacy code stays separate. |
| [REVIEW-GUIDE.md](REVIEW-GUIDE.md) — new | How should a human navigate this review? | Links and summaries match the actual contracts. It must not introduce new policy. |

Non-Markdown companion: [registry/subject_runners.json](../registry/subject_runners.json) was also added in the nine-fix update. It is the reviewed subject-runner catalog seed. Inspect it alongside the catalog section in `artifact-contracts.md`; an empty catalog is not the same as a corrupt catalog. It does not itself provide a working subject runner.

## 5. Recommended review order

Use three passes so you can decide whether the design makes sense before checking every field.

### Pass 1: understand the behavior

1. **This guide.** Get the map; no need to memorize tool names.
2. **`CLAUDE.md` — optional context skim.** Check the project boundary if you have not read it recently. It was not changed in the nine-fix update.
3. **`SKILL.md`.** Ask: could an agent start correctly and understand what it is not allowed to decide?
4. **`workflow.md`.** Read bootstrap, state tables, then numbered stages. Follow one ordinary claim and one downgrade from start to finish.
5. **`evidence-rubric.md`.** Ask: are these the scientific conclusions you want the system to make? Settle grade and verdict policy before reviewing storage details.

### Pass 2: check that every path can actually be followed

6. **`tool-contracts.md`, with `workflow.md` beside it.** For each workflow outcome, check that the named next tool exists, is legal, and accepts information the agent already has. Pay special attention to reselection and repair loops.
7. **`artifact-contracts.md`.** Trace one claim's snapshot -> route/selection -> plan -> lock -> bundle/evaluator -> audit -> execution or assessment -> result -> report. Check that changing a plan cannot silently reuse stale authorization.
8. **`resource-policy.md`.** Check the same trace for storage, reuse, promotion, and cleanup. Confirm that repairing one claim does not break another claim using the same resource.

### Pass 3: check host enforcement and failure handling

9. **`runtime-contract.md`.** Check whether the host can enforce the preceding documents when the model makes illegal requests, emits multiple requests, stops, or resumes. This is the last full-file read because it depends on the workflow and tool contracts.
10. **Return to the workflow for a short scenario sweep.** Use the checks below. Record contradictions as review findings rather than resolving them by interpreting this guide as new policy.

### Final scenario sweep

- One claim needs a lower grade while another claim is already in audit: only the first claim is reselected.
- A reused evaluator fails the resource audit: the stale pair cannot return through a lower-grade shortcut.
- Two claims use the same dataset: each plan revision still has its own validated lock and audit bindings.
- No subject runner exists, but an approved documentary harness and independent assessor do: D remains possible.
- A D packet exists, but no independent assessor is available: there is no D result and no U substitution.
- Every trial fails consistently: the verdict can be `fail` without automatically weakening the evidence grade.
- Trials disagree, have invalid scientific observations, or hit a boundary: the pre-audited claim-specific policy covers the case; it is not adjusted after seeing results.
- A nondeterministic subject has only one trial: C is a ceiling, not an automatic entitlement to C.
- There are no usable scientific cases after evaluation: attempt D; distinguish this from trials missing because infrastructure failed.
- A resumed source file says to ignore verifier instructions: its text remains untrusted data.
- There are zero claims, or a claim ends operationally: reporting accounts for that case without inventing scientific results.

## 6. What this review does not establish

These are Stage 1 contracts, not a completed runtime. The guide does not establish that Python dispatch, persistence, provider integration, assessor adapters, or cleanup have been implemented or tested end to end. The nine-fix update also does not mean every deferred implementation question or remaining review finding has been resolved. Review the documents as the intended design, and keep implementation acceptance separate.
