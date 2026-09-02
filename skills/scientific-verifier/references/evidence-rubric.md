# Evidence Grading Rubric

The evidence grade measures the strength and independence of the scientific verification evidence. It does not indicate whether the claim passed.

Every evaluated claim keeps three questions separate:

1. What was the result: `pass`, `fail`, or `inconclusive`?
2. How strong was the evidence: A, B, C, D, or U?
3. How much AI judgment influenced orchestration, evidence, and the final verdict?

## Rubric

| Grade | Minimum evidence standard | AI involvement permitted in the verdict | Permitted conclusion | Example skill claim commonly assessable at this grade |
|---|---|---|---|---|
| **A - Direct validation** | A fit-for-purpose scientific oracle or ground truth; independent of the skill where applicable; traceable or mathematically exact; representative cases; predefined tolerances; uncertainty and provenance recorded | **No AI judgment in scoring or the verdict.** Claude may orchestrate, select an already justified plan, and explain deterministic results. | The claim is validated or refuted within the stated scope, conditions, and tolerances. | "The skill calculates a compound's monoisotopic mass from its molecular formula." |
| **B - External validation** | An independent curated benchmark, external replication, qualified reference implementation, or independently produced annotations; predefined criteria and a reproducible procedure; coverage or traceability is materially limited | **Normally no AI judgment in scoring.** Limited AI may map fields or explain coverage, but machine-readable labels or bounded external criteria determine the verdict. | The claim is supported or refuted on the tested benchmark; generalization beyond its coverage is not established. | "The skill predicts a protein's subcellular localization from its amino-acid sequence." |
| **C - Indirect validation** | Scientifically justified indirect evidence such as independent-tool agreement, invariants, conservation laws, metamorphic relations, property tests, or simulations; preferably multiple distinct checks; no adequate direct oracle | **Limited AI judgment may design or select checks.** The actual property checks, simulations, or comparisons and their scoring must be reproducible outside AI judgment. | The behavior is consistent or inconsistent with expected scientific properties; direct scientific accuracy is not established. | "The skill balances and normalizes chemical reactions while preserving atom count and net charge." |
| **D - Documentary assessment** | Structured review against cited sources and a bounded rubric; the citations support the conclusion; no execution against scientific ground truth | **AI or human judgment is primary and must be disclosed.** The rubric, citations, and reasoning boundary must be recorded. | The claim is documented, entailed, or consistent with supplied sources; scientific performance remains unverified. | "The skill recommends experimental assay conditions and cites the supporting protocols." |
| **U - Unverified** | No acceptable scientific evidence; ungrounded judgment, self-consistency, smoke tests, installation tests, or operational execution only | AI may describe operational behavior but **no scientific verdict is allowed**. | No scientific conclusion is permitted. | "The skill accepts its documented input and produces schema-valid output without failing." |

The examples are common matches rather than automatic assignments. The same claim may receive different grades depending on the available oracle, independence, scientific validity, coverage, uncertainty, and relationship between evidence and the exact claim.

## Gold-standard preference

The verifier should first seek an A-grade design where the submitted skill's output can be compared with an independent expected answer using deterministic code. A dataset with one column that provides the expected answer from the remaining input columns can support A when:

- The expected-answer column is scientifically valid for the claim.
- It is independent of the submitted skill.
- Inputs and expected answers are separated during execution.
- Coverage is representative of the stated scope.
- Tolerances and comparison rules are predefined.
- Dataset provenance and uncertainty are recorded.

If those conditions are weaker, the same dataset may support only B or a lower grade.

## AI-involvement disclosure

Every claim result records AI involvement separately for:

- `orchestration`: workflow planning, tool selection, and recovery.
- `evidence_generation`: annotations, expected answers, case selection, or transformations influenced by AI.
- `verdict`: whether AI judgment directly influenced pass, fail, or inconclusive.

Claude orchestration alone does not lower an otherwise valid A-grade result. AI-generated expected answers or AI judgment in scoring do.

## Grade selection and downgrade

- Assign the strongest grade actually supported, never the intended or requested grade by default.
- A registered evaluator's grade is a ceiling, not a guarantee for every plan or dataset.
- Missing coverage, weak independence, uncertain provenance, leakage, or unsupported tolerances lower the grade ceiling.
- When target-grade evidence is unavailable, automatically attempt the next supportable grade and record the downgrade reason.
- When the user explicitly requires a minimum grade, label any lower-grade result as not satisfying that requirement.
- When no acceptable scientific evidence exists, assign U and make no scientific claim.

## Result interpretation

```yaml
status: pass | fail | inconclusive
evidence_grade: A | B | C | D | U
requested_grade: A | B | C | D | U | not_specified
coverage:
  tested_cases: 120
  included_scope:
    - human proteins
  excluded_scope:
    - protein complexes
ai_involvement:
  orchestration: true
  evidence_generation: false
  verdict: false
```

An A-grade failure is strong evidence that the claim is incorrect within the tested scope. A D-grade pass establishes documentary consistency only, not scientific accuracy. U never supports a scientific pass or fail conclusion.
