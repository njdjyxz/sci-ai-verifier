# Evidence Grading Rubric

The evidence grade measures the strength and independence of the scientific verification evidence. It does not indicate whether the claim passed, and it is not an endorsement by anyone.

Read the grade as a statement about where the evidence came from. A high grade means the answers the skill was checked against came from a gold-standard source outside the verifier. A low grade means AI judgment supplied more of the test design or the conclusion. The grade therefore also tells the verifier what to go looking for: seek the strongest evidence the claim allows, then report honestly how strong it turned out to be.

No human sign-off assigns a grade. The verifier proposes the grade its design supports, the runner checks that proposal against facts it recorded itself, and an independent critique session can lower it. That settlement is the grade.

Every evaluated claim keeps six questions separate. No answer may overwrite another:

1. **Grade.** How good was the reference the skill was checked against: A, B, C, D, or U?
2. **Accuracy.** How often did the skill's output match the expected answer?
3. **Consistency.** Did repeated trials of the same case agree with each other?
4. **Completeness.** How much of the planned trial set actually ran?
5. **Status.** Does the claim hold: `pass`, `fail`, `inconclusive`, or withheld?
6. **AI involvement.** How much AI judgment influenced orchestration, evidence, and the verdict?

The grade answers question 1 **only**. It is a statement about the reference and the test
bundle built from it, both of which are known before any trial runs. It must never move
because of how the skill behaved or because something in the runner broke. A skill that
fails every case against a gold-standard oracle keeps grade A: the evidence is exactly as
strong, it simply refutes the claim. Behavioural facts belong to accuracy and consistency;
operational facts belong to completeness and to the recorded fault.

Accuracy and consistency are not symmetric. Consistency compares the skill against itself,
so it is meaningful even against a worthless reference. Accuracy compares the skill against
the reference, so it is only interpretable through the grade: an accuracy figure carried
next to a `U` grade measures nothing. A reader with all six answers in front of them can
tell these apart, which is why the card reports them side by side rather than folding them
into a single score. Any automated consumer that filters or promotes claims must read the
grade before it reads accuracy.

## Rubric

| Grade | Minimum evidence standard | AI involvement permitted in the verdict | Permitted conclusion | Example skill claim commonly assessable at this grade |
|---|---|---|---|---|
| **A - Direct validation** | A fit-for-purpose scientific oracle or ground truth; independent of the skill where applicable; traceable or mathematically exact; representative cases; predefined tolerances; uncertainty and provenance recorded | **No AI judgment in scoring or the verdict.** The verifier agent may orchestrate, select an already justified plan, and explain deterministic results. | The claim is validated or refuted within the stated scope, conditions, and tolerances. | "The skill calculates a compound's monoisotopic mass from its molecular formula." |
| **B - External validation** | An independent curated benchmark, external replication, qualified reference implementation, or independently produced annotations; predefined criteria and a reproducible procedure; coverage or traceability is materially limited | **Normally no AI judgment in scoring.** Limited AI may map fields or explain coverage, but machine-readable labels or bounded external criteria determine the verdict. | The claim is supported or refuted on the tested benchmark; generalization beyond its coverage is not established. | "The skill predicts a protein's subcellular localization from its amino-acid sequence." |
| **C - Indirect validation** | Scientifically justified indirect evidence such as independent-tool agreement, invariants, conservation laws, metamorphic relations, property tests, or simulations; preferably multiple distinct checks; no adequate direct oracle | **Limited AI judgment may design or select checks.** The actual property checks, simulations, or comparisons and their scoring must be reproducible outside AI judgment. | The behavior is consistent or inconsistent with expected scientific properties; direct scientific accuracy is not established. | "The skill balances and normalizes chemical reactions while preserving atom count and net charge." |
| **D - Documentary assessment** | Structured review against cited sources and a bounded rubric; the citations support the conclusion; no execution against scientific ground truth | **AI or human judgment is primary and must be disclosed.** The rubric, citations, and reasoning boundary must be recorded. | The claim is documented, entailed, or consistent with supplied sources; scientific performance remains unverified. | "The skill recommends experimental assay conditions and cites the supporting protocols." |
| **U - Unverified** | No acceptable scientific evidence; ungrounded judgment, self-consistency, smoke tests, installation tests, or operational execution only | AI may describe operational behavior but **no scientific verdict is allowed**. | No scientific conclusion is permitted. | "The skill accepts its documented input and produces schema-valid output without failing." |

The examples are common matches rather than automatic assignments. The same claim may receive different grades depending on the available oracle, independence, scientific validity, coverage, uncertainty, and relationship between evidence and the exact claim.

**A case must test what its claim asserts — no less, and no more.**

*No less.* A claim about what a function *does* is not tested by a case asking what it is *named*. Naming and spelling cases are legitimate where the claim is itself about an API surface; they are recitation where the claim is about behaviour, meaning or a numeric relationship.

*No more.* A case must not reach past the claim to a consequence or fact the claim never states. A claim that pIC50 is the negative base-10 logarithm of the molar IC50 is not tested by a case asking which direction of the scale means more potent. That is in neither the claim nor the skill, so a subject faithfully applying the skill has nothing to answer from: it either falls back on the base model's own knowledge, which credits the skill for something the model already knew, or it declines, which fails a correct skill. Either way the case measures something other than the claim. A case framed as "which statement does a reference make" invites exactly this, because a subject running the skill reads "a reference" as its own loaded material.

A case that recites, or that reaches beyond the claim, does not count toward the representative cases grade A requires, and a design resting on such cases does not support grade A. This is a fitness judgment rather than a computable property: once quoted from a source, a function name, a scientific value and an unasserted consequence are all the same shape, so Python counts cases and cannot weigh them. The critique answers it as a named criterion of its rubric, and lowering the grade is what returns the design to the planner for better cases.

## Negotiating the grade

Grading is a loop, not a label chosen at the end:

1. **Seek strong evidence.** Start from the A-grade question: can the skill's output be compared with an independently obtained expected answer using deterministic code? Find and retrieve the sources that would make that possible before settling for anything weaker.
2. **Propose the ceiling.** Every proposal must be the strongest grade the runner's own recorded facts support for that design. There is exactly one exception, in step 4. Aiming below the ceiling is refused, because understating the evidence misreports it just as badly as overclaiming; and "no suitable oracle exists for a stronger grade" is not a reason to aim low — it is already what the ceiling computes. Justify the proposal: where the oracle came from and how independent it is, what the cases cover and which of them test what the claim asserts rather than what it is named, what the tolerance rests on, what is uncertain, and what would be needed to go higher.
3. **Critique its suitability.** A fresh session that never saw the planning judges whether that evidence is fit for this exact claim at that grade. It receives the concerns earlier reviewers raised about earlier versions of the design, so it can check whether they are now answered, but never their grades: a reviewer shown a previous verdict has an easy answer available, which is the anchoring the fresh session exists to avoid.
4. **Revise, or accept.** When the critique supports less, there are two legal moves. Strengthen the evidence — a more authoritative source, cases that cover the stated scope, a tighter comparison — and propose the new ceiling; that earns another round. Or accept the grade this exact design was critiqued at, which settles immediately and spends no further session. Re-proposing a grade on an unchanged design is refused without spending a round, so the loop cannot spin.
5. **Settle at the highest justified grade.** The settled grade is the weakest of the proposal, the runner's ceiling and the critique's verdict. On the last permitted round the critique's grade is settled rather than offered for revision, and the grade always describes the plan that will actually execute, not a stronger design that was discarded.

Proposing again is the normal path, not a failure. What is not permitted is arguing the critique into agreement, restating a design without changing it, or treating a lowered grade as a reason to abandon the claim. A critique concluding that the design supports no grade is accepted the same way: the plan still executes and produces ungraded comparison evidence, and the claim continues to the documentary path.

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

Three consequences, and only the first touches the grade:

- **A planned `n = 1` against a non-deterministic subject caps the grade at C.** This is a fact about the test bundle, fixed before execution, so it belongs to the grade. A single sample cannot distinguish a skill that is right from one that is sometimes right, and a claim of direct validation from one observation is a claim the evidence does not support. A deterministic subject with a fixed entry point is unaffected and uses `n = 1` legitimately; in a profile whose subject is always a fresh model session, that exemption is unreachable and the planned trial count must be at least three.
- **Observed disagreement between trials never lowers the grade.** Agreement measures consistency of scored evidence, not the quality of the reference, and nothing about the reference changed when the subject wobbled. Disagreement is reported as `consistency` and feeds the audited aggregation rule, which decides `status`. Under a unanimity rule a split case makes the claim `fail`; under a majority rule it may still `pass`. Either way a verdict is produced: a flaky skill is a finding, not an absence of one. Unanimous failure supports the same grade as unanimous success when the other evidence requirements are equal.
- **Changing the subject model withholds the verdict without touching the grade.** A verdict earned on one model is evidence about that model running that skill, so a trial set containing two models has no single subject to describe and `status` is withheld as `unattributable_observations`. The reference is unaffected and keeps its grade. The observed models appear in the result and in the report card.

A runner fault that truncates a trial set is treated the same way: the surviving observations are kept and reported with their `completeness` denominator, and `status` is withheld rather than computed from a sample nobody audited. Where the surviving cases fall below the audited minimum, the withholding reason is `incomplete_coverage`, not `unattributable_observations` — the observations were fine, there were simply too few cases left to answer the question that was reviewed.

The aggregation rule is chosen from the claim. A claim that a calculation is correct is not served by a majority rule, since being right most of the time is the thing that claim denies. A claim about typical behavior is not served by requiring unanimity. Choosing the rule after seeing the trials is not grading; it is fitting the rule to the answer, and the audit rejects a plan that leaves it open.

### Audited trial-grade policy

`trial_grade_policy` names an exact policy identity, version, and digest installed in the runner, plus parameters restricted to its declared bounds. A registered evaluator retains this policy reference. The policy's applicability to the claim is settled before execution; neither the verifier agent nor execution may invent a policy or tune its parameters after observing results.

The policy defines total eligibility predicates for A, B, and C over the **reference and test-bundle facts only**: where the expected answers came from, how independent they are of the skill, whether they are token-exact in their source, how the comparison is scored, the number of distinct cases, and the planned trial count. Every one of these is known before a trial runs, which is what makes the grade a statement about the evidence design rather than about the run. Unsupported grades have an explicitly false predicate. Simultaneous eligibility is resolved by choosing the strongest eligible grade no higher than the planned and audited ceilings; when none is satisfied the default is `no_supported_execution_grade`.

Observed trial outcomes are **not** inputs to those predicates. The contract must still specify, for the axes that do consume them:

- What agreement measures over the scored trials, including ties, numerical boundary equality, and mixed `pass`, `fail`, and `inconclusive` outcomes. This determines `consistency`, never the grade.
- The denominators used for trial and case coverage, the treatment of scientifically invalid outputs or cases, and the reduction from per-case evidence to a claim-level verdict. Invalid observations cannot silently disappear from counts or denominators.
- The distinction between requested, attempted, obtained, evaluated, invalid, and missing trials, which `completeness` reports.
- Explicit behaviour for zero usable cases or zero scientifically evaluable trials. An initially empty evaluation bundle fails audit rather than running.

The strongest eligible grade is Python's authoritative `achieved_grade_ceiling`. A downgrade must still satisfy that grade's rubric; it is not merely changing an A label to B or C. Execution records `grade_policy_ref`, `grade_limit_reasons`, `execution_limit_reasons`, trial counts, per-trial scores and decisions, and per-case agreement and coverage alongside that ceiling. The two reason lists are kept apart on purpose: `grade_limit_reasons` may name only facts about the reference and the test bundle, and anything behavioural or operational — disagreement between trials, retained invalid observations, a changed subject model — belongs in `execution_limit_reasons`. A reader must be able to tell a weak reference from a wobbling skill without inspecting the raw trials.

### Status

`status` answers whether the claim holds. It is one of `pass`, `fail`, `inconclusive`, or `null` with a recorded `status_withheld_reason`. It is evaluated in order, first match winning:

| # | Condition | Status |
| --- | --- | --- |
| 1 | grade is `U`, or no reference supports any execution grade | `null` — `no_reference_grade` |
| 2 | zero evaluable observations | `null` — `not_executed` |
| 3 | observations not attributable to one subject | `null` — `unattributable_observations` |
| 4 | usable cases below the audited minimum | `null` — `incomplete_coverage` |
| 5 | the audited aggregation rule is satisfied | `pass` |
| 6 | the audited aggregation rule is violated | `fail` |
| 7 | the rule is indeterminate on this evidence | `inconclusive` |

Only `U` gates status by way of the grade, and that dependency is definitional rather than qualitative: with no reference there is no expected answer, so the question has no value at all — not a weak one. Grades A through D never touch status. A D-grade claim may `pass` and an A-grade claim may `fail`.

The card records which `aggregation_rule` produced the verdict, because `fail` is uninterpretable without it: thirteen passes in fifteen trials is a `fail` under unanimity and a `pass` under a majority rule. Synthetic fixture runs withhold status for the same reason they stay ungraded.

`status` is a scientific verdict and never a report on whether the workflow completed. Redefining it so that a finished run yields `pass` was considered and rejected on 2026-09-21: it would print `status: pass` beside `accuracy: 0 of 15` for a skill that was reliably wrong, which is the single most dangerous misreading this card can produce and is the case the independence rule exists to prevent. Whether the process finished is already answered by `completeness`, by `fault`, and by `verification_complete` on the report.

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
- For grade D, `execute_evaluation_plan` obtains a completed assessment through a runner-provisioned independent assessor meeting the audited documentary plan's assessor boundary. The host selects and verifies the assessor; the planner cannot invent its identity. The assessor is a separate session given only the bounded judgment packet, cited evidence, and audited rubric, not the planning conversation. `documentary_assessment_ready` means that this assessment has completed and its identity, independence, rubric findings, status, and provenance are recorded. A completed assessment against the installed rubric is grade D on its own; no further sign-off is required, and none of it makes the conclusion more than documentary. The planning session never assesses its own packet, and result commit preserves the recorded assessment rather than accepting a new planning-agent judgment. If no eligible independent assessor is available, or assessment cannot complete within the runner's bounded limits, `assessor_unavailable` records a terminal claim-scoped operational outcome before result commit, with no scientific status. It does not justify either D or U.
- Grade U always has `status: inconclusive`. `pass` or `fail` with grade U is invalid.

Operational completion, schema validity, evaluator crashes, unavailable tools, and exhausted runtime limits never determine a scientific status.

## Grade selection and downgrade

- Assign the strongest grade actually supported: never the intended or requested grade by default, and never a weaker grade than the evidence earns.
- A registered evaluator's grade is a ceiling, not a guarantee for every plan or dataset.
- Missing coverage, weak independence, uncertain provenance, leakage, unsupported tolerances, or failure to meet the audited trial-count, agreement, or coverage requirements lower the grade ceiling. Trial-related limits are computed by the fixed `trial_grade_policy`, not inferred by the verifier agent after execution.
- When target-grade evidence is unavailable, automatically attempt the next supportable grade and record the downgrade reason.
- When the user explicitly requires a minimum grade, label any lower-grade result as not satisfying that requirement.
- When no acceptable evidence supports any grade A through D, assign U through the workflow's no-acceptable-evidence path and make no scientific claim. Failure to support A through C does not skip the documentary-evidence attempt; unavailable implementation or an unavailable assessor remains an operational outcome, not U.
- Before lowering a target plan, reconsider registered evaluators that support the lower grade so an existing capability is not rebuilt unnecessarily.
- A grade is never conferred by a person approving it and never withheld because nobody has. Absent approval is not an evidence limit; absent evidence is.

## Result interpretation

This schematic shows the recorded claim-result fields, not a numerical threshold policy or an evaluated claim. The plan audit separately records `evidence_ceiling`, the strongest grade the runner's own facts support, its limiting reasons, and the independent critique's supported grade, findings and objections:

```yaml
status: pass | fail | inconclusive
evidence_grade: A | B | C
requested_grade: A | B | C | D | U | not_specified
achieved_grade_ceiling: <authoritative A, B, or C from execution>
proposed_grade: <the grade the planner proposed>
settled_ceiling: <the grade the negotiation settled on, copied from the plan audit>
grade_policy_ref: <installed policy identity, version, and digest>
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
