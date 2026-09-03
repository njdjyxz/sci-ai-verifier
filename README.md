# Scientific AI Verifier

Scientific AI Verifier is a planned agent-orchestrated system for testing the scientific claims made by chemical, biological, and other scientific AI skills. Its goal is not merely to confirm that a skill runs, but to determine what each atomic claim is, what evidence can test it, how independent that evidence is from AI judgment, and what conclusion the evidence supports.

The verifier agent will manage semantic workflow decisions and recovery. Small approved Python tools will perform operations that must be reproducible, exact, persistent, or auditable.

## Current stage: complete Markdown specification

Stage 1 contains the complete intended verifier behavior in Markdown. It names future Python files and tools but does not implement them.

There is intentionally no active Python package at the repository root. This allows the architecture, workflow, interfaces, artifacts, resource policy, failure behavior, and grading rules to be reviewed before code makes them harder to change.

## Review order

1. [`skills/scientific-verifier/SKILL.md`](skills/scientific-verifier/SKILL.md) — the verifier agent's entry instructions and reference routing.
2. [`skills/scientific-verifier/references/workflow.md`](skills/scientific-verifier/references/workflow.md) — the authoritative textual state machine, exact tool transitions, autonomous fallback behavior, and failure paths. Its retained graph is a non-authoritative review aid.
3. [`skills/scientific-verifier/references/tool-contracts.md`](skills/scientific-verifier/references/tool-contracts.md) — every approved Python tool and the planned `.py` file responsible for it.
4. [`skills/scientific-verifier/references/runtime-contract.md`](skills/scientific-verifier/references/runtime-contract.md) — what the host process must guarantee so the state machine holds when the agent is a language model.
5. [`skills/scientific-verifier/references/artifact-contracts.md`](skills/scientific-verifier/references/artifact-contracts.md) — what each run, registry, result, and report artifact must contain.
6. [`skills/scientific-verifier/references/resource-policy.md`](skills/scientific-verifier/references/resource-policy.md) — what to reuse, store, return, retain, promote, and discard.
7. [`skills/scientific-verifier/references/evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md) — evidence grades, AI-involvement limits, subject non-determinism, and grade fallback rules.

## Architecture

```text
User starts verifier
        |
Python creates the run and starts a bounded verifier-agent session
        |
Python supplies SKILL.md, workflow.md, and committed run state
        |
Python declares the tools legal for the committed state and enforces it on dispatch
        |
The agent chooses a permitted semantic branch and requests its named tool
        |
Python validates and performs the deterministic operation
        |
Python returns ok, retryable, or fatal
        |
The agent continues, repairs, lowers the evidence target, or completes
        |
Python writes the audited claim results and report card
```

## Session context

At startup or resumption, Python supplies the complete verifier `SKILL.md`, the complete authoritative `workflow.md`, their versions or digests, the committed run and claim states, current limits, and its declaration of the tools legal in that state. Each source is a separately labeled context block with an explicit trust class. The submitted scientific skill is not included at bootstrap; Python reads and hashes it through `load_submitted_skill`, then returns its top-level content as explicitly untrusted data. Files inside the snapshot are read one at a time through `read_snapshot_file`, because a skill's testable scientific statements usually live in its bundled reference documents rather than in the file that routes to them.

Tool definitions may be published more broadly than they are legal. Legality is declared per state and enforced by the dispatcher, which is what the security boundary has always rested on; `runtime-contract.md` explains why the published surface is held stable instead.

The runner supplies applicable tool and artifact contract sections with each legal operation and introduces the evidence rubric and resource policy only when their stages become relevant. Registries, run artifacts, datasets, expected answers, evaluator code, and credentials are not exposed as raw project files; approved tools return only the structured data required for the current state.

The verifier agent owns:

- Atomic claim interpretation.
- Semantic claim-type comparison.
- Evaluation strategy and target-evaluator descriptions.
- Resource-candidate reasoning.
- Bounded scope, fairness, and limitation assessment.
- Recovering from retryable tool results.
- Explaining evidence and risks.

Python owns:

- File access, hashing, IDs, and schemas.
- Artifact and registry integrity.
- Exact per-claim evaluator/harness and approved subject-runner lookup, including lower-grade fallback.
- Workflow state, prerequisites, and tool eligibility.
- Resource materialization, digests, and locks.
- Reproducible case construction.
- Objective bundle validation and plan prerequisites.
- Running the submitted skill under the audited subject runner, scoring each trial with an isolated evaluator, then aggregating scored results.
- Obtaining a completed independent documentary assessment for grade D, or recording assessor unavailability.
- Evaluator execution, metrics, tolerances, and grade ceilings.
- Run audit trail and report rendering.

A Python tool result is authoritative. The verifier agent may respond to it but cannot override it.

## Complete workflow

Each submitted skill is processed as atomic claims:

```text
load and profile
→ read the snapshot files that carry the claims
→ route claim type
→ reuse evaluator or define target evaluator
→ create evaluation plan, including the subject runner and trial rules
→ reuse or acquire resources
→ build and validate evaluation capability when needed
→ audit exact plan and asset versions
→ run the submitted skill under the audited subject runner, then the evaluator
→ assign supported claim result and evidence grade
→ write claim-level report card
```

Every decision gate has a failure path. Missing resources, inadequate cases, failed audits, and operational failures never become scientific passes. The default unattended behavior is to continue at the strongest supportable grade and disclose downgrades. If the user explicitly requires a minimum grade, lower-grade evidence is labeled as not satisfying that requirement.

## Evidence principle

The preferred result is a scientific verdict determined completely outside AI judgment. The verifier agent may orchestrate a deterministic test without becoming its oracle.

- A: direct independent ground truth; no AI judgment in scoring or verdict.
- B: external benchmark or replication; normally no AI judgment in scoring.
- C: reproducible indirect properties or simulations; limited AI may design the checks.
- D: bounded documentary judgment; AI or human judgment is primary and disclosed.
- U: no acceptable scientific evidence; no scientific conclusion.

Documentary-only D does not run the submitted skill and therefore does not require an installed subject runner. It still requires an approved documentary harness and a completed independent assessment; assessor unavailability is an operational outcome, not U.

Pass or fail is separate from evidence strength. An A-grade failure is strong evidence against a claim; a D-grade pass establishes documentary consistency only.

A submitted skill is usually a set of instructions for a model, so running it twice can give two answers. Every execution plan fixes the **subject runner**, model/settings, trial count, and deterministic rule aggregating individually scored trials. An approved claim-specific trial-grade policy is locked during audit; Python computes the verdict and evidence ceiling separately from the retained sample. A single trial against a non-deterministic subject cannot support grade A or B. Agreement is distinct from accuracy: unanimous failures may strongly refute a claim. If no A-through-C evidence grade remains supported, the workflow attempts a separately audited documentary plan rather than fabricating a D or U result.

The model running the verifier agent and the model running the submitted skill are different roles with separate records. The first orchestrating a run does not weaken the evidence; the second is the thing being measured, not evidence about it.

## Storage principle

Per-skill artifacts stay under `.verifier/runs/<run-id>/` or company-managed storage. Large payloads use content-addressed managed storage and are referenced by digest. Git stores small reusable metadata and implementation code, not every submitted skill's datasets and reports.

The registry has two layers. `registry/` in Git holds entries a human has reviewed and committed; `.verifier/registry/` holds provisional entries written by runs. Runs read the merge and write only to the runtime layer, so no automated step can rewrite the files the review process depends on, and two runs on one checkout cannot race for the same bytes. Promotion is a human commit.

Text payloads are normalized to LF before hashing. Without that, the same skill checked out on Windows and on Linux would produce different snapshot digests, and every content-addressed guarantee here would be platform-dependent. `.gitattributes` enforces the same normalization for repository content.

The verifier returns the report card, machine-readable results, claim manifest, and reproducibility references. It retains the minimum provenance and assets required for audit. Temporary downloads, duplicate payloads, failed drafts, unused search results, caches, and secrets are discarded according to the resource policy.

## Active repository structure

```text
.
├── .gitattributes
├── CLAUDE.md
├── README.md
├── evaluators/
├── registry/
│   ├── claim_types.json
│   ├── evaluators.json
│   ├── subject_runners.json
│   ├── bundles/
│   └── resources/
├── skills/
│   └── scientific-verifier/
│       ├── SKILL.md
│       └── references/
│           ├── artifact-contracts.md
│           ├── evidence-rubric.md
│           ├── resource-policy.md
│           ├── runtime-contract.md
│           ├── tool-contracts.md
│           └── workflow.md
└── tmp/
    └── legacy_fixed_workflow/
```

`evaluators/` will hold approved harness implementation code and is empty in Stage 1. `registry/bundles/` and `registry/resources/` are empty and tracked so a fresh clone has them. `registry/subject_runners.json` is a reviewed-only catalog, initially empty; it has no runtime overlay. Its record contract is in `artifact-contracts.md`. The runtime registry and every run artifact live under the gitignored `.verifier/`. Resource locks are scoped to a claim and semantic plan revision; sharing a payload digest does not share authorization.

## Planned implementation structure

The Markdown tool contracts name this future structure without creating it:

```text
src/sci_ai_verifier/
├── agent.py
├── tools.py
├── storage.py
├── ingest.py
├── claims.py
├── routing.py
├── planning.py
├── resources.py
├── evaluation.py
├── audit.py
├── execution.py
└── reporting.py
```

The files are planned responsibility boundaries, not separate workflow controllers. `agent.py` will run one generic agent/tool loop while enforcing the authoritative workflow state, context bootstrap, and legal tool set; the other files will provide small deterministic capabilities behind approved tools.

## Preserved fixed workflow

The previous Python-controlled implementation, tests, packaging file, and README remain intact under [`tmp/legacy_fixed_workflow/`](tmp/legacy_fixed_workflow/). They are reference material only and are not active Stage 1 code.

Useful deterministic behavior may be migrated later after the new tool contract is reviewed. The old controller should not be restored as a competing workflow.

## Next implementation stage

Stage 2 will build only:

1. The bounded verifier-agent loop and deterministic session bootstrap, meeting `runtime-contract.md`.
2. State-aware tool dispatch driven by the state tables in `workflow.md`, with the common `ok`, `retryable`, and `fatal` protocol and the two separate retry budgets.
3. `load_submitted_skill`.
4. `read_snapshot_file`.
5. `commit_claim_manifest`.
6. Run-state and artifact persistence required by those operations, including the LF normalization the digests depend on.

The subject runner is not implemented in Stage 2. Later capability selection and planning need its reviewed catalog metadata, but only `execute_evaluation_plan` invokes the runner. Implementation and each catalog entry require their own security review.

Later implementation stages will add the remaining tools in workflow order without changing the reviewed Markdown silently.
