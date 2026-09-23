"""Evidence-strength ceilings, the critique boundary and assessor limits; no live models."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault
from sci_ai_verifier.local_science import (GRADES,MAX_ROUNDS,POLICY_REF,audit,decide,evidence_ceiling,
                                           proposal_problem,weaker)
from sci_ai_verifier.documentary import (CRITIQUE_RUBRIC,RUBRIC,assess,critique,validate_assessment,
                                         validate_critique)
from sci_ai_verifier.local_evaluators import qualify,validate_spec
from sci_ai_verifier.local_candidates import METHOD_VERSION

RETRIEVED={"origin":"retrieved_public_https","url":"https://example.org/r","version":"1","license":"unknown"}


class CeilingTests(unittest.TestCase):
    def setUp(self):
        self.references={"r"+str(index):dict(RETRIEVED) for index in range(5)}
        self.candidate={"method":"numeric","method_version":METHOD_VERSION,"name":"Fixture",
            "scope":"Fixture scope","limitations":"Fixture","absolute_tolerance":"0.000001",
            "cases":[{"case_id":str(index),"input":str(index),"expected":str(index)+".0",
                      "reference_ref":"r"+str(index),"source_quote":"row "+str(index)+" is "+str(index)+".0 exactly",
                      "applicability":"row"} for index in range(5)]}

    def ceiling(self,trials=3,counted=None,**changes):
        candidate={**self.candidate,**changes}
        return evidence_ceiling(candidate,self.references,trials,counted)

    def test_retrieved_deterministic_three_trials_reaches_a(self):
        self.assertEqual(self.ceiling(),("A",[]))

    def test_a_needs_five_counting_cases_and_three_or_four_reach_only_b(self):
        for size in (3,4):
            with self.subTest(cases=size):
                grade,reasons=self.ceiling(cases=self.candidate["cases"][:size])
                self.assertEqual(grade,"B")
                self.assertEqual(reasons,["fewer_than_five_counting_cases"])

    def test_a_recognised_only_design_cannot_pass_c(self):
        """A `choice` design has no generated case, so an A-quality reference still gives C."""
        options=["alpha","beta","gamma","delta","none of these"]
        cases=[{**case,"expected":"1","options":options,"source_quote":"the answer is alpha here"}
               for case in self.candidate["cases"]]
        grade,reasons=self.ceiling(method="choice",cases=cases)
        self.assertEqual(grade,"C")
        self.assertEqual(reasons,["no_generated_case"])

    def test_only_counted_cases_enter_the_ceiling(self):
        """Run d87a6d5c: five cases, two of them counted, still graded A. The count now decides."""
        self.assertEqual(self.ceiling(counted=["0","1","2","3","4"])[0],"A")
        self.assertEqual(self.ceiling(counted=["0","1","2","3"])[0],"B")
        self.assertEqual(self.ceiling(counted=["0","1","2"])[0],"B")
        grade,reasons=self.ceiling(counted=["0","1"])
        self.assertIsNone(grade)
        self.assertIn("insufficient_distinct_cases",reasons)
        self.assertIsNone(self.ceiling(counted=[])[0])

    def test_operator_dataset_and_generated_scorer_cap_at_b(self):
        self.references["r0"]={**RETRIEVED,"origin":"operator_local_resource"}
        grade,reasons=self.ceiling()
        self.assertEqual(grade,"B")
        self.assertIn("expected_answers_not_independently_retrieved",reasons)
        self.references["r0"]=dict(RETRIEVED)
        grade,reasons=self.ceiling(method="python",controls_receipts=[{"passed":True}])
        self.assertEqual(grade,"B")
        self.assertIn("scoring_code_authored_by_planner",reasons)

    def test_single_trial_substring_and_unknown_origin_cap_at_c(self):
        self.assertEqual(self.ceiling(trials=1)[0],"C")
        self.assertIn("model_subject_trial_count_below_three",self.ceiling(trials=1)[1])
        cases=deepcopy(self.candidate["cases"])
        # "1.0" inside "21.09" is a substring, not an independent answer for this case.
        cases[0]["source_quote"]="row 0 is 21.09 total"
        cases[0]["expected"]="1.0"
        self.assertEqual(self.ceiling(cases=cases)[0],"C")
        self.references["r1"]={"url":"cached","version":"1","license":"unknown"}
        self.assertEqual(self.ceiling()[0],"C")

    def test_failed_controls_support_no_execution_grade(self):
        grade,reasons=self.ceiling(method="python",controls_receipts=[{"passed":False}])
        self.assertIsNone(grade)
        self.assertIn("comparison_not_deterministic",reasons)

    def test_only_the_ceiling_or_an_accepted_critique_grade_may_be_proposed(self):
        # The ceiling is always proposable; aiming below it is refused just like overclaiming.
        for grade in ("A","B","C"):
            self.assertIsNone(proposal_problem(grade,grade))
        self.assertEqual(proposal_problem("A","C"),"above_evidence_ceiling")
        self.assertEqual(proposal_problem("C","A"),"below_evidence_ceiling")
        self.assertEqual(proposal_problem("C",None),"no_supported_execution_grade")
        # A grade the last critique of this same design supported is the one exception.
        self.assertIsNone(proposal_problem("C","A",accepted="C"))
        self.assertEqual(proposal_problem("B","A",accepted="C"),"below_evidence_ceiling")
        with self.assertRaises(Fault) as caught:
            proposal_problem("D","A")
        self.assertEqual(caught.exception.code,"grade_proposal_invalid")

    def test_one_negotiation_round_per_rubric_grade(self):
        self.assertEqual(MAX_ROUNDS,len(GRADES))
        self.assertEqual(GRADES,("A","B","C","D","U"))

    def test_weaker_never_raises_a_grade(self):
        self.assertEqual(weaker("A","C"),"C")
        self.assertEqual(weaker("C","A"),"C")
        self.assertIsNone(weaker("A",None))


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.cases=[{"case_id":str(index)} for index in range(3)]
        self.selection={"trials_per_case":3,"target_grade":"A","source_digest":"b"*64,
                        "environment_digest":"c"*64,"oracle_independence":"retrieved","coverage":"three rows",
                        "tolerance_basis":"installed","uncertainty":"none stated",
                        "stronger_grade_considered":"A proposed"}
        self.audit={"settled_ceiling":"A","proposed_grade":"A","evidence_ceiling":"A",
                    "evidence_limits":[],"policy_ref":POLICY_REF}

    def rows(self,count,status="pass"):
        return [{"case_id":case["case_id"],"trial":trial,"comparison_status":status,"model_ids":["fixture-model"]}
                for case in self.cases for trial in range(1,count+1)]

    def test_unanimous_failure_and_success_receive_the_same_grade(self):
        for status in ("pass","fail"):
            result=decide(self.audit,self.rows(3,status),self.cases,3)
            self.assertEqual(result["evidence_grade"],"A")
            self.assertEqual(result["scientific_status"],status)
            self.assertEqual(result["observed_model_ids"],["fixture-model"])

    def test_no_settled_ceiling_and_synthetic_runs_stay_ungraded(self):
        for record,synthetic in (({**self.audit,"settled_ceiling":None,"evidence_ceiling":None},False),
                                 (self.audit,True)):
            result=decide(record,self.rows(3),self.cases,3,synthetic=synthetic)
            self.assertIsNone(result["evidence_grade"])
            self.assertIsNone(result["scientific_status"])
            self.assertEqual(result["next_target_grade"],"D")

    def test_settled_ceiling_is_the_grade_even_when_a_stronger_one_was_proposed(self):
        result=decide({**self.audit,"settled_ceiling":"C"},self.rows(3),self.cases,3)
        self.assertEqual(result["evidence_grade"],"C")
        self.assertEqual(result["proposed_grade"],"A")

    def test_missing_or_duplicate_trials_cannot_become_a_verdict(self):
        for rows in (self.rows(3)[:-1],self.rows(3)+self.rows(3)[:1]):
            with self.assertRaises(Fault):
                decide(self.audit,rows,self.cases,3)

    def test_disagreement_fails_the_claim_and_leaves_the_grade_alone(self):
        """The headline repair: a flaky skill is a recorded failure, not an absent result."""
        rows=self.rows(3)
        rows[0]["comparison_status"]="fail"
        result=decide(self.audit,rows,self.cases,3)
        self.assertEqual(result["evidence_grade"],"A")
        self.assertEqual(result["scientific_status"],"fail")
        self.assertIsNone(result["status_withheld_reason"])
        self.assertEqual(result["consistency"]["label"],"split")
        self.assertEqual(result["consistency"]["split_cases"],1)
        self.assertEqual(result["accuracy"],{"matched":8,"evaluated":9,"ratio":round(8/9,4)})
        self.assertIn("trial_agreement_below_policy",result["execution_limit_reasons"])
        self.assertNotIn("trial_agreement_below_policy",result["grade_limit_reasons"])

    def test_invalid_observations_are_inconclusive_and_keep_the_grade(self):
        rows=self.rows(3)
        rows[0]["comparison_status"]="invalid"
        result=decide(self.audit,rows,self.cases,3)
        self.assertEqual(result["evidence_grade"],"A")
        self.assertEqual(result["scientific_status"],"inconclusive")
        self.assertEqual(result["trial_counts"]["evaluated"],9)
        self.assertEqual(result["trial_counts"]["invalid"],1)
        self.assertIn("invalid_observations_retained",result["execution_limit_reasons"])
        self.assertNotIn("invalid_observations_retained",result["grade_limit_reasons"])

    def test_changed_observed_model_identity_withholds_the_verdict_not_the_grade(self):
        rows=self.rows(3)
        rows[0]["model_ids"]=["another-model"]
        result=decide(self.audit,rows,self.cases,3)
        self.assertEqual(result["evidence_grade"],"A")
        self.assertIsNone(result["scientific_status"])
        self.assertEqual(result["status_withheld_reason"],"unattributable_observations")
        self.assertIn("observed_model_identity_changed",result["execution_limit_reasons"])
        self.assertNotIn("observed_model_identity_changed",result["grade_limit_reasons"])

    def test_grade_limit_reasons_never_carry_behavioural_facts(self):
        """The grade reports the reference only; behaviour lives in the other list."""
        behavioural={"trial_agreement_below_policy","invalid_observations_retained",
                     "observed_model_identity_changed"}
        rows=self.rows(3)
        rows[0]["comparison_status"]="fail"
        rows[1]["comparison_status"]="invalid"
        rows[2]["model_ids"]=["another-model"]
        result=decide(self.audit,rows,self.cases,3)
        self.assertEqual(behavioural&set(result["grade_limit_reasons"]),set())
        self.assertEqual(behavioural,set(result["execution_limit_reasons"]))

    def test_unanimous_pass_records_every_axis(self):
        result=decide(self.audit,self.rows(3),self.cases,3)
        self.assertEqual(result["accuracy"],{"matched":9,"evaluated":9,"ratio":1.0})
        self.assertEqual(result["consistency"]["label"],"unanimous")
        self.assertEqual(result["consistency"]["overall_agreement"],1.0)
        self.assertEqual(result["completeness"],
                         {"obtained":9,"planned":9,"usable_cases":3,"planned_cases":3})
        self.assertEqual(result["aggregation_rule"],"unanimity")
        self.assertIsNone(result["fault"])

    def test_audit_records_the_critique_that_settled_the_grade(self):
        candidate={"method":"numeric","method_version":METHOD_VERSION,"name":"Fixture",
                   "scope":"s","limitations":"l","absolute_tolerance":"0.000001",
                   "cases":[{"case_id":str(i),"reference_ref":"r","expected":"1.0","source_quote":"is 1.0 exactly"}
                            for i in range(5)]}
        critique={"supported_grade":"C","findings":["f"]*len(CRITIQUE_RUBRIC["criteria"]),
                  "objections":["Three rows do not cover the stated scope."],"required_revisions":"Add cases."}
        record=audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,
                     {"r":dict(RETRIEVED)},critique=critique,rounds=2)
        self.assertEqual(record["proposed_grade"],"A")
        self.assertEqual(record["settled_ceiling"],"C")
        self.assertEqual(record["critique_rounds"],2)
        self.assertTrue(record["mechanically_accepted"])
        # A critique naming D is saying this execution plan supports no execution grade.
        documentary={**critique,"supported_grade":"D"}
        self.assertIsNone(audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,
                                {"r":dict(RETRIEVED)},critique=documentary,rounds=1)["settled_ceiling"])
        self.assertIsNone(audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,
                                {"r":dict(RETRIEVED)})["settled_ceiling"])

    def test_no_counted_case_reports_no_agreement_rather_than_unanimity(self):
        record={"settled_ceiling":None,"evidence_limits":[],"case_limits":["insufficient_distinct_cases"],
                "policy_ref":POLICY_REF,"proposed_grade":"A","evidence_ceiling":"A"}
        result=decide(record,[],[],3,synthetic=False)
        self.assertEqual(result["consistency"]["label"],"no_counted_cases")
        self.assertIsNone(result["evidence_grade"])
        self.assertIn("insufficient_distinct_cases",result["grade_limit_reasons"])

    def test_the_case_count_binds_a_critique_that_rejected_cases_but_supported_a(self):
        """The critique's letter cannot outrun its own verdicts; nor is its lower grade overridden."""
        candidate={"method":"numeric","method_version":METHOD_VERSION,"name":"Fixture",
                   "scope":"s","limitations":"l","absolute_tolerance":"0.000001",
                   "cases":[{"case_id":str(i),"reference_ref":"r","expected":"1.0","source_quote":"is 1.0 exactly"}
                            for i in range(5)]}
        verdicts=[{"case_id":str(i),"verdict":"counts" if i<3 else "beyond_scope","reason":"r",
                   "replacement":"" if i<3 else "Ask what the claim states."} for i in range(5)]
        critique={"supported_grade":"A","findings":["f"]*len(CRITIQUE_RUBRIC["criteria"]),
                  "objections":[],"required_revisions":[],"case_verdicts":verdicts}
        record=audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,
                     {"r":dict(RETRIEVED)},critique=critique)
        self.assertEqual(record["evidence_ceiling"],"A")
        self.assertEqual(record["counted_cases"],["0","1","2"])
        self.assertEqual(record["case_ceiling"],"B")
        self.assertEqual(record["settled_ceiling"],"B")
        # Every case counting leaves the critique's own, lower judgment standing.
        agreeing=[{**item,"verdict":"counts","replacement":""} for item in verdicts]
        record=audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,
                     {"r":dict(RETRIEVED)},critique={**critique,"supported_grade":"C","case_verdicts":agreeing})
        self.assertEqual(record["case_ceiling"],"A")
        self.assertEqual(record["settled_ceiling"],"C")


class IndependentSessionTests(unittest.TestCase):
    def test_documentary_response_requires_exact_packet_citations(self):
        packet={"evidence":[{"reference_ref":"b"*64,"quote":"Known source text."}]}
        response={"status":"inconclusive","findings":["Evidence bounded"]*len(RUBRIC["criteria"]),
                  "citations":[{"reference_ref":"b"*64,"quote":"Known source"}],"limitations":"Documentary only."}
        validate_assessment(response,packet)
        response["citations"][0]["quote"]="Invented source"
        with self.assertRaises(Fault):
            validate_assessment(response,packet)

    def _assessor_packet_and_reply(self):
        packet={"evidence":[{"reference_ref":"b"*64,"quote":"Known source text."}]}
        reply={"status":"inconclusive","findings":["Evidence bounded"]*len(RUBRIC["criteria"]),
               "citations":[{"reference_ref":"b"*64,"quote":"Known source"}],
               "limitations":"Documentary only."}
        return packet,json.dumps(reply)

    def _replies(self,*texts):
        """Stand in for the fresh assessor sessions, one reply each, in order."""
        calls=iter(texts)
        def isolated(adapter,packet,*,role,system_prompt):
            return ({"text":next(calls),"observed_model_ids":["fixture-model"],
                     "usage":{},"total_cost_usd":0.0},str(uuid4()))
        return isolated

    def test_unusable_assessor_shape_is_retried_once_then_accepted(self):
        packet,good=self._assessor_packet_and_reply()
        with patch("sci_ai_verifier.documentary.isolated_answer",
                   side_effect=self._replies("not json at all",good)):
            result=assess(object(),packet)
        self.assertEqual(result["assessment"]["status"],"inconclusive")
        self.assertEqual(len(result["attempts"]),2)
        self.assertEqual(result["attempts"][0]["rejected"],"reply_not_parseable")
        self.assertNotIn("rejected",result["attempts"][1])

    def test_a_second_unusable_shape_is_an_operational_failure(self):
        packet,_=self._assessor_packet_and_reply()
        with patch("sci_ai_verifier.documentary.isolated_answer",
                   side_effect=self._replies("not json","{\"status\":\"pass\"}")):
            with self.assertRaises(Fault) as caught:
                assess(object(),packet)
        self.assertEqual(caught.exception.code,"assessor_response_invalid")

    def test_bad_citations_are_never_retried(self):
        """Re-rolling a parsed judgement until it is acceptable would be grade shopping."""
        packet,_=self._assessor_packet_and_reply()
        invented=json.dumps({"status":"pass","findings":["f"]*len(RUBRIC["criteria"]),
                             "citations":[{"reference_ref":"b"*64,"quote":"Invented source"}],
                             "limitations":"Documentary only."})
        calls=[]
        def counting(adapter,packet,*,role,system_prompt):
            calls.append(role)
            return ({"text":invented,"observed_model_ids":[],"usage":{},"total_cost_usd":0.0},str(uuid4()))
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=counting):
            with self.assertRaises(Fault) as caught:
                assess(object(),packet)
        self.assertEqual(caught.exception.code,"assessor_citation_invalid")
        self.assertEqual(len(calls),1)

    def test_critique_must_answer_inside_its_rubric(self):
        # `required_revisions` is a list beside `objections`, which is what a real session
        # emits. Recorded replies and the exhaustive refusal cases live in
        # tests/test_recorded_replies.py; this guards the shape the science path consumes.
        valid={"supported_grade":"B","findings":["f"]*len(CRITIQUE_RUBRIC["criteria"]),
               "objections":[],"required_revisions":["Add cases covering the rest of the scope."],
               "case_verdicts":[{"case_id":"c","verdict":"counts","reason":"in scope","replacement":""}]}
        self.assertEqual(validate_critique(valid)["supported_grade"],"B")
        self.assertEqual(validate_critique(valid)["required_revisions"],valid["required_revisions"])
        self.assertIsNone(validate_critique({**valid,"supported_grade":"none"})["supported_grade"])
        for broken in ({**valid,"supported_grade":"A+"},{**valid,"findings":["only one"]},
                       {**valid,"objections":"not a list"},{**valid,"required_revisions":0},
                       {**valid,"extra":"field"}):
            with self.subTest(broken=sorted(broken)),self.assertRaises(Fault):
                validate_critique(broken)

    def test_unusable_critique_shape_is_retried_once_and_a_verdict_never_is(self):
        packet={"evidence":{"cases":[{"case_id":"c"}]}}
        good=json.dumps({"supported_grade":"B","findings":["f"]*len(CRITIQUE_RUBRIC["criteria"]),
                         "objections":[],"required_revisions":[],
                         "case_verdicts":[{"case_id":"c","verdict":"counts","reason":"r","replacement":""}]},
                        separators=(",",":"))
        calls=[]
        def replies(*texts):
            texts=iter(texts)
            def isolated(adapter,packet,*,role,system_prompt,limit,timeout):
                # A critique gets five minutes; two killed one in run 74eadedd.
                self.assertEqual(timeout,300)
                calls.append(role)
                return ({"text":next(texts),"observed_model_ids":[],"usage":{},"total_cost_usd":0.0},str(uuid4()))
            return isolated
        # A case verdict naming a case the packet does not hold is a shape failure.
        wrong_case=good.replace('"case_id":"c"','"case_id":"x"')
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=replies(wrong_case,good)):
            result=critique(object(),packet)
        self.assertEqual(result["supported_grade"],"B")
        self.assertEqual([item.get("rejected") for item in result["attempts"]],["critic_response_invalid",None])
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=replies("not json","not json")):
            with self.assertRaises(Fault) as caught:
                critique(object(),packet)
        self.assertEqual(caught.exception.code,"critic_response_invalid")
        # A valid reply is kept at once, whatever grade it gives: one session, no re-roll.
        calls.clear()
        with patch("sci_ai_verifier.documentary.isolated_answer",
                   side_effect=replies(good.replace('"B"','"none"',1),good)):
            self.assertIsNone(critique(object(),packet)["supported_grade"])
        self.assertEqual(len(calls),1)


class GeneratedEvaluatorTests(unittest.TestCase):
    def test_python_candidate_failing_negative_control_is_rejected(self):
        cases=[{"case_id":str(i),"input":"input "+str(i),"expected":str(i),"reference_ref":"b"*64,
                "source_quote":"0 1 2","applicability":"fixture"} for i in range(3)]
        spec={"name":"Fixture","scope":"Fixture","method":"python","code":"print('unused fixture')",
              "limitations":"Synthetic only","cases":cases,"absolute_tolerance":"0","relative_tolerance":"0",
              "controls":[{"case_id":"0","actual":"0","group":group,"expected_status":status}
                for group,status in (("positive","pass"),("negative","fail"),("boundary","pass"),
                                     ("invalid","invalid"),("held_out","pass"))]}

        def always_pass(*args,**kwargs):
            return {"status":"pass","code_sha256":"a"*64,"image_id":"fixture","packet_sha256":"c"*64}

        result=qualify(spec,{"b"*64:{"text":"0 1 2"}},{},scorer=always_pass)
        self.assertEqual(result["status"],"rejected")
        for field in ("case_id","expected_status","group"):
            malformed=deepcopy(spec)
            malformed["controls"][0][field]=[]
            with self.assertRaises(Fault):
                validate_spec(malformed,{"b"*64:{"text":"0 1 2"}})
        spec["cases"][0]["expected"]="invented"
        with self.assertRaises(Fault):
            validate_spec(spec,{"b"*64:{"text":"0 1 2"}})


if __name__=="__main__":
    unittest.main()
