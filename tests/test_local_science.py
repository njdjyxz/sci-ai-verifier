"""Evidence-strength ceilings, the critique boundary and assessor limits; no live models."""

import json
import sys
import unittest
from copy import deepcopy
from math import log10 as math_log10
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault, canonical
from sci_ai_verifier.local_science import (GRADES,MAX_ROUNDS,POLICY_REF,audit,decide,evidence_ceiling,
                                           proposal_problem,weaker)
from sci_ai_verifier.documentary import (CRITIQUE_RUBRIC,RUBRIC,assess,critique,validate_assessment,
                                         validate_critique)
from sci_ai_verifier.local_evaluators import qualify,validate_spec
from sci_ai_verifier.local_candidates import METHOD_VERSION,qualify as qualify_candidate

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

    def test_every_open_answer_type_is_generated_and_only_choice_is_recognised(self):
        from sci_ai_verifier.answers import TYPES
        from sci_ai_verifier.local_science import answer_form
        for method in TYPES:
            with self.subTest(method=method):
                self.assertEqual(answer_form({"method": method}, {}), "recognised" if method == "choice" else "generated")

    def test_a_term_traces_to_its_quote_whatever_its_case(self):
        """A term is quoted as its words, so a key written in lower case still traces exactly to a
        sentence that capitalises it, and a design of such terms reaches A."""
        cases=[{**case,"expected":"molar","source_quote":"Molar concentration is used in row "+case["case_id"]}
               for case in self.candidate["cases"]]
        self.assertEqual(self.ceiling(method="term",cases=cases),("A",[]))
        cases=[{**case,"expected":"molar","source_quote":"Molarity is used in row "+case["case_id"]}
               for case in self.candidate["cases"]]
        self.assertIn("expected_value_not_token_exact_in_source",self.ceiling(method="term",cases=cases)[1])

    def test_the_grade_a_source_alone_supports_is_read_back_from_an_audit(self):
        from sci_ai_verifier.local_science import reference_grade, size_limit
        self.assertEqual(reference_grade(["fewer_than_five_counting_cases"]),"A")
        self.assertEqual(reference_grade(["expected_answers_not_independently_retrieved","no_generated_case"]),"B")
        self.assertEqual(reference_grade(["reference_origin_unknown"]),"C")
        self.assertIsNone(reference_grade(["comparison_not_deterministic"]))
        audit={"evidence_limits":["fewer_than_five_counting_cases"],"case_limits":["fewer_than_five_counting_cases"],
               "case_ceiling":"B","settled_ceiling":"B","counted_cases":["0","1","2","3"]}
        self.assertEqual(size_limit(audit,self.candidate),{"source_supports":"A","settled":"B","counting":4,
                                                           "generated":4,"counting_needed":5,"generated_needed":2})
        # A critique grade below the case ceiling is what held it down, not the claim's size.
        self.assertIsNone(size_limit({**audit,"settled_ceiling":"C"},self.candidate))
        # A source that supports only B is not held below itself.
        self.assertIsNone(size_limit({**audit,"evidence_limits":["expected_answers_not_independently_retrieved"]},
                                     self.candidate))
        # Too few cases for any grade is still the claim's size.
        few={**audit,"case_limits":["insufficient_distinct_cases"],"case_ceiling":None,"settled_ceiling":None,
             "counted_cases":["0","1"]}
        self.assertEqual(size_limit(few,self.candidate)["settled"],None)

    def test_only_counted_cases_enter_the_ceiling(self):
        """Run d87a6d5c: five cases, two of them counted, still graded A. The count now decides."""
        self.assertEqual(self.ceiling(counted=["0","1","2","3","4"])[0],"A")
        self.assertEqual(self.ceiling(counted=["0","1","2","3"])[0],"B")
        self.assertEqual(self.ceiling(counted=["0","1","2"])[0],"B")
        grade,reasons=self.ceiling(counted=["0","1"])
        self.assertIsNone(grade)
        self.assertIn("insufficient_distinct_cases",reasons)
        self.assertIsNone(self.ceiling(counted=[])[0])

    def test_the_case_gap_counts_what_a_grade_still_needs(self):
        """Run 31b67427: A was one counting case of either form away, and the planner, thinking
        it lacked an open case, accepted B. The gap is Python's count, not the planner's."""
        from sci_ai_verifier.local_science import case_gap
        options=["alpha","beta","gamma","delta","none of these"]
        mixed={**self.candidate,"method":"mixed",
               "cases":[{**case,"method":"numeric"} for case in self.candidate["cases"][:2]]
                      +[{**case,"method":"choice","expected":"1","options":options} for case in self.candidate["cases"][2:]]}
        # Four counted, two of them open: one more case of either form reaches A.
        gap=case_gap(mixed,["0","1","2","3"],"A","A")
        self.assertEqual((gap["counting_needed"],gap["generated_needed"]),(1,0))
        self.assertIn("add at least 1 more counting case of either form.",gap["summary"])
        # Four counted, one of them open: the one more case must be generated, and a critique
        # grade below the proposal is named as a second limit.
        gap=case_gap(mixed,["0","2","3","4"],"A","B")
        self.assertEqual((gap["counting_needed"],gap["generated_needed"]),(1,1))
        self.assertIn("add at least 1 more counting case, 1 of them generated.",gap["summary"])
        self.assertIn("The critique's own grade is B",gap["summary"])
        # Enough counted cases: the critique's grade is the only limit, including no grade at all.
        gap=case_gap(mixed,None,"B",None)
        self.assertEqual((gap["counting_needed"],gap["generated_needed"]),(0,0))
        self.assertIn("The critique's own grade, none, is what holds the settled grade down",gap["summary"])

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
        return packet,reply

    def _replies(self,*values,calls):
        """Stand in for the fresh sessions: each returns its next structured reply, in order."""
        values=iter(values)
        def isolated(adapter,packet,*,role,system_prompt,schema,**limits):
            calls.append({"role":role,"schema":schema,**limits})
            return ({"structured_output":next(values),"observed_model_ids":["fixture-model"],
                     "usage":{},"total_cost_usd":0.0},str(uuid4()))
        return isolated

    def test_one_assessor_session_is_asked_and_its_reply_is_checked_again(self):
        packet,good=self._assessor_packet_and_reply()
        calls=[]
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=self._replies(good,calls=calls)):
            result=assess(object(),packet)
        self.assertEqual(result["assessment"]["status"],"inconclusive")
        # The schema lets the assessor cite the packet's own references and nothing else.
        citation=calls[0]["schema"]["properties"]["citations"]["items"]["properties"]["reference_ref"]
        self.assertEqual(citation["enum"],["b"*64])
        # Claude Code corrects a reply outside the schema inside the session, so one that still
        # reaches Python is an operational failure and no second session is asked.
        calls.clear()
        with patch("sci_ai_verifier.documentary.isolated_answer",
                   side_effect=self._replies({"status":"pass"},good,calls=calls)):
            with self.assertRaises(Fault) as caught:
                assess(object(),packet)
        self.assertEqual(caught.exception.code,"assessor_response_invalid")
        self.assertEqual(len(calls),1)

    def test_bad_citations_are_never_retried(self):
        """Re-rolling a parsed judgement until it is acceptable would be grade shopping."""
        packet,good=self._assessor_packet_and_reply()
        invented={**good,"status":"pass","citations":[{"reference_ref":"b"*64,"quote":"Invented source"}]}
        calls=[]
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=self._replies(invented,good,calls=calls)):
            with self.assertRaises(Fault) as caught:
                assess(object(),packet)
        self.assertEqual(caught.exception.code,"assessor_citation_invalid")
        self.assertEqual(len(calls),1)

    def valid_critique(self):
        return {"supported_grade":"B","findings":["f"]*len(CRITIQUE_RUBRIC["criteria"]),
                "objections":[],"required_revisions":["Add cases covering the rest of the scope."],
                "coverage_gaps":[],"prior_verdicts":[],
                "case_verdicts":{"c":{"verdict":"counts","reason":"in scope","replacement":""}}}

    def test_critique_must_answer_inside_its_rubric(self):
        valid=self.valid_critique()
        self.assertEqual(validate_critique(valid,["c"])["supported_grade"],"B")
        self.assertEqual(validate_critique(valid,["c"])["required_revisions"],valid["required_revisions"])
        # Keyed by case ID in the reply, a list in packet order afterwards.
        self.assertEqual(validate_critique(valid,["c"])["case_verdicts"],
                         [{"case_id":"c","verdict":"counts","reason":"in scope","replacement":""}])
        self.assertIsNone(validate_critique({**valid,"supported_grade":"none"},["c"])["supported_grade"])
        for broken in ({**valid,"supported_grade":"A+"},{**valid,"findings":["only one"]},
                       {**valid,"objections":"not a list"},{**valid,"required_revisions":0},
                       {**valid,"extra":"field"}):
            with self.subTest(broken=sorted(broken)),self.assertRaises(Fault):
                validate_critique(broken,["c"])

    def test_one_critique_session_is_asked_and_a_verdict_is_never_re_rolled(self):
        packet={"evidence":{"cases":[{"case_id":"c"}]}}
        good=self.valid_critique()
        calls=[]
        # A valid reply is kept at once, whatever grade it gives.
        with patch("sci_ai_verifier.documentary.isolated_answer",
                   side_effect=self._replies({**good,"supported_grade":"none"},good,calls=calls)):
            self.assertIsNone(critique(object(),packet)["supported_grade"])
        self.assertEqual(len(calls),1)
        # A critique gets ten minutes: two killed one in run 74eadedd, and replays judging eleven
        # earlier concerns ran past five.
        self.assertEqual(calls[0]["timeout"],600)
        # The schema asks for exactly the packet's cases.
        self.assertEqual(calls[0]["schema"]["properties"]["case_verdicts"]["required"],["c"])
        calls.clear()
        wrong_case={**good,"case_verdicts":{"x":good["case_verdicts"]["c"]}}
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=self._replies(wrong_case,good,calls=calls)):
            with self.assertRaises(Fault) as caught:
                critique(object(),packet)
        self.assertEqual(caught.exception.code,"critic_response_invalid")
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


class ClaimProbeTests(unittest.TestCase):
    """The claim-only answers, with each Claude Code session replaced by a scripted reply."""

    def setUp(self):
        self.claim={"statement":"Setting X prevents partial rings.","expected_behavior":"Rings are whole.",
                    "scope":"X only"}
        self.closed="Which?\n1. a\n2. b\n3. c\n4. d\n5. none of these"
        self.candidate={"method":"mixed","cases":[
            {"case_id":"open","method":"numeric","input":"How many atoms?","expected":"3"},
            {"case_id":"closed","method":"choice","input":self.closed,"expected":"2",
             "options":["a","b","c","d","none of these"]}]}
        self.adapter=type("Pinned",(),{"model":"pinned-model"})()

    def probe(self,table,cache=None,readings=None):
        """Each question pops its next scripted reply; an exception is raised instead of answered,
        and a (text, models) pair names who answered. An answer the case's reader does not pass
        goes to the AI reader, which reads `readings[answer]`, or by default that it differs."""
        from threading import Lock
        from sci_ai_verifier.documentary import claim_probe
        lock,seen=Lock(),[]
        self.read=[]
        def answer(adapter,packet,*,role,system_prompt,schema,timeout,limit=64000):
            if role=="reader":
                with lock:
                    self.read.append(packet)
                value=(readings or {}).get(packet["reply"],{"reading":"differs","answer":packet["reply"],
                                                            "reason":"Scripted."})
                return ({"structured_output":value,"observed_model_ids":["pinned-model"],"usage":None,
                         "total_cost_usd":0.01},"reader-"+str(len(self.read)))
            with lock:
                seen.append(packet)
                reply=table[packet["question"]].pop(0)
            if isinstance(reply,Exception):
                raise reply
            text,models=reply if isinstance(reply,tuple) else (reply,["pinned-model"])
            return ({"structured_output":{"answer":text,"reason":"From the claim."},"observed_model_ids":models,
                     "total_cost_usd":0.01},"session-"+str(len(seen)))
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=answer):
            return claim_probe(self.adapter,self.claim,self.candidate,cache=cache),seen

    def outcomes(self,probe):
        return {item["case_id"]:item["outcome"] for item in probe["cases"]}

    def test_a_case_counts_only_when_every_claim_only_answer_reaches_its_key(self):
        """Run 3b3f3c94: faithful readers of one claim split on "lone ring atoms", once on the
        key and once on none of these. A split is the sign that the claim does not settle it."""
        probe,seen=self.probe({"How many atoms?":["3","2"],self.closed:["2","**2**"]})
        self.assertEqual(self.outcomes(probe),{"open":"missed","closed":"reached"})
        self.assertEqual(len(seen),4)
        # Each session saw the claim, one question and its answer form, never the skill or the key.
        self.assertTrue(all(set(packet)=={"claim","question","answer_format"} for packet in seen))
        self.assertEqual({packet["answer_format"] for packet in seen},
                         {"Write only the answer on the first line of your reply: the number.",
                          "Write only the answer on the first line of your reply: the number of the correct option."})
        # The miss was read once more, and the reading that it differs kept it a miss.
        self.assertEqual([packet["reply"] for packet in self.read],["2"])
        missed_sample=next(sample for item in probe["cases"] for sample in item["samples"] if sample["answer"]=="2")
        self.assertEqual((missed_sample["python_status"],missed_sample["status"]),("fail","fail"))
        self.assertEqual(missed_sample["reading"]["reading"],"differs")
        self.assertEqual(seen[0]["claim"],{"statement":self.claim["statement"],
                                           "expected_behavior":self.claim["expected_behavior"]})
        missed=next(item for item in probe["cases"] if item["case_id"]=="open")
        self.assertEqual(sorted(sample["answer"] for sample in missed["samples"]),["2","3"])

    def test_a_failed_or_substituted_session_leaves_its_case_unmeasured_and_asked_again(self):
        """A provider fault, or a refusal another model answered, says nothing about the claim."""
        cache={}
        probe,_=self.probe({"How many atoms?":[Fault("claude_timeout","slow"),"3"],
                            self.closed:[("2",["other-model","pinned-model"]),"2"]},cache)
        self.assertEqual(self.outcomes(probe),{"open":"unmeasured","closed":"unmeasured"})
        self.assertEqual(cache,{})
        # Asked again, and an answer that misses is still a miss beside a fault.
        probe,seen=self.probe({"How many atoms?":[Fault("claude_timeout","slow"),"4"],self.closed:["2","2"]},cache)
        self.assertEqual(len(seen),4)
        self.assertEqual(self.outcomes(probe),{"open":"missed","closed":"reached"})

    def test_an_unchanged_case_is_not_asked_again(self):
        cache={}
        self.probe({"How many atoms?":["3","3"],self.closed:["2","2"]},cache)
        self.assertEqual(len(cache),2)
        probe,seen=self.probe({},cache)
        self.assertEqual(seen,[])
        self.assertEqual(self.outcomes(probe),{"open":"reached","closed":"reached"})
        # A changed key is a different question.
        self.candidate["cases"][0]["expected"]="4"
        probe,seen=self.probe({"How many atoms?":["3","3"]},cache)
        self.assertEqual(len(seen),2)
        self.assertEqual(self.outcomes(probe)["open"],"missed")

    def test_a_reused_answer_is_reported_under_the_cases_current_id(self):
        """Run d416f79d: a case renamed between rounds kept its old ID on its reused answers, and
        counting matches misses by ID, so a renamed miss would still have counted."""
        from sci_ai_verifier.local_science import counted_cases
        first,_=self.probe({"How many atoms?":["3","2"],self.closed:["2","2"]})
        # As local.py builds it from the critiques earlier in the negotiation.
        earlier={item["case_ref"]:item for item in first["cases"] if item["outcome"]!="unmeasured"}
        self.candidate["cases"][0]["case_id"]="open-renamed"
        probe,seen=self.probe({},earlier)
        self.assertEqual(seen,[])
        self.assertEqual(self.outcomes(probe),{"open-renamed":"missed","closed":"reached"})
        critique={"case_verdicts":[{"case_id":"open-renamed","verdict":"counts","reason":"r","replacement":""},
                                   {"case_id":"closed","verdict":"counts","reason":"r","replacement":""}],
                  "claim_probe":probe}
        self.assertEqual(counted_cases(critique),["closed"])

    def test_an_answer_the_reader_reads_as_the_key_reaches_it(self):
        """Python's reader cannot read `3 atoms` as a number; the AI reader can, so a claim-only
        answer that gave the key in words does not reject a fair case."""
        probe,_=self.probe({"How many atoms?":["3 atoms","3"],self.closed:["2","2"]},
                           readings={"3 atoms":{"reading":"matches","answer":"3 atoms","reason":"It says 3."}})
        self.assertEqual(self.outcomes(probe),{"open":"reached","closed":"reached"})
        sample=next(sample for item in probe["cases"] for sample in item["samples"] if sample["answer"]=="3 atoms")
        self.assertEqual((sample["python_status"],sample["status"],sample["reading"]["status"]),
                         ("invalid","pass","used"))
        # The reader saw the question, its form, the key and the reply, and nothing of the claim.
        self.assertEqual(set(self.read[0]),{"question","answer_format","answer_type","expected_answer","reply"})

    def test_an_answer_saying_the_claim_does_not_settle_the_case_is_not_read_again(self):
        probe,_=self.probe({"How many atoms?":["UNDETERMINED","3"],self.closed:["5","2"]})
        self.assertEqual(self.outcomes(probe),{"open":"missed","closed":"missed"})
        self.assertEqual(self.read,[])

    def test_a_reading_python_can_contradict_is_refused(self):
        """A reader claiming `2` is the key 3 is overruled: Python reads 2 as another number."""
        probe,_=self.probe({"How many atoms?":["2","3"],self.closed:["2","2"]},
                           readings={"2":{"reading":"matches","answer":"2","reason":"Wrong."}})
        self.assertEqual(self.outcomes(probe)["open"],"missed")
        sample=next(sample for item in probe["cases"] for sample in item["samples"] if sample["answer"]=="2")
        self.assertEqual((sample["reading"]["status"],sample["reading"]["refusal"],sample["status"]),
                         ("refused","python_reads_another_answer","fail"))

    def test_a_stop_the_caller_asked_for_ends_the_probe(self):
        with self.assertRaises(Fault) as caught:
            self.probe({"How many atoms?":[Fault("verification_cancelled","stop"),"3"],self.closed:["2","2"]})
        self.assertEqual(caught.exception.code,"verification_cancelled")

    def test_each_session_carries_the_callers_deadline(self):
        """Worker threads start with empty context variables, so the probe copies the caller's."""
        from sci_ai_verifier.documentary import claim_probe
        from sci_ai_verifier.execution_control import CURRENT,Control
        control,observed=Control(60),[]
        def answer(adapter,packet,*,role,system_prompt,schema,timeout,limit=64000):
            observed.append(CURRENT.get())
            return {"structured_output":{"answer":"3" if "atoms" in packet["question"] else "2","reason":"r"},
                    "observed_model_ids":["pinned-model"],"total_cost_usd":0},"session"
        token=CURRENT.set(control)
        try:
            with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=answer):
                claim_probe(self.adapter,self.claim,self.candidate)
        finally:
            CURRENT.reset(token)
        self.assertEqual(observed,[control]*4)

    def test_counting_follows_the_claim_only_answers_and_keeps_the_critiques_verdicts(self):
        from sci_ai_verifier.local_science import counted_cases,rejected_cases
        critique={"case_verdicts":[{"case_id":"open","verdict":"counts","reason":"r","replacement":""},
                                   {"case_id":"closed","verdict":"leaked","reason":"stem","replacement":"x"}],
                  "claim_probe":{"cases":[{"case_id":"open","outcome":"missed","expected":"3",
                                           "samples":[{"answer":"2"},{"error":"claude_timeout"}]},
                                          {"case_id":"closed","outcome":"missed","expected":"2","samples":[]}]}}
        self.assertEqual(counted_cases(critique),[])
        rejected=rejected_cases(critique)
        self.assertEqual([(item["case_id"],item["verdict"],item.get("source")) for item in rejected],
                         [("open","beyond_scope","claim_probe"),("closed","leaked",None)])
        self.assertEqual(rejected[0]["reason"],"Fresh sessions given only the claim answered '2' where the key is "
                                               "'3', so a subject applying the claim as written could answer otherwise.")
        # Without claim-only answers, counting is the critique's alone, as before.
        del critique["claim_probe"]
        self.assertEqual(counted_cases(critique),["open"])


class ReplySchemaSessionTests(unittest.TestCase):
    """isolated_answer with only the child process replaced: what it asks Claude Code for and what it
    accepts back. Replies real sessions sent are in tests/recorded/, driven by test_recorded_replies.py."""

    SCHEMA={"type":"object","additionalProperties":False,"required":["answer"],
            "properties":{"answer":{"type":"string","minLength":1,"maxLength":10}}}

    def ask(self,*,code=0,tool="StructuredOutput",subtype="success",structured=True):
        from sci_ai_verifier.claude_runner import ClaudeCode
        from sci_ai_verifier.common import canonical
        from sci_ai_verifier.documentary import isolated_answer
        seen={}

        def process(command,**kwargs):
            seen["command"]=command
            session=command[command.index("--session-id")+1]
            reply={"answer":"9"}
            result={"type":"result","subtype":subtype,"is_error":subtype!="success","session_id":session,
                    "result":canonical(reply).decode()}
            if structured:
                result["structured_output"]=reply
            events=[{"type":"assistant","session_id":session,"message":{"model":"m","role":"assistant","content":[
                        {"type":"tool_use","id":"toolu_1","name":tool,"input":reply}]}},result]
            return code,b"".join(canonical(event)+b"\n" for event in events),b""

        import os
        with patch.dict(os.environ,{"CLAUDE_CODE_OAUTH_TOKEN":"fake-oauth-for-boundary-test"}):
            response,_=isolated_answer(ClaudeCode(auth="subscription",process=process),{"question":"q"},
                                       role="probe",system_prompt="Answer.",schema=self.SCHEMA)
        return response,seen["command"]

    def test_the_session_gets_the_schema_room_to_correct_and_no_other_tool(self):
        from sci_ai_verifier.common import canonical
        response,command=self.ask()
        self.assertEqual(response["structured_output"],{"answer":"9"})
        self.assertEqual(command[command.index("--json-schema")+1],canonical(self.SCHEMA).decode())
        self.assertEqual(command[command.index("--tools")+1],"")
        self.assertEqual(command[command.index("--max-turns")+1],"4")

    def test_any_other_tool_call_is_a_boundary_violation(self):
        with self.assertRaises(Fault) as caught:
            self.ask(tool="Bash")
        self.assertEqual(caught.exception.code,"probe_boundary_violation")

    def test_a_session_whose_replies_never_met_the_schema_is_an_invalid_reply(self):
        """Probed live on 2026-09-28: a session whose replies the schema refused twice ended as
        error_max_turns, exit code 1."""
        for subtype in ("error_max_turns","error_max_structured_output_retries"):
            with self.subTest(subtype),self.assertRaises(Fault) as caught:
                self.ask(code=1,subtype=subtype,structured=False)
            self.assertEqual(caught.exception.code,"probe_response_invalid")
        with self.assertRaises(Fault) as caught:
            self.ask(structured=False)
        self.assertEqual(caught.exception.code,"probe_response_invalid")
        # Any other failed session is simply unavailable.
        with self.assertRaises(Fault) as caught:
            self.ask(code=1,subtype="error_during_execution",structured=False)
        self.assertEqual(caught.exception.code,"probe_unavailable")


class CalculatedAnswerTests(unittest.TestCase):
    """Expected answers Python calculates from a quoted formula ("qualify_local_candidate" in
    tool-contracts.md). The pIC50 quotes are ChEMBL's, as run d416f79d retrieved them."""

    FORMULA="-Log(molar IC50, XC50, EC50, AC50, Ki, Kd or Potency)"
    WORKED="an IC50 measurement of 1nM would have a pChEMBL value of 9"
    PROGRAM="import math, sys\nprint(repr(-math.log10(float(sys.stdin.read()))))\n"

    def setUp(self):
        self.references={"f":{**RETRIEVED,"text":"pChEMBL is "+self.FORMULA+". For example, "+self.WORKED+"."}}
        self.runs=[]

    def calculate(self,code,inputs,log=math_log10):
        from sci_ai_verifier.common import digest
        self.runs.append(list(inputs))
        return {"code_sha256":digest(code.encode("utf-8")),"image_id":"sha256:"+"0"*64,
                "outputs":{value:repr(-log(float(value))) for value in inputs}}

    def proposal(self,**changes):
        cases=[{"case_id":"c"+str(index),"input":"An IC50 is "+molar+" M. Give its pIC50 rounded to two decimal places.",
                "arguments":molar,"decimals":2,"applicability":"fixture"}
               for index,molar in enumerate(("2.5e-4","3.2e-9","9.5e-10","6e-12","3e-8"))]
        return {"name":"pIC50 calculated","scope":"fixture","method":"numeric","limitations":"fixture","cases":cases,
                "calculation":{"code":self.PROGRAM,"reference_ref":"f","formula_quote":self.FORMULA,
                               "anchors":[{"arguments":"1e-9","expected":"9","reference_ref":"f",
                                           "source_quote":self.WORKED}]},**changes}

    def with_calculation(self,**changes):
        return self.proposal(calculation={**self.proposal()["calculation"],**changes})

    def problems(self,candidate):
        return " ".join(candidate["qualification_problems"])

    def test_python_keys_every_case_from_the_quoted_formula_and_the_design_can_reach_a(self):
        candidate=qualify_candidate(self.proposal(),self.references,self.calculate)
        self.assertEqual(candidate["status"],"qualified_local",candidate["qualification_problems"])
        self.assertEqual([case["expected"] for case in candidate["cases"]],["3.60","8.49","9.02","11.22","7.52"])
        self.assertTrue(all(case["source_quote"]==self.FORMULA and case["reference_ref"]=="f"
                            for case in candidate["cases"]))
        self.assertTrue(candidate["calculation_receipts"]["anchors"][0]["reproduced"])
        # One run per distinct input, the anchor's included.
        self.assertEqual(self.runs,[["1e-9","2.5e-4","3.2e-9","9.5e-10","6e-12","3e-8"]])
        self.assertEqual(evidence_ceiling(candidate,self.references,3),("A",[]))

    def test_a_wrong_formula_fails_on_the_quoted_worked_example_before_any_case_is_keyed(self):
        """A natural logarithm gives 20.7 for 1 nM where the page prints 9."""
        import math
        candidate=qualify_candidate(self.proposal(),self.references,
                                    lambda code,inputs:self.calculate(code,inputs,log=math.log))
        self.assertEqual(candidate["status"],"rejected")
        self.assertIn("where its reference prints '9'",self.problems(candidate))
        self.assertFalse(candidate["calculation_receipts"]["anchors"][0]["reproduced"])
        self.assertTrue(all("expected" not in case for case in candidate["cases"]))

    def test_an_anchor_is_compared_at_the_precision_its_page_prints(self):
        """Run 3b3f3c94 keyed 30 nM to a page's "which is pIC50 = 7.5"; the exact value is 7.522879."""
        from decimal import Decimal
        from sci_ai_verifier.local_candidates import at_precision
        self.references["f"]["text"]+=" A 30 nM compound, which is pIC50 = 7.5."
        candidate=qualify_candidate(self.with_calculation(anchors=[
            {"arguments":"3e-8","expected":"7.5","reference_ref":"f","source_quote":"which is pIC50 = 7.5"}]),
            self.references,self.calculate)
        self.assertEqual(candidate["status"],"qualified_local",candidate["qualification_problems"])
        self.assertEqual(at_precision("7.522879","7.5"),Decimal("7.5"))
        # Half away from zero, not to even, and a page's integer is compared as an integer.
        self.assertEqual(at_precision("7.55","7.5"),Decimal("7.6"))
        self.assertEqual(at_precision("0.125","0.01"),Decimal("0.13"))
        self.assertEqual(at_precision("8.999999999999998","9"),Decimal("9"))

    def test_a_worked_example_from_a_page_python_did_not_retrieve_lowers_the_ceiling(self):
        self.references["o"]={**RETRIEVED,"origin":"operator_local_resource","text":self.WORKED}
        candidate=qualify_candidate(self.with_calculation(anchors=[
            {"arguments":"1e-9","expected":"9","reference_ref":"o","source_quote":self.WORKED}]),
            self.references,self.calculate)
        self.assertEqual(candidate["status"],"qualified_local",candidate["qualification_problems"])
        ceiling,limits=evidence_ceiling(candidate,self.references,3)
        self.assertEqual(ceiling,"B")
        self.assertIn("expected_answers_not_independently_retrieved",limits)

    def test_the_formula_and_every_anchor_must_be_quoted_exactly(self):
        anchor={"arguments":"1e-9","expected":"9","reference_ref":"f","source_quote":self.WORKED}
        for label,changes in (("formula not on the page",{"formula_quote":"-log10(IC50 in M)"}),
                              ("anchor quote not on the page",{"anchors":[{**anchor,"source_quote":"1 nM gives 9"}]}),
                              ("anchor value not in its quote",{"anchors":[{**anchor,"expected":"9.0"}]}),
                              ("anchor reference not fetched",{"anchors":[{**anchor,"reference_ref":"missing"}]})):
            with self.subTest(label):
                candidate=qualify_candidate(self.with_calculation(**changes),self.references,self.calculate)
                self.assertEqual(candidate["status"],"rejected")
        self.assertEqual(self.runs,[],"nothing runs until the formula and anchors are proved quoted")

    def test_python_supplies_the_answer_and_its_quote(self):
        first=qualify_candidate(self.proposal(),self.references,self.calculate)
        # A saved candidate repeats Python's values exactly, so it qualifies again.
        self.assertEqual(qualify_candidate(self.proposal(cases=first["cases"]),self.references,self.calculate)["status"],
                         "qualified_local")
        changed=deepcopy(first["cases"])
        changed[0]["expected"]="3.61"
        candidate=qualify_candidate(self.proposal(cases=changed),self.references,self.calculate)
        self.assertEqual(candidate["status"],"rejected")
        self.assertIn("Python supplies a calculated case's expected",self.problems(candidate))

    def test_what_may_be_calculated_and_what_it_needs(self):
        cases=self.proposal()["cases"]
        quoted=[{"case_id":"q"+str(index),"input":"Question "+str(index),"expected":"9","reference_ref":"f",
                 "source_quote":self.WORKED,"applicability":"fixture"} for index in range(3)]
        for label,proposal,calculate in (
                ("no pinned sandbox",self.proposal(),None),
                ("arguments without decimals",self.proposal(cases=[{key:value for key,value in cases[0].items()
                                                                    if key!="decimals"},*cases[1:]]),self.calculate),
                ("an exact design",self.proposal(method="exact"),self.calculate),
                ("arguments without a calculation",{key:value for key,value in self.proposal().items()
                                                    if key!="calculation"},self.calculate),
                ("a calculation no case uses",self.proposal(cases=quoted),self.calculate),
                ("a quoted case without its quote",self.proposal(cases=[*cases[:2],{key:value for key,value in quoted[0].items()
                                                                            if key!="source_quote"}]),self.calculate)):
            with self.subTest(label):
                self.assertEqual(qualify_candidate(proposal,self.references,calculate)["status"],"rejected")

    def test_selection_re_checks_a_saved_candidate_from_its_receipts(self):
        from sci_ai_verifier.local_candidates import recorded
        candidate=qualify_candidate(self.proposal(),self.references,self.calculate)
        fields={key:candidate[key] for key in ("name","scope","method","limitations","cases","calculation")}
        self.assertEqual(qualify_candidate(fields,self.references,recorded(candidate))["status"],"qualified_local")
        self.assertEqual(len(self.runs),1,"the program is not run again")
        altered={**fields,"calculation":{**fields["calculation"],"code":self.PROGRAM+"# changed\n"}}
        with self.assertRaises(Fault) as caught:
            qualify_candidate(altered,self.references,recorded(candidate))
        self.assertEqual(caught.exception.code,"candidate_integrity")

    def test_the_critique_sees_the_program_the_anchors_and_every_cases_arguments(self):
        from sci_ai_verifier.local import critique_packet
        from sci_ai_verifier.local_science import PLANNER_JUSTIFICATION
        candidate=qualify_candidate(self.proposal(),self.references,self.calculate)
        packet=critique_packet({"statement":"s","scope":"s","expected_behavior":"e"},candidate,self.references,
                               {"target_grade":"A",**{key:"j" for key in PLANNER_JUSTIFICATION}},"A",[],3)
        shown=packet["evidence"]["calculation"]
        self.assertEqual(shown["code"],self.PROGRAM)
        self.assertEqual((shown["anchors"][0]["expected"],shown["anchors"][0]["output"]),("9","9.0"))
        self.assertTrue(all(case["calculated"] and case["arguments"] for case in packet["evidence"]["cases"]))
        self.assertIn("calculated_answers",packet["rubric"])
        # With no workflow log attached, Python says it recorded no search rather than inventing one.
        self.assertFalse(packet["python_checked"]["search_record"]["recorded"])

    def test_the_critique_reads_the_planners_notes_whole(self):
        """Run 26312681's critiques read every design's limitations cut at 800 characters and its
        coverage note at 2,000, although the tool schemas allow 8,000 and 4,000."""
        from sci_ai_verifier.local import JUSTIFICATION_TEXT,NOTE_TEXT,critique_packet
        from sci_ai_verifier.local_science import PLANNER_JUSTIFICATION
        candidate=qualify_candidate(self.proposal(),self.references,self.calculate)
        notes={key:key[0]*JUSTIFICATION_TEXT for key in PLANNER_JUSTIFICATION}
        whole={**candidate,"scope":"s"*NOTE_TEXT,"limitations":"l"*NOTE_TEXT}
        packet=critique_packet({"statement":"s","scope":"s","expected_behavior":"e"},whole,self.references,
                               {"target_grade":"A",**notes},"A",[],3)
        self.assertEqual(packet["evidence"]["candidate_scope"],"s"*NOTE_TEXT)
        self.assertEqual(packet["evidence"]["candidate_limitations"],"l"*NOTE_TEXT)
        self.assertEqual(packet["justification"],notes)
        self.assertNotIn("[truncated]",canonical(packet).decode())

    def test_the_largest_critique_packet_the_schemas_allow_fits_its_limit(self):
        """Every field at its schema maximum: claim, twelve cases each with its own reference, the
        program and its eight anchors, the planner's notes, a full search record and every carried
        concern. A design the tools accept must never fail on the packet's size."""
        from sci_ai_verifier.documentary import CRITIC_PACKET_LIMIT
        from sci_ai_verifier.local import JUSTIFICATION_TEXT,NOTE_TEXT,RECORD_ITEMS,critique_packet
        from sci_ai_verifier.local_science import PLANNER_JUSTIFICATION
        candidate=qualify_candidate(self.proposal(),self.references,self.calculate)
        references={f"ref-{index}":{"url":f"https://example.org/{index}/"+"u"*4070,"version":"v"*200,
                                     "license":"l"*2000,"origin":"retrieved_public_https"} for index in range(21)}
        case=candidate["cases"][0]
        cases=[{**case,"case_id":f"{index:02d}"+"c"*78,"input":"i"*8000,"expected":"e"*4000,"reference_ref":f"ref-{index}",
                "source_quote":"q"*8000,"applicability":"a"*4000,"options":["o"*4000]*9,"arguments":"x"*4000}
               for index in range(12)]
        anchor={"arguments":"x"*4000,"expected":"9"*100,"output":"9"*100,"source_quote":"q"*8000}
        largest={**candidate,"scope":"s"*NOTE_TEXT,"limitations":"l"*NOTE_TEXT,"cases":cases,
                 "calculation":{**candidate["calculation"],"code":"p"*32000,"formula_quote":"f"*8000,
                                "reference_ref":"ref-12"},
                 "calculation_receipts":{**candidate["calculation_receipts"],
                                         "anchors":[{**anchor,"reference_ref":f"ref-{13+index}"} for index in range(8)]}}
        record={"recorded":True,"searches_total":RECORD_ITEMS*2,"fetches_total":RECORD_ITEMS*2,
                "searches":[{"query":"w"*200,"for":"another claim"}]*RECORD_ITEMS,
                "fetches":[{"tool":"fetch_local_reference","url":"u"*200,"for":"another claim",
                            "outcome":"refused: "+"r"*80}]*RECORD_ITEMS,"note":"n"*400}
        packet=critique_packet({key:"t"*16000 for key in ("statement","scope","expected_behavior")},largest,references,
                               {"target_grade":"A",**{key:"j"*JUSTIFICATION_TEXT for key in PLANNER_JUSTIFICATION}},
                               "A",["limit-reason"]*12,3,["o"*1000]*16,record)
        self.assertLess(len(canonical(packet)),CRITIC_PACKET_LIMIT)

    def test_the_report_says_the_planner_wrote_the_calculation(self):
        candidate=qualify_candidate(self.proposal(),self.references,self.calculate)
        audit_record={"settled_ceiling":"A","evidence_ceiling":"A","evidence_limits":[],"case_limits":[],
                      "policy_ref":POLICY_REF,"proposed_grade":"A"}
        observations=[{"case_id":case["case_id"],"trial":trial,"comparison_status":"pass","model_ids":["m"]}
                      for case in candidate["cases"] for trial in (1,2,3)]
        record=decide(audit_record,observations,candidate["cases"],3)
        self.assertEqual(record["evidence_grade"],"A")
        self.assertIn("wrote the program that calculated 5 of the 5",record["ai_involvement"]["evidence_generation"])

    def test_the_program_runs_once_per_input_in_one_pinned_container(self):
        from sci_ai_verifier.local_evaluators import calculate
        commands,opened=[],[]

        class Sandbox:
            image="sha256:"+"1"*64

            def __init__(self,source,settings,*,timeout,log):
                self.source=source
                opened.append(timeout)

            def __enter__(self):
                return self

            def __exit__(self,*args):
                return False

            def command(self,command,*,stdin,timeout):
                commands.append((command,stdin,(self.source/"calculation.py").read_text(encoding="utf-8")))
                printed,code={"1e-9":("9.0\n",0),"2":("not a number",0),"3":("1",1)}[stdin]
                return {"exit_code":code,"stdout":printed,"stderr":""}

        result=calculate("print(1)",["1e-9","2","3"],{"sandbox_image":"img"},sandbox_factory=Sandbox)
        self.assertEqual(result["outputs"],{"1e-9":"9.0","2":None,"3":None})
        self.assertEqual(result["image_id"],Sandbox.image)
        self.assertEqual(len(opened),1)
        self.assertEqual({(command,program) for command,_,program in commands},
                         {("python3 -I /work/calculation.py","print(1)")})
        with self.assertRaises(Fault) as caught:
            calculate("print(1)",["1"],{},sandbox_factory=Sandbox)
        self.assertEqual(caught.exception.code,"sandbox_configuration_required")


if __name__=="__main__":
    unittest.main()
