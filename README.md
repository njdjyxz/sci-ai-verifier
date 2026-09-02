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
4. [`skills/scientific-verifier/references/artifact-contracts.md`](skills/scientific-verifier/references/artifact-contracts.md) — what each run, registry, result, and report artifact must contain.
5. [`skills/scientific-verifier/references/resource-policy.md`](skills/scientific-verifier/references/resource-policy.md) — what to reuse, store, return, retain, promote, and discard.
6. [`skills/scientific-verifier/references/evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md) — evidence grades, AI-involvement limits, and grade fallback rules.

## Architecture

```text
User starts verifier
        |
Python creates the run and starts a bounded verifier-agent session
        |
Python supplies SKILL.md, workflow.md, and committed run state
        |
Python exposes only the tools legal for the committed state
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

At startup or resumption, Python supplies the complete verifier `SKILL.md`, the complete authoritative `workflow.md`, their versions or digests, the committed run and claim states, current limits, and only the tool definitions legal in that state. Each source is a separately labeled context block with an explicit trust class. The submitted scientific skill is not included at bootstrap; Python reads and hashes it through `load_submitted_skill`, then returns its content as explicitly untrusted data.

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
- Exact evaluator lookup.
- Workflow state, prerequisites, and tool eligibility.
- Resource materialization, digests, and locks.
- Reproducible case construction.
- Objective bundle validation and plan prerequisites.
- Evaluator execution, metrics, tolerances, and grade ceilings.
- Run audit trail and report rendering.

A Python tool result is authoritative. The verifier agent may respond to it but cannot override it.

## Complete workflow

Each submitted skill is processed as atomic claims:

```text
load and profile
→ route claim type
→ reuse evaluator or define target evaluator
→ create evaluation plan
→ reuse or acquire resources
→ build and validate evaluation capability when needed
→ audit exact plan and asset versions
→ execute evaluator
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

Pass or fail is separate from evidence strength. An A-grade failure is strong evidence against a claim; a D-grade pass establishes documentary consistency only.

## Storage principle

Per-skill artifacts stay under `.verifier/runs/<run-id>/` or company-managed storage. Large payloads use content-addressed managed storage and are referenced by digest. Git stores small reusable metadata and implementation code, not every submitted skill's datasets and reports.

The verifier returns the report card, machine-readable results, claim manifest, and reproducibility references. It retains the minimum provenance and assets required for audit. Temporary downloads, duplicate payloads, failed drafts, unused search results, caches, and secrets are discarded according to the resource policy.

## Active repository structure

```text
.
├── AGENT.md
├── README.md
├── registry/
│   ├── claim_types.json
│   ├── evaluators.json
│   ├── bundles/
│   └── resources/
├── skills/
│   └── scientific-verifier/
│       ├── SKILL.md
│       └── references/
│           ├── artifact-contracts.md
│           ├── evidence-rubric.md
│           ├── resource-policy.md
│           ├── tool-contracts.md
│           └── workflow.md
└── tmp/
    └── legacy_fixed_workflow/
```

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

1. The bounded verifier-agent loop and deterministic session bootstrap.
2. State-aware tool dispatch and the common `ok`, `retryable`, and `fatal` protocol.
3. `load_submitted_skill`.
4. `commit_claim_manifest`.
5. Run-state and artifact persistence required by those operations.

Later implementation stages will add the remaining tools in workflow order without changing the reviewed Markdown silently.
