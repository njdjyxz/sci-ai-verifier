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

The plan fixes the subject model, its generation settings, the trial count `n`, the deterministic trial-aggregation rule, and the `trial_grade_policy` before execution. Python first runs the subject with expected answers withheld, then scores each trial with the audited evaluator, then aggregates the scored trials into per-case outcomes and the claim decision. Raw outputs are not aggregated before scoring. These fixed rules make an A-through-C decision reproducible given the recorded trial set; recording model settings does not guarantee that a non-deterministic subject will generate identical outputs again.

Three consequences for grading:

- **`n = 1` against a non-deterministic subject caps the grade at C.** A single sample cannot distinguish a skill that is right from one that is sometimes right, and a claim of direct validation from one observation is a claim the evidence does not support. A deterministic subject with a fixed entry point is unaffected and uses `n = 1` legitimately.
- **Exceeding audited agreement or coverage limits lowers the ceiling.** The permitted variation depends on the claim and is fixed by the audited policy, not by a universal numerical cutoff. Agreement measures consistency of scored evidence, not correctness: unanimous failure can support the same evidence grade as unanimous success when the other evidence requirements are equal. Passing most trials is not interchangeable with passing every trial; the recorded observations and audited rules determine what can be concluded.
- **Changing the subject model invalidates the result, not just the audit.** A grade earned on one model is evidence about that model running that skill. Reporting it as a property of the skill alone overstates it, so the subject model appears in the result and in the report card.

The aggregation rule is chosen from the claim. A claim that a calculation is correct is not served by a majority rule, since being right most of the time is the thing that claim denies. A claim about typical behavior is not served by requiring unanimity. Choosing the rule after seeing the trials is not grading; it is fitting the rule to the answer, and the audit rejects a plan that leaves it open.

### Audited trial-grade policy

`trial_grade_policy` names an exact policy identity, version, and digest supplied by the approved reviewed harness, plus parameters restricted to that harness's declared bounds. A registered evaluator retains this harness-policy reference. The policy's scientific justification and its applicability to the claim are audited before execution; neither the verifier agent nor execution may invent a policy or tune its parameters after observing results.

The policy defines total eligibility predicates for A, B, and C. Each predicate combines the applicable rubric requirements with the audited trial-count, agreement, coverage, and invalid-observation requirements. Unsupported grades have an explicitly false predicate. The contract must specify:

- What agreement measures over the scored trials, including ties, numerical boundary equality, and mixed `pass`, `fail`, and `inconclusive` outcomes.
- The denominators used for trial and case coverage, the treatment of scientifically invalid outputs or cases, and the reduction from per-case evidence to claim-level eligibility. Invalid observations cannot silently disappear from counts or denominators.
- Every supported trial count, including the C ceiling for `n = 1` with a non-deterministic subject, and the distinction between requested, attempted, obtained, evaluated, invalid, and missing trials.
- Explicit behavior for zero usable cases or zero scientifically evaluable trials: no A-through-C grade is eligible. An initially empty evaluation bundle fails audit rather than running.
- An explicit default, `no_supported_execution_grade`, when no A-through-C eligibility predicate is satisfied. There must be no uncovered observation pattern; simultaneous eligibility for several grades is resolved by choosing the strongest eligible grade no higher than the planned and audited ceilings.

The strongest eligible grade is Python's authoritative `achieved_grade_ceiling`. A downgrade must still satisfy that grade's rubric; it is not merely changing an A label to B or C. Execution records `grade_policy_ref`, `grade_limit_reasons`, trial counts, per-trial scores and decisions, and per-case agreement and coverage alongside that ceiling. Verdict rules remain separate from grade eligibility, so evidence against a claim is not weakened merely because the claim failed.

Missing trials caused by runner, provider, evaluator, or other operational failures use bounded execution retries and then `operational_failure`; they are not scientifically invalid observations, a scientific `fail`, or grounds for assigning U. For a completed scientific evaluation with `no_supported_execution_grade`, execution returns `lower_grade_required`, `achieved_grade_ceiling: null`, and `next_target_grade: D`. The claim returns to planning and capability selection to attempt documentary evidence under a separate audited plan. This outcome does not authorize a D result or bypass that assessment. U is reached only through the existing no-acceptable-evidence paths after no grade A through D is supportable.

## AI-involvement disclosure

Every claim result records AI involvement separately for:

- `orchestration`: workflow planning, tool selection, and recovery.
- `evidence_generation`: annotations, expected answers, case selection, or transformations influenced by AI.
- `verdict`: whether AI judgment directly influenced pass, fail, or inconclusive.

Verifier-agent orchestration alone does not lower an otherwise valid A-grade result. AI-generated expected answers or AI judgment in scoring do.

The subject model is not `evidence_generation`. It produces the outputs being tested, which is the thing under examination, not evidence about it; if it counted, no model-based skill could exceed grade D and the system would have nothing to say. What matters is whether AI produced the *expected answers*, selected the cases, or decided the verdict. The subject model is disclosed in its own field so a reader can see what was tested without confusing it with what did the testing.

## Verdict authority

The audited plan defines how invalid cases, coverage shortfalls, tolerances, and decision thresholds map to `pass`, `fail`, or `inconclusive` before execution.

Documentary-only D does not execute the submitted skill, so it does not require an installed subject runner. Its plan and artifacts mark subject runner/model, trial count, aggregation, and trial-grade policy `not_applicable`. An approved documentary harness, bounded evidence packet/rubric, and independent assessment remain required; missing assessor infrastructure is not missing scientific evidence.

- For grades A through C, `execute_evaluation_plan` returns `completed_deterministic_decision` with the authoritative status and `achieved_grade_ceiling` produced by the audited rules, plus `grade_policy_ref` and `grade_limit_reasons`. The verifier agent may explain them but may not select, revise, or override them. `commit_claim_result` copies the exact strongest supported grade and status; caller-supplied values must be omitted or equal those execution values. `lower_grade_required` is a replanning outcome and cannot be committed as an evaluated result.
- For grade D, `execute_evaluation_plan` obtains a completed assessment through a runner-provisioned independent assessor meeting the audited documentary plan's assessor boundary. The host selects and verifies the assessor; the planner cannot invent its identity. The assessor is an identified human or separate assessor session given only the bounded judgment packet, cited evidence, and audited rubric, not the planning conversation. `documentary_assessment_ready` means that this assessment has completed and its identity, independence, rubric findings, status, and provenance are recorded. The planning session never assesses its own packet, and result commit preserves the recorded assessment rather than accepting a new planning-agent judgment. If no eligible independent assessor is available, or assessment cannot complete within the runner's bounded limits, `assessor_unavailable` records a terminal claim-scoped operational outcome before result commit, with no scientific status. It does not justify either D or U.
- Grade U always has `status: inconclusive`. `pass` or `fail` with grade U is invalid.

Operational completion, schema validity, evaluator crashes, unavailable tools, and exhausted runtime limits never determine a scientific status.

## Grade selection and downgrade

- Assign the strongest grade actually supported, never the intended or requested grade by default.
- A registered evaluator's grade is a ceiling, not a guarantee for every plan or dataset.
- Missing coverage, weak independence, uncertain provenance, leakage, unsupported tolerances, or failure to meet the audited trial-count, agreement, or coverage requirements lower the grade ceiling. Trial-related limits are computed by the fixed `trial_grade_policy`, not inferred by the verifier agent after execution.
- When target-grade evidence is unavailable, automatically attempt the next supportable grade and record the downgrade reason.
- When the user explicitly requires a minimum grade, label any lower-grade result as not satisfying that requirement.
- When no acceptable evidence supports any grade A through D, assign U through the workflow's no-acceptable-evidence path and make no scientific claim. Failure to support A through C does not skip the documentary-evidence attempt; unavailable implementation or an unavailable assessor remains an operational outcome, not U.
- Before lowering a target plan, reconsider registered evaluators that support the lower grade so an existing capability is not rebuilt unnecessarily.

## Result interpretation

This schematic shows the recorded fields, not a numerical threshold policy or an evaluated claim:

```yaml
status: pass | fail | inconclusive
evidence_grade: A | B | C
requested_grade: A | B | C | D | U | not_specified
achieved_grade_ceiling: <authoritative A, B, or C from execution>
grade_policy_ref: <reviewed policy identity, version, and digest>
grade_limit_reasons: <recorded reasons, or an empty list>
coverage:
  tested_cases: <recorded count>
  included_scope: <audited scope>
  excluded_scope: <recorded exclusions>
subject:
  subject_runner: <approved runner identity and version>
  subject_model: <exact model id and version>
  trial_count: <audited count per case>
  aggregation_rule: <audited rule identity>
  case_trial_agreement: <recorded per-case summaries and denominators>
ai_involvement:
  orchestration: true
  evidence_generation: false
  verdict: false
```

An A-grade failure is strong evidence that the claim is incorrect within the tested scope. A D-grade pass establishes documentary consistency only, not scientific accuracy. U is valid only with `inconclusive` and never supports a scientific pass or fail conclusion.
