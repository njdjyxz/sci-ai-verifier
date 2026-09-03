# Evidence Grading Rubric

The evidence grade measures the strength and independence of the scientific verification evidence. It does not indicate whether the claim passed.

Every evaluated claim keeps three questions separate:

1. What was the result: `pass`, `fail`, or `inconclusive`?
2. How strong was the evidence: A, B, C, D, or U?
3. How much AI judgment influenced orchestration, evidence, and the final verdict?

## Rubric

| Grade | Minimum evidence standard | AI involvement permitted in the verdict | Permitted conclusion | Example skill claim commonly assessable at this grade |
|---|---|---|---|---|
| **A - Direct validation** | A fit-for-purpose scientific oracle or ground truth; independent of the skill where applicable; traceable or mathematically exact; representative cases; predefined tolerances; uncertainty and provenance recorded | **No AI judgment in scoring or the verdict.** The verifier agent may orchestrate, select an already justified plan, and explain deterministic results. | The claim is validated or refuted within the stated scope, conditions, and tolerances. | "The skill calculates a compound's monoisotopic mass from its molecular formula." |
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

## Subject non-determinism

Most submitted skills are instructions for a model. Running one twice can produce two different outputs, so a verdict is a statement about a sample, and the sample has to be described before the verdict means anything.

The plan fixes the subject model, its generation settings, the trial count `n`, and the deterministic rule that reduces a case's `n` trials to one per-case outcome, all before execution. Those four together are what make an A-through-C decision reproducible: the decision rules are deterministic given the trial set, and the subject-runner configuration is what makes the trial set repeatable.

Three consequences for grading:

- **`n = 1` against a non-deterministic subject caps the grade at C.** A single sample cannot distinguish a skill that is right from one that is sometimes right, and a claim of direct validation from one observation is a claim the evidence does not support. A deterministic subject with a fixed entry point is unaffected and uses `n = 1` legitimately.
- **Disagreement between trials lowers the ceiling.** A claim that satisfies its oracle on every trial is directly validated within its scope. A claim that satisfies it on most trials is evidence about a distribution, and the result says so. Observed agreement is recorded per case and reported; a bare pass that concealed heavy disagreement would misstate what was found.
- **Changing the subject model invalidates the result, not just the audit.** A grade earned on one model is evidence about that model running that skill. Reporting it as a property of the skill alone overstates it, so the subject model appears in the result and in the report card.

The aggregation rule is chosen from the claim. A claim that a calculation is correct is not served by a majority rule, since being right most of the time is the thing that claim denies. A claim about typical behavior is not served by requiring unanimity. Choosing the rule after seeing the trials is not grading; it is fitting the rule to the answer, and the audit rejects a plan that leaves it open.

## AI-involvement disclosure

Every claim result records AI involvement separately for:

- `orchestration`: workflow planning, tool selection, and recovery.
- `evidence_generation`: annotations, expected answers, case selection, or transformations influenced by AI.
- `verdict`: whether AI judgment directly influenced pass, fail, or inconclusive.

Verifier-agent orchestration alone does not lower an otherwise valid A-grade result. AI-generated expected answers or AI judgment in scoring do.

The subject model is not `evidence_generation`. It produces the outputs being tested, which is the thing under examination, not evidence about it; if it counted, no model-based skill could exceed grade D and the system would have nothing to say. What matters is whether AI produced the *expected answers*, selected the cases, or decided the verdict. The subject model is disclosed in its own field so a reader can see what was tested without confusing it with what did the testing.

## Verdict authority

The audited plan defines how invalid cases, coverage shortfalls, tolerances, and decision thresholds map to `pass`, `fail`, or `inconclusive` before execution.

- For grades A through C, `execute_evaluation_plan` returns the authoritative status produced by those deterministic rules. The verifier agent may explain it but may not select, revise, or override it. `commit_claim_result` rejects a different status.
- For grade D, an audited documentary-rubric harness may return a bounded judgment packet. The status is proposed only from that packet and rubric, and only by an assessor independent of the session that designed the plan and rubric: an identified human, or a separate assessor session given the packet and nothing else. The session that chose the evidence does not also grade it — that is the specific bias the D disclosure exists to let a reader discount, and it cannot be discounted if it is not separated. Where no independent assessor is available, the limitation is recorded and no D status is proposed. The provider, model or assessor identity, its independence from the planning session, cited evidence, and judgment boundary are all recorded.
- Grade U always has `status: inconclusive`. `pass` or `fail` with grade U is invalid.

Operational completion, schema validity, evaluator crashes, unavailable tools, and exhausted runtime limits never determine a scientific status.

## Grade selection and downgrade

- Assign the strongest grade actually supported, never the intended or requested grade by default.
- A registered evaluator's grade is a ceiling, not a guarantee for every plan or dataset.
- Missing coverage, weak independence, uncertain provenance, leakage, unsupported tolerances, a trial count too small for a non-deterministic subject, or unexplained disagreement between trials all lower the grade ceiling.
- When target-grade evidence is unavailable, automatically attempt the next supportable grade and record the downgrade reason.
- When the user explicitly requires a minimum grade, label any lower-grade result as not satisfying that requirement.
- When no acceptable scientific evidence exists, assign U and make no scientific claim.
- Before lowering a target plan, reconsider registered evaluators that support the lower grade so an existing capability is not rebuilt unnecessarily.

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
subject:
  subject_runner: model-skill-runner@3
  subject_model: <exact model id and version>
  trial_count: 5
  aggregation_rule: all_trials_satisfy_oracle
  case_trial_agreement: 117 unanimous, 3 split
ai_involvement:
  orchestration: true
  evidence_generation: false
  verdict: false
```

An A-grade failure is strong evidence that the claim is incorrect within the tested scope. A D-grade pass establishes documentary consistency only, not scientific accuracy. U is valid only with `inconclusive` and never supports a scientific pass or fail conclusion.
