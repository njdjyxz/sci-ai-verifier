# Sci-AI Verifier

Sci-AI Verifier is a framework for evaluating the scientific accuracy of AI skills and recipes in chemistry and biology. Its purpose is not merely to check whether a skill executes successfully, but to determine whether its scientific claims are supported by appropriate evidence, datasets, test cases, and evaluation methods.

The project treats each atomic scientific claim as the unit of verification. A single skill may therefore receive different results for different claims. Example scientific skills and recipes can be found in the [Scripps AI Enablement catalog](https://github.com/scripps-ai-enablement/sci-ai-enabler/tree/main).

## Current implementation: claim manifest

The package has one operation: start verification of a submitted skill. The current implementation completes only the first subprocess: it asks Claude to extract scientific claims, validates Claude's structured response, assigns claim IDs in Python, and writes the claim manifest. It does not yet find evaluation resources, assign evidence grades, execute scientific tests, or generate a report card.

```text
Submitted skill file
        |
        v
Python reads and hashes the file
        |
        v
Python calls the Claude API
        |
        v
Claude returns extracted claims without IDs
        |
        v
Python validates fields and source quotes
        |
        v
Python assigns IDs and writes the claim manifest
```

Python remains the workflow controller. Claude receives the submitted skill as untrusted text and is instructed to analyze rather than follow it. Every extracted claim must include a supporting quote that Python can locate in the submitted file. An ambiguity never pauses the program; Claude records it in `report_note` so a future report card can disclose it.

### Accepted input

The command accepts either:

- One UTF-8 text file, such as a catalog entry or recipe Markdown file.
- A skill directory containing a top-level `SKILL.md`; only that file is submitted in this prototype.

The current file-size limit is 256 KiB. Supporting files in a skill directory are not read or sent to Claude yet.

### Install and run

Python 3.11 or later is required. Create an environment and install the project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Configure the direct Claude API without placing the API key in a command or repository file. The model has no hard-coded default; use the model ID approved by company policy.

```powershell
$env:ANTHROPIC_API_KEY = "<your-api-key>"
$env:CLAUDE_MODEL = "<company-approved-claude-model-id>"
```

Start verification with a single file:

```powershell
sci-ai-verifier C:\path\to\recipe.md
```

Or start with a skill directory containing `SKILL.md`:

```powershell
sci-ai-verifier C:\path\to\skill-directory
```

By default, the manifest is written under `.verifier/runs/<run-id>/claim-manifest.json`. Use `--output` to select another path. Existing output files are not replaced unless `--force` is explicitly supplied.

The current stage produces this claim manifest:

```json
{
  "schema_version": "0.1",
  "manifest_id": "cmf-...",
  "claims": [
    {
      "claim_id": "clm-...",
      "statement": "The skill calculates monoisotopic mass from a molecular formula.",
      "scope": "Small molecules represented by molecular formula",
      "expected_behavior": "Return the corresponding monoisotopic mass.",
      "source_quote": "Calculate the monoisotopic mass from a molecular formula.",
      "report_note": ""
    }
  ]
}
```

Run the offline test suite without calling Claude:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Core principles

- Scientific correctness is separate from software functionality.
- Every claim must be evaluated against explicit evidence requirements.
- Every decision gate must include both a success path and a failure path.
- A missing dataset, inadequate test set, or failed audit must never silently become a pass.
- If the requested verification grade cannot be supported, the workflow returns to the requester to ask for a lower grade or revised scope.
- A grade is not lowered without requester approval.
- A result is published only after its evaluator, resources, evaluation bundle, and evaluation plan have been validated.

## Verification workflow

```mermaid
flowchart TD
    A["Scientific skill or recipe"] --> B["Profile the skill"]
    B --> C["Create claim manifest<br/>claim, claim ID, scope, priority, risk"]
    C --> D["Route each atomic claim"]

    D --> E{"Registered evaluator<br/>already exists?"}

    E -- Yes --> F["Create registered evaluation plan<br/>grade, evaluator, required evidence, budget"]
    E -- No --> G["Create target evaluation plan<br/>target grade, evaluator type,<br/>required evidence, budget"]

    G --> H["Acquire target datasets<br/>and evaluation resources"]
    H --> I{"Required dataset or<br/>resource found?"}

    I -- No --> R["Return to requester<br/>Explain why the requested grade is unsupported<br/>Ask for a lower grade or revised scope"]
    I -- Yes --> J["Version and register resources"]
    J --> K["Build and validate evaluation cases<br/>Add, edit, or delete cases"]
    K --> L{"Are the dataset and cases sufficient<br/>to test the claim at the target grade?"}

    L -- No --> R
    L -- Yes --> M["Create reusable evaluation bundle<br/>bundle.yaml, cases.json, expected.json"]
    M --> N["Register the new evaluator"]
    N --> D

    F --> O{"Does the evaluation-plan audit pass?<br/>Use-case fairness<br/>Test-case adequacy and efficiency<br/>Governance"}
    O -- No --> R
    O -- Yes --> P["Execute evaluator"]
    P --> Q["Publish claim-level result<br/>with its supported grade and evidence"]

    R --> S{"Requester approves a lower grade<br/>or revised scope?"}
    S -- Yes --> T["Update target grade or scope"]
    T --> D
    S -- No --> U["Record the claim as unverifiable<br/>at the requested grade<br/>Do not publish a passing result"]
```

## Workflow stages

### 1. Profile

Read the skill or recipe and decompose it into atomic, testable scientific claims. Record each claim's scope, priority, and risk in a claim manifest.

### 2. Route

Determine whether a registered evaluator already exists for each claim.

- If an evaluator exists, create a concrete evaluation plan using its supported grade, evidence requirements, test budget, and execution method.
- If no evaluator exists, describe the target evaluator and the grade it is intended to support, then continue to resource acquisition.

### 3. Acquire

Search for suitable datasets, standards, reference calculations, expert annotations, or other evaluation resources. Record their origin, version, and scientific domain.

If the required resources cannot be found, return to the requester. Explain what evidence is missing and ask whether the claim should be evaluated at a lower grade or with a narrower scope.

### 4. Build and validate

Construct evaluation cases from the acquired resources. Cases may be added, edited, or removed while validating whether they adequately test the claim.

If the cases are insufficient for the target grade, return to the requester rather than overstating the result. If they are sufficient, package them as a reusable evaluation bundle and register the resulting evaluator.

### 5. Audit

Audit the evaluation plan before execution. The audit considers:

- Whether the use cases are fair and representative.
- Whether the cases provide adequate and efficient coverage.
- Whether governance and provenance requirements are satisfied.

A failed audit returns to the requester for a revised plan, revised scope, or lower-grade decision.

### 6. Execute and publish

Execute only an audited evaluation plan. Publish the claim-level result together with its supported grade, evidence, evaluator identity, resource versions, and evaluation budget.

## Repository structure

The repository separates reusable verifier software from reusable scientific assets. Information produced while verifying an individual skill does not belong in `src/` or automatically enter the shared registry.

```text
sci-ai-verifier/
├── README.md
├── AGENT.md
├── pyproject.toml
├── src/
│   └── sci_ai_verifier/
│       ├── __main__.py
│       ├── cli.py
│       ├── ingest.py
│       ├── models.py
│       ├── claims.py
│       └── adapters/
│           └── claude.py
├── evaluators/
├── registry/
│   ├── resources/
│   └── bundles/
├── policies/
├── tests/
└── docs/
```

Only skill ingestion and claim-manifest construction are implemented at this stage. The evaluator, registry, policy, and documentation directories remain reserved for later workflow slices.

### `src/sci_ai_verifier/`

Contains the generic verifier application. The current files implement the command-line interface, skill ingestion, typed claim artifacts, claim validation and ID assignment, and the Claude boundary. Later workflow slices may add registry access, evaluation execution, and reporting.

This directory contains reusable program code only. It must not accumulate claim manifests, datasets, reports, or other information from every submitted skill.

### `src/sci_ai_verifier/adapters/`

Contains integrations for external systems. The current Claude adapter requests schema-constrained JSON from the Claude Messages API and converts it into extracted claim models. Future adapters may cover other skill formats, resource providers, and evaluator execution environments.

### `evaluators/`

Contains reusable scientific evaluator implementations. An evaluator should represent a scientific test capability that can be applied to compatible claims from multiple skills.

An evaluator is added only when a new reusable evaluation capability is intentionally developed. It is not created automatically for every submitted skill.

### `registry/resources/`

Contains small metadata records describing reusable datasets, standards, reference calculations, gold labels, models, or other scientific resources.

Large resource payloads must not be stored directly in this directory. A resource record should reference the payload's source or managed storage location and record its version, digest, license, access restrictions, and scientific scope.

### `registry/bundles/`

Contains reusable evaluation-bundle definitions. A bundle connects an evaluator with compatible resources, cases, and expected criteria for a scientific claim type.

Bundles belong to a scientific testing capability rather than to the first skill that needed them.

### `policies/`

Contains project-level rules such as grade definitions, retention decisions, resource licensing requirements, and evaluation-plan audit requirements.

### `tests/`

Contains software tests for the verifier and its evaluator integrations. Scientific evaluation cases belong to reusable bundles or managed resource storage rather than being mixed with application unit tests.

### `docs/`

Contains architecture decisions, contributor guidance, resource and evaluator authoring instructions, and descriptions of the verifier's public artifact formats.

## Per-skill runtime information

When a skill is submitted, its temporary information should be isolated in a Git-ignored runtime workspace rather than stored under `src/`:

```text
.verifier/
├── cache/
├── runs/<run-id>/
├── store/
└── index.sqlite
```

This runtime structure has not been created yet. During a future verification run it may contain the submitted skill snapshot, claim manifest, evaluation plan, downloaded resources, working files, and result package.

After the run:

1. Return the verification result to the requester.
2. Promote only reviewed, genuinely reusable evaluators, resources, or bundles into the shared project structure.
3. Retain the minimum provenance required for published results.
4. Delete the remaining temporary workspace.

Nothing should enter the shared registry merely because it appeared during a run.

## Artifact schemas

The project has not created a separate `schemas/` directory yet. For the initial Python implementation, claim, resource, evaluator, bundle, run-lock, and verification-result structures should have one source of truth in typed application models. Standalone JSON Schemas can be generated later if external tools need language-neutral validation.

## Evidence grading rubric

The evidence grade measures the strength of the verification evidence, not whether the skill passed. Each atomic claim receives its own evidence grade, result status, and coverage statement.

| Evidence grade | Minimum evidence standard | Permitted conclusion | Example skill claim commonly assessable at this grade |
|---|---|---|---|
| **A - Direct validation** | A fit-for-purpose scientific oracle or ground truth; independent of the skill where applicable; traceable or mathematically exact; representative cases; predefined tolerances; uncertainty and provenance recorded | The claim is validated or refuted within the stated scope, conditions, and tolerances | "The skill calculates a compound's monoisotopic mass from its molecular formula." |
| **B - External validation** | An independent curated benchmark, external replication, qualified reference implementation, or independently produced annotations; predefined criteria and a reproducible procedure; coverage or traceability is materially limited | The claim is supported or refuted on the tested benchmark; generalization beyond its coverage is not established | "The skill predicts a protein's subcellular localization from its amino-acid sequence." |
| **C - Indirect validation** | Scientifically justified indirect evidence such as genuinely independent tool agreement, invariants, conservation laws, metamorphic relations, property tests, or simulations; preferably multiple distinct checks; no adequate direct oracle | The behavior is consistent or inconsistent with expected scientific properties; direct scientific accuracy is not established | "The skill balances and normalizes chemical reactions while preserving atom count and net charge." |
| **D - Documentary assessment** | Structured human or agent review against cited sources and a bounded rubric; the citations support the conclusion; no execution against scientific ground truth | The claim is documented, entailed, or consistent with the supplied sources; scientific performance remains unverified | "The skill recommends experimental assay conditions and cites the supporting protocols." |
| **U - Unverified** | No acceptable scientific evidence; ungrounded judgment, self-consistency, smoke tests, installation tests, or operational execution only | No scientific conclusion is permitted; only operational behavior may be reported | "The skill accepts its documented input and produces schema-valid output without failing." |

The skill-claim examples show common matches, not automatic grade assignments. The same claim may be assessed at different grades depending on the available oracle, independence, scientific validity, coverage, uncertainty, and relationship between the evidence and the exact claim.

A claim result should keep these dimensions separate:

```yaml
status: pass | fail | inconclusive
evidence_grade: A | B | C | D | U
coverage:
  tested_cases: 120
  included_scope:
    - human proteins
  excluded_scope:
    - protein complexes
```

For example, `status: fail` with `evidence_grade: A` is strong evidence that the claim is incorrect within the tested scope. Conversely, `status: pass` with `evidence_grade: D` establishes documentary consistency only, not scientific accuracy.
