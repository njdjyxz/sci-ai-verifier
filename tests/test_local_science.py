"""Evidence-strength ceilings, the critique boundary and assessor limits for task designs; no live models."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault, canonical
from sci_ai_verifier.local_science import (GRADES,MAX_ROUNDS,POLICY_REF,audit,decide,evidence_ceiling,
                                           proposal_problem,weaker)
from sci_ai_verifier.documentary import RUBRIC,TASK_CRITIQUE_RUBRIC,assess,critique_tasks,validate_assessment
from sci_ai_verifier.local_tasks import METHOD_VERSION

RETRIEVED={"origin":"retrieved_public_https","url":"https://example.org/r","version":"1","license":"unknown"}
MODEL="Fixture model: the response is the dose times the slope."


def quoted(index,ref=None):
    """A task whose one output is quoted from its own reference, or from `ref`."""
    return {"case_id":str(index),"job":"Report row "+str(index)+".","sections":["S1"],
            "outputs":[{"field":"value","type":"number","value":str(index)+".0","expected":str(index)+".0",
                        "source":"quoted","reference_ref":ref or "r"+str(index),
                        "source_quote":"row "+str(index)+" is "+str(index)+".0 exactly"}],
            "applicability":"row"}


def planted(index):
    """A task whose output the generator planted from the design's quoted model."""
    return {"case_id":"p"+str(index),"job":"Fit table "+str(index)+".","sections":["S1"],"arguments":"{}",
            "outputs":[{"field":"slope","type":"number","planted":"slope","expected":"2","source":"planted"}],
            "applicability":"table"}


def design(count=3,ref=None):
    return {"method":"task","method_version":METHOD_VERSION,"name":"Fixture","scope":"Fixture scope",
            "limitations":"Fixture","solver":{"code":"print(1)"},"cases":[quoted(index,ref) for index in range(count)]}


class CeilingTests(unittest.TestCase):
    def setUp(self):
        self.references={"r"+str(index):dict(RETRIEVED) for index in range(5)}
        self.candidate=design()

    def ceiling(self,trials=3,counted=None,**changes):
        return evidence_ceiling({**self.candidate,**changes},self.references,trials,counted)

    def test_three_tasks_quoted_from_retrieved_pages_with_three_trials_reach_a(self):
        self.assertEqual(self.ceiling(),("A",[]))

    def test_a_needs_three_counting_tasks_and_two_reach_only_b(self):
        self.assertEqual(self.ceiling(cases=self.candidate["cases"][:2]),("B",["fewer_than_three_counting_tasks"]))
        self.assertEqual(self.ceiling(cases=self.candidate["cases"][:1]),
                         (None,["fewer_than_three_counting_tasks","fewer_than_two_counting_tasks"]))

    def test_planted_values_trace_to_the_generator_s_quoted_model(self):
        """A planted number rests on the model the generator implements; without one it rests on nothing."""
        self.references["m"]={**RETRIEVED,"text":MODEL}
        generator={"code":"print(1)","reference_ref":"m","model_quote":MODEL}
        cases=[planted(index) for index in range(3)]
        self.assertEqual(self.ceiling(cases=cases,generator=generator),("A",[]))
        self.assertIn("expected_value_not_token_exact_in_source",self.ceiling(cases=cases)[1])
        # A planted judgment, such as which compound is more potent, also quotes the rule it follows.
        judged=[{**case,"outputs":[{"field":"pick","type":"text","planted":"pick","expected":"A","source":"planted"}]}
                for case in cases]
        self.assertIn("expected_value_not_token_exact_in_source",self.ceiling(cases=judged,generator=generator)[1])

    def test_a_quoted_value_must_be_a_whole_token_of_its_quote(self):
        cases=design()["cases"]
        # "1.0" inside "21.09" is a substring, not an independent answer for this task.
        cases[1]["outputs"][0]["source_quote"]="row 1 is 21.09 total"
        grade,reasons=self.ceiling(cases=cases)
        self.assertEqual(grade,"C")
        self.assertIn("expected_value_not_token_exact_in_source",reasons)

    def test_the_grade_a_source_alone_supports_is_read_back_from_an_audit(self):
        from sci_ai_verifier.local_science import reference_grade, size_limit
        self.assertEqual(reference_grade(["fewer_than_three_counting_tasks"]),"A")
        self.assertEqual(reference_grade(["expected_answers_not_independently_retrieved"]),"B")
        self.assertEqual(reference_grade(["reference_origin_unknown"]),"C")
        audit={"evidence_limits":["fewer_than_three_counting_tasks"],"case_limits":["fewer_than_three_counting_tasks"],
               "case_ceiling":"B","settled_ceiling":"B","counted_cases":["0","1"]}
        self.assertEqual(size_limit(audit,self.candidate),{"source_supports":"A","settled":"B","unit":"tasks",
                                                           "counting":2,"counting_needed":3})
        # A critique grade below the task ceiling is what held it down, not the number of tasks.
        self.assertIsNone(size_limit({**audit,"settled_ceiling":"C"},self.candidate))
        # A source that supports only B is not held below itself.
        self.assertIsNone(size_limit({**audit,"evidence_limits":["expected_answers_not_independently_retrieved"]},
                                     self.candidate))
        # Too few tasks for any grade is still the design's size.
        few={**audit,"case_limits":["fewer_than_three_counting_tasks","fewer_than_two_counting_tasks"],
             "case_ceiling":None,"settled_ceiling":None,"counted_cases":["0"]}
        self.assertEqual(size_limit(few,self.candidate)["settled"],None)

    def test_only_counted_tasks_enter_the_ceiling(self):
        """Run d87a6d5c: five cases, two of them counted, still graded A. The count now decides."""
        self.assertEqual(self.ceiling(counted=["0","1","2"])[0],"A")
        self.assertEqual(self.ceiling(counted=["0","1"])[0],"B")
        grade,reasons=self.ceiling(counted=["0"])
        self.assertIsNone(grade)
        self.assertIn("fewer_than_two_counting_tasks",reasons)
        self.assertIsNone(self.ceiling(counted=[])[0])

    def test_the_task_gap_counts_what_a_grade_still_needs(self):
        """Run 31b67427's planner accepted B one counting case short of A, believing it lacked one it
        already had. The gap is Python's count, not the planner's."""
        from sci_ai_verifier.local_science import case_gap
        gap=case_gap(self.candidate,["0","1"],"A","A")
        self.assertEqual((gap["tasks_required"],gap["tasks_counted"],gap["tasks_needed"]),(3,2,1))
        self.assertIn("add at least 1 more task.",gap["summary"])
        # A critique grade below the proposal is named as a second limit.
        gap=case_gap(self.candidate,["0"],"A","B")
        self.assertEqual(gap["tasks_needed"],2)
        self.assertIn("add at least 2 more tasks.",gap["summary"])
        self.assertIn("The critique's own grade is B",gap["summary"])
        # Enough counted tasks: the critique's grade is the only limit, including no grade at all.
        gap=case_gap(self.candidate,None,"B",None)
        self.assertEqual(gap["tasks_needed"],0)
        self.assertIn("The critique's own grade, none, is what holds the settled grade down",gap["summary"])

    def test_an_operator_dataset_caps_at_b(self):
        self.references["r0"]={**RETRIEVED,"origin":"operator_local_resource"}
        grade,reasons=self.ceiling()
        self.assertEqual(grade,"B")
        self.assertIn("expected_answers_not_independently_retrieved",reasons)

    def test_a_single_trial_and_an_unknown_origin_cap_at_c(self):
        self.assertEqual(self.ceiling(trials=1)[0],"C")
        self.assertIn("model_subject_trial_count_below_three",self.ceiling(trials=1)[1])
        self.references["r1"]={"url":"cached","version":"1","license":"unknown"}
        self.assertEqual(self.ceiling()[0],"C")
        self.assertIn("reference_origin_unknown",self.ceiling()[1])

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
        # D is the ceiling of a judged design only ("Judged outputs" in local-tasks.md).
        self.assertIsNone(proposal_problem("D","D"))
        self.assertEqual(proposal_problem("D","A"),"below_evidence_ceiling")
        with self.assertRaises(Fault) as caught:
            proposal_problem("U","A")
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
        self.cases=[quoted(index) for index in range(3)]
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

    def test_one_wrong_result_beats_an_unreadable_one(self):
        """Operator, 2026-10-05: a trial that was clearly wrong decides the claim, whatever another said."""
        rows=self.rows(3)
        rows[0]["comparison_status"]="invalid"
        rows[4]["comparison_status"]="fail"
        result=decide(self.audit,rows,self.cases,3)
        self.assertEqual((result["scientific_status"],result["evidence_grade"]),("fail","A"))
        self.assertIn("invalid_observations_retained",result["execution_limit_reasons"])

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
        # No AI reads a trial: Python's fixed checks decide every one.
        self.assertFalse(result["ai_involvement"]["verdict"])
        self.assertIn("Every expected value is quoted from a reference Python retrieved.",
                      result["ai_involvement"]["evidence_generation"])

    def test_audit_records_the_critique_that_settled_the_grade(self):
        candidate=design(ref="r")
        critique={"supported_grade":"C","findings":["f"]*len(TASK_CRITIQUE_RUBRIC["criteria"]),
                  "objections":["Three rows do not cover the stated scope."],"required_revisions":["Add tasks."]}
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

    def test_no_counted_task_reports_no_agreement_rather_than_unanimity(self):
        record={"settled_ceiling":None,"evidence_limits":[],"case_limits":["fewer_than_two_counting_tasks"],
                "policy_ref":POLICY_REF,"proposed_grade":"A","evidence_ceiling":"A"}
        result=decide(record,[],[],3,synthetic=False)
        self.assertEqual(result["consistency"]["label"],"no_counted_cases")
        self.assertIsNone(result["evidence_grade"])
        self.assertIn("fewer_than_two_counting_tasks",result["grade_limit_reasons"])

    def test_the_task_count_binds_a_critique_that_rejected_tasks_but_supported_a(self):
        """The critique's letter cannot outrun its own verdicts; nor is its lower grade overridden."""
        candidate=design(4,ref="r")
        verdicts=[{"case_id":str(i),"verdict":"counts" if i<2 else "beyond_scope","reason":"r",
                   "replacement":"" if i<2 else "Ask what the claim states."} for i in range(4)]
        critique={"supported_grade":"A","findings":["f"]*len(TASK_CRITIQUE_RUBRIC["criteria"]),
                  "objections":[],"required_revisions":[],"case_verdicts":verdicts}
        record=audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,
                     {"r":dict(RETRIEVED)},critique=critique)
        self.assertEqual(record["evidence_ceiling"],"A")
        self.assertEqual(record["counted_cases"],["0","1"])
        self.assertEqual(record["case_ceiling"],"B")
        self.assertEqual(record["settled_ceiling"],"B")
        # Every task counting leaves the critique's own, lower judgment standing.
        agreeing=[{**item,"verdict":"counts","replacement":""} for item in verdicts]
        record=audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,
                     {"r":dict(RETRIEVED)},critique={**critique,"supported_grade":"C","case_verdicts":agreeing})
        self.assertEqual(record["case_ceiling"],"A")
        self.assertEqual(record["settled_ceiling"],"C")

    def test_a_departure_holds_the_grade_one_below_the_proposal_it_judged(self):
        """Run 2bef9e0d's critique worked out that the skill's two-step formula passed only inside the tolerance,
        agreed with A, and listed it as a gap. A listed departure now holds the grade below the proposal, and
        accepting the grade it settled at holds it no lower."""
        from sci_ai_verifier.local_science import POLICY
        candidate=design(4,ref="r")
        verdicts=[{"case_id":str(i),"verdict":"counts","reason":"r","replacement":"","criterion_given":""}
                  for i in range(4)]
        critique={"supported_grade":"A","findings":["f"]*len(TASK_CRITIQUE_RUBRIC["criteria"]),"objections":[],
                  "required_revisions":[],"departures":["Followed literally, the formula keeps the loading."],
                  "case_verdicts":verdicts}
        for proposed,held in (("A","B"),("B","C"),("C",None)):
            record=audit(candidate,{"scope":"s"},{"max_subject_calls":64},{**self.selection,"target_grade":proposed},
                         {"r":dict(RETRIEVED)},critique=critique)
            self.assertEqual((record["settled_ceiling"],record["held_by_departures"]),(held,True))
        accepted=audit(candidate,{"scope":"s"},{"max_subject_calls":64},{**self.selection,"target_grade":"B"},
                       {"r":dict(RETRIEVED)},critique=critique,accepted="B")
        self.assertEqual((accepted["settled_ceiling"],accepted["held_by_departures"]),("B",False))
        clean=audit(candidate,{"scope":"s"},{"max_subject_calls":64},self.selection,{"r":dict(RETRIEVED)},
                    critique={**critique,"departures":[]})
        self.assertEqual((clean["settled_ceiling"],clean["held_by_departures"]),("A",False))
        self.assertIn("departures",POLICY)

    def test_accepting_a_design_a_departure_held_to_no_grade_settles_at_no_grade(self):
        """A departure holds C, or a judged design's D, to no grade. Accepting that is proposing the ceiling
        again, since there is no lower grade to name, and the settled grade must stay none: the planner of
        such a design used to regain C or D on acceptance, and the departure's hold vanished with it."""
        verdicts=[{"case_id":str(i),"verdict":"counts","reason":"r","replacement":"","criterion_given":""}
                  for i in range(4)]
        critique={"supported_grade":"C","findings":["f"]*len(TASK_CRITIQUE_RUBRIC["criteria"]),"objections":[],
                  "required_revisions":[],"departures":["Followed literally, the formula keeps the loading."],
                  "case_verdicts":verdicts}
        # Two trials hold the reference to C.
        selection={**self.selection,"target_grade":"C","trials_per_case":2}
        judged=audit(design(4,ref="r"),{"scope":"s"},{"max_subject_calls":64},selection,{"r":dict(RETRIEVED)},
                     critique=critique)
        self.assertEqual((judged["settled_ceiling"],judged["held_by_departures"]),(None,True))
        accepted=audit(design(4,ref="r"),{"scope":"s"},{"max_subject_calls":64},selection,{"r":dict(RETRIEVED)},
                       critique=critique,accepted=None)
        self.assertEqual((accepted["settled_ceiling"],accepted["held_by_departures"]),(None,False))
        # The same for a judged design, whose ceiling is D.
        from sci_ai_verifier.local_tasks import METHOD_VERSION
        self.references={"r":{**RETRIEVED,"text":"Quoted rule."}}
        cases=[{**quoted(index,"r"),"outputs":[{"field":"advice","type":"judged","expected":["q"],"source":"judged",
                                              "criteria":[{"question":"q","reference_ref":"r","source_quote":"Quoted rule."}],
                                              "fail_example":"wrong"}]} for index in range(2)]
        design_d={"method":"task","method_version":METHOD_VERSION,"name":"Judged","scope":"s","limitations":"l",
                  "solver":{"code":"print(1)"},"cases":cases}
        critique_d={**critique,"supported_grade":"D","case_verdicts":verdicts[:2]}
        selection_d={**self.selection,"target_grade":"D"}
        judged=audit(design_d,{"scope":"s"},{"max_subject_calls":64},selection_d,self.references,critique=critique_d)
        self.assertEqual((judged["evidence_ceiling"],judged["settled_ceiling"]),("D",None))
        accepted=audit(design_d,{"scope":"s"},{"max_subject_calls":64},selection_d,self.references,
                       critique=critique_d,accepted=None)
        self.assertIsNone(accepted["settled_ceiling"])
        # Accepting a grade the critique settled at, B after A, still holds there and no lower.
        held=audit(design(4,ref="r"),{"scope":"s"},{"max_subject_calls":64},{**self.selection,"target_grade":"B"},
                   {"r":dict(RETRIEVED)},critique={**critique,"supported_grade":"A"},accepted="B")
        self.assertEqual(held["settled_ceiling"],"B")


class IndependentSessionTests(unittest.TestCase):
    @staticmethod
    def statement(verdict,quote=""):
        return {"statement":"A statement of the claim.","verdict":verdict,
                "reference_ref":"b"*64 if quote else "","quote":quote}

    def test_documentary_response_requires_exact_packet_citations(self):
        packet={"evidence":[{"reference_ref":"b"*64,"quote":"Known source text."}]}
        response={"statements":[self.statement("supported","Known source"),self.statement("not_addressed")],
                  "findings":["Evidence bounded"]*len(RUBRIC["criteria"]),"limitations":"Documentary only."}
        value=validate_assessment(response,packet)
        # Python derives the status and the citations from the statements.
        self.assertEqual((value["status"],value["citations"]),
                         ("inconclusive",[{"reference_ref":"b"*64,"quote":"Known source"}]))
        response["statements"][0]["quote"]="Invented source"
        with self.assertRaises(Fault):
            validate_assessment(response,packet)
        # A supported or contradicted statement must quote the packet.
        response["statements"][0]["quote"]=""
        with self.assertRaises(Fault):
            validate_assessment(response,packet)

    def test_python_gives_the_documentary_status_and_unaddressed_sources_give_u(self):
        """Run 3f073fec's made-up fade correction got D, inconclusive, from a blot review that never named it."""
        from sci_ai_verifier.documentary import documentary_status
        supported,contradicted,silent=(self.statement("supported","q"),self.statement("contradicted","q"),
                                       self.statement("not_addressed"))
        self.assertEqual(documentary_status([supported,supported]),"pass")
        self.assertEqual(documentary_status([supported,contradicted,silent]),"fail")
        self.assertEqual(documentary_status([supported,silent]),"inconclusive")
        self.assertEqual(documentary_status([silent,silent]),"no_evidence")
        self.assertEqual(RUBRIC["id"],"local-documentary-v2")
        self.assertIn("grade U",RUBRIC["status_rules"]["no_evidence"])

    def _assessor_packet_and_reply(self):
        packet={"evidence":[{"reference_ref":"b"*64,"quote":"Known source text."}]}
        reply={"statements":[self.statement("supported","Known source"),self.statement("not_addressed")],
               "findings":["Evidence bounded"]*len(RUBRIC["criteria"]),"limitations":"Documentary only."}
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
        # The schema lets the assessor cite the packet's own references and nothing else, or none.
        citation=calls[0]["schema"]["properties"]["statements"]["items"]["properties"]["reference_ref"]
        self.assertEqual(citation["enum"],["","b"*64])
        # Run ed14663f's assessor of a claim about a script's code ran past the two minutes it had.
        from sci_ai_verifier.documentary import ASSESSOR_TIMEOUT_SECONDS
        self.assertEqual(ASSESSOR_TIMEOUT_SECONDS,600)
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
        invented={**good,"statements":[self.statement("supported","Invented source")]}
        calls=[]
        with patch("sci_ai_verifier.documentary.isolated_answer",side_effect=self._replies(invented,good,calls=calls)):
            with self.assertRaises(Fault) as caught:
                assess(object(),packet)
        self.assertEqual(caught.exception.code,"assessor_citation_invalid")
        self.assertEqual(len(calls),1)

    def valid_critique(self):
        from sci_ai_verifier.documentary import TASK_QUESTIONS
        return {"supported_grade":"B","findings":["f"]*len(TASK_CRITIQUE_RUBRIC["criteria"]),
                "objections":[],"required_revisions":["Add tasks covering the rest of the scope."],"coverage_gaps":[],
                "departures":[],"unsourced_rules":[],"task_checks":{"c":{**{key:{"answer":"no","reason":"in scope"}
                                                      for key,_,_ in TASK_QUESTIONS},
                                                   "criterion_given":"","replacement":""}}}

    def test_one_critique_session_is_asked_and_a_verdict_is_never_re_rolled(self):
        packet={"evidence":{"tasks":[{"case_id":"c"}]}}
        good=self.valid_critique()
        calls=[]
        # A valid reply is kept at once, whatever grade it gives.
        with patch("sci_ai_verifier.documentary.isolated_answer",
                   side_effect=self._replies({**good,"supported_grade":"none"},good,calls=calls)):
            self.assertIsNone(critique_tasks(object(),packet)["supported_grade"])
        self.assertEqual(len(calls),1)
        # A critique gets twenty minutes at effort high: two killed one in run 74eadedd, replays judging eleven
        # earlier concerns ran past five, and answering a question per verdict for six tasks took eight at the
        # default effort ("Critique" in local-contract.md).
        self.assertEqual((calls[0]["timeout"],calls[0]["effort"]),(1200,"high"))
        # Run cfe9e57a's critiques passed 256 KiB at xhigh and were cut off; the assessor keeps that limit.
        self.assertEqual(calls[0]["max_bytes"],2*1024*1024)
        # The schema asks for exactly the packet's tasks, and for the answers before the grade.
        self.assertEqual(calls[0]["schema"]["properties"]["task_checks"]["required"],["c"])
        properties=list(calls[0]["schema"]["properties"])
        self.assertEqual((properties[0],properties[-1]),("task_checks","supported_grade"))
        # The rules it finds no source for come just before its grade, shown as grade U beside it.
        self.assertEqual(properties[-2],"unsourced_rules")
        for broken in ({**good,"task_checks":{"x":good["task_checks"]["c"]}},{**good,"supported_grade":"A+"},
                       {**good,"findings":["only one"]},{**good,"extra":"field"}):
            calls.clear()
            with self.subTest(broken=sorted(broken)), \
                    patch("sci_ai_verifier.documentary.isolated_answer",side_effect=self._replies(broken,good,calls=calls)):
                with self.assertRaises(Fault) as caught:
                    critique_tasks(object(),packet)
                self.assertEqual(caught.exception.code,"critic_response_invalid")
                self.assertEqual(len(calls),1)


class CritiquePacketTests(unittest.TestCase):
    """What the critique of a task design reads ("Selecting and critiquing a task design" in local-tasks.md)."""

    def test_the_critique_reads_the_planners_notes_whole(self):
        """Run 26312681's critiques read every design's limitations cut at 800 characters and its
        coverage note at 2,000, although the tool schemas allow 8,000 and 4,000."""
        from sci_ai_verifier.local import JUSTIFICATION_TEXT,NOTE_TEXT
        from sci_ai_verifier.local_science import PLANNER_JUSTIFICATION
        from sci_ai_verifier.local_tasks import critique_packet
        notes={key:key[0]*JUSTIFICATION_TEXT for key in PLANNER_JUSTIFICATION}
        whole={**design(),"scope":"s"*NOTE_TEXT,"limitations":"l"*NOTE_TEXT}
        references={"r"+str(index):dict(RETRIEVED) for index in range(3)}
        packet=critique_packet({"statement":"s","scope":"s","expected_behavior":"e"},[],whole,references,
                               {"target_grade":"A",**notes},"A",[],3,[],{"recorded":False},lambda ref:b"")
        self.assertEqual(packet["evidence"]["design_scope"],"s"*NOTE_TEXT)
        self.assertEqual(packet["evidence"]["design_limitations"],"l"*NOTE_TEXT)
        self.assertEqual(packet["justification"],notes)
        self.assertEqual(packet["rubric"],TASK_CRITIQUE_RUBRIC)
        self.assertNotIn("[truncated]",canonical(packet).decode())


class ReplySchemaSessionTests(unittest.TestCase):
    """isolated_answer with only the child process replaced: what it asks Claude Code for and what it
    accepts back. Replies real sessions sent are in tests/recorded/, driven by test_recorded_replies.py."""

    SCHEMA={"type":"object","additionalProperties":False,"required":["answer"],
            "properties":{"answer":{"type":"string","minLength":1,"maxLength":10}}}

    def ask(self,*,code=0,tool="StructuredOutput",subtype="success",structured=True,offered=None,outcome=None):
        """`offered` is the init event's tool list; `outcome` answers the call: "ran", "refused" or none."""
        from sci_ai_verifier.claude_runner import ClaudeCode
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
                        {"type":"tool_use","id":"toolu_1","name":tool,"input":reply}]}}]
            if offered is not None:
                events.insert(0,{"type":"system","subtype":"init","session_id":session,"tools":offered})
            if outcome:
                events.append({"type":"user","session_id":session,"message":{"role":"user","content":[
                    {"type":"tool_result","tool_use_id":"toolu_1","is_error":outcome=="refused",
                     "content":"Error: No such tool available: "+tool if outcome=="refused" else "done"}]}})
            events.append(result)
            return code,b"".join(canonical(event)+b"\n" for event in events),b""

        with patch.dict(os.environ,{"CLAUDE_CODE_OAUTH_TOKEN":"fake-oauth-for-boundary-test"}):
            response,_=isolated_answer(ClaudeCode(auth="subscription",process=process),{"evidence":"e"},
                                       role="critic",system_prompt="Answer.",schema=self.SCHEMA)
        return response,seen["command"]

    def test_two_judges_are_asked_and_each_reply_is_checked_again(self):
        """judge_pair ("Judged outputs" in local-tasks.md): two fresh sessions over one packet, each answering
        every criterion in the judge schema, which Python checks again rather than trusting the CLI."""
        from sci_ai_verifier.claude_runner import ClaudeCode
        from sci_ai_verifier.documentary import JUDGE_RUBRIC,JUDGE_TIMEOUT_SECONDS,judge_pair,judge_schema
        packet={"job":"Advise.","answer":"Block with BSA.","rubric":JUDGE_RUBRIC,
                "criteria":[{"id":"c1","question":"Names BSA?","source_quote":"q"},{"id":"c2","question":"Says why?","source_quote":"q"}]}
        replies=[{"answers":{"c1":{"fact":"It names BSA.","answer":"yes"},"c2":{"fact":"No reason.","answer":"no"}}},
                 {"answers":{"c1":{"fact":"BSA is named.","answer":"yes"},"c2":{"fact":"Silent on why.","answer":"no"}}}]
        seen=[]

        def process(command,**kwargs):
            seen.append((command,kwargs))
            session=command[command.index("--session-id")+1]
            reply=replies[len(seen)-1]
            events=[{"type":"assistant","session_id":session,"message":{"model":"judge-model","role":"assistant","content":[
                        {"type":"tool_use","id":"toolu_1","name":"StructuredOutput","input":reply}]}},
                    {"type":"result","subtype":"success","is_error":False,"session_id":session,"result":"",
                     "structured_output":reply,"total_cost_usd":0.01}]
            return 0,b"".join(canonical(event)+b"\n" for event in events),b""
        with patch.dict(os.environ,{"CLAUDE_CODE_OAUTH_TOKEN":"fake-oauth-for-boundary-test"}):
            value=judge_pair(ClaudeCode(auth="subscription",process=process),packet)
        self.assertEqual(len(seen),2)
        self.assertEqual([item["answers"] for item in value],[reply["answers"] for reply in replies])
        self.assertEqual({item["observed_model_ids"][0] for item in value},{"judge-model"})
        self.assertNotEqual(value[0]["session_id"],value[1]["session_id"])
        for command,kwargs in seen:
            self.assertEqual(json.loads(command[command.index("--json-schema")+1]),judge_schema(["c1","c2"]))
            self.assertEqual((command[command.index("--tools")+1],kwargs["timeout"]),("",JUDGE_TIMEOUT_SECONDS))
            self.assertEqual(json.loads(kwargs["prompt"]),packet)
        # A reply outside the schema the CLI let through is refused here, as a judge fault.
        replies[1]={"answers":{"c1":{"fact":"x","answer":"yes"}}}
        seen.clear()
        with patch.dict(os.environ,{"CLAUDE_CODE_OAUTH_TOKEN":"fake-oauth-for-boundary-test"}),self.assertRaises(Fault) as caught:
            judge_pair(ClaudeCode(auth="subscription",process=process),packet)
        self.assertEqual(caught.exception.code,"judge_response_invalid")

    def test_the_session_gets_the_schema_room_to_correct_and_no_other_tool(self):
        response,command=self.ask()
        self.assertEqual(response["structured_output"],{"answer":"9"})
        self.assertEqual(command[command.index("--json-schema")+1],canonical(self.SCHEMA).decode())
        self.assertEqual(command[command.index("--tools")+1],"")
        self.assertEqual(command[command.index("--max-turns")+1],"4")

    def test_another_tool_given_or_run_is_a_boundary_violation(self):
        for label,options in (("ran",{"tool":"Bash","outcome":"ran"}),
                              ("given",{"offered":["StructuredOutput","Bash"],"outcome":"ran"})):
            with self.subTest(label),self.assertRaises(Fault) as caught:
                self.ask(**options)
            self.assertEqual(caught.exception.code,"critic_boundary_violation")

    def test_a_call_claude_code_refused_ran_nothing_and_the_reply_counts(self):
        """Runs b573cd15 and 4f16f74d each lost a claim to a critique whose `bash` Claude Code refused;
        tests/recorded/critic-refused-tool.jsonl is the second."""
        response,_=self.ask(tool="Bash",offered=["StructuredOutput"],outcome="refused")
        self.assertEqual(response["structured_output"],{"answer":"9"})
        self.assertEqual([(call["name"],call["completed"]) for call in response["tool_calls"]],[("Bash",False)])

    def test_a_session_that_fails_before_answering_is_started_once_more(self):
        """A critique's 429 used to end its claim outright; nothing scientific was observed, so a second fresh
        session is not grade shopping. A reply in shape, and a session the schema stopped, are never retried."""
        from sci_ai_verifier.claude_runner import ClaudeCode
        from sci_ai_verifier.documentary import isolated_answer
        reply={"answer":"9"}

        def process_for(first):
            calls=[]

            def process(command,**kwargs):
                session=command[command.index("--session-id")+1]
                calls.append(session)
                if len(calls)==1 and first=="raise":
                    raise Fault("claude_timeout","fixture")
                failed=len(calls)==1 and first is not None
                result={"type":"result","subtype":first if failed else "success","is_error":failed,"session_id":session,
                        "result":canonical(reply).decode()}
                if not failed:
                    result["structured_output"]=reply
                events=[{"type":"assistant","session_id":session,"message":{"model":"m","role":"assistant","content":[
                            {"type":"tool_use","id":"toolu_1","name":"StructuredOutput","input":reply}]}},result]
                return (1 if failed else 0),b"".join(canonical(event)+b"\n" for event in events),b""
            return process,calls

        def ask(first):
            process,calls=process_for(first)
            with patch.dict(os.environ,{"CLAUDE_CODE_OAUTH_TOKEN":"fake-oauth-for-boundary-test"}):
                response,session=isolated_answer(ClaudeCode(auth="subscription",process=process),{"evidence":"e"},
                                                 role="critic",system_prompt="Answer.",schema=self.SCHEMA)
            return response,session,calls
        response,session,calls=ask(None)
        self.assertEqual((response["session_attempts"],len(calls)),(1,1))
        for first in ("error_during_execution","raise"):
            response,session,calls=ask(first)
            self.assertEqual((response["structured_output"],response["session_attempts"]),(reply,2),first)
            self.assertEqual(len(set(calls)),2,"the second session is fresh")
            self.assertEqual(session,calls[1])
        # A session the schema stopped had its turns to correct its shape; it is not started again.
        with self.assertRaises(Fault) as caught:
            ask("error_max_turns")
        self.assertEqual(caught.exception.code,"critic_response_invalid")
        # Two failures are the limitation they always were.
        process,calls=process_for("error_during_execution")
        always=lambda command,**kwargs:(1,process(command,**kwargs)[1],b"")  # noqa: E731
        with patch.dict(os.environ,{"CLAUDE_CODE_OAUTH_TOKEN":"fake-oauth-for-boundary-test"}),self.assertRaises(Fault) as caught:
            isolated_answer(ClaudeCode(auth="subscription",process=always),{"evidence":"e"},role="critic",
                            system_prompt="Answer.",schema=self.SCHEMA)
        self.assertEqual((caught.exception.code,len(calls)),("critic_unavailable",2))

    def test_a_session_whose_replies_never_met_the_schema_is_an_invalid_reply(self):
        """Probed live on 2026-09-28: a session whose replies the schema refused twice ended as
        error_max_turns, exit code 1."""
        for subtype in ("error_max_turns","error_max_structured_output_retries"):
            with self.subTest(subtype),self.assertRaises(Fault) as caught:
                self.ask(code=1,subtype=subtype,structured=False)
            self.assertEqual(caught.exception.code,"critic_response_invalid")
        with self.assertRaises(Fault) as caught:
            self.ask(structured=False)
        self.assertEqual(caught.exception.code,"critic_response_invalid")
        # Any other failed session is simply unavailable.
        with self.assertRaises(Fault) as caught:
            self.ask(code=1,subtype="error_during_execution",structured=False)
        self.assertEqual(caught.exception.code,"critic_unavailable")


if __name__=="__main__":
    unittest.main()
