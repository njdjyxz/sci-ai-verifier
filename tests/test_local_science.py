"""Independent grade eligibility and assessor boundaries, with no live models."""

import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault,canonical,digest
from sci_ai_verifier.local_science import decide,validate_reviews,POLICY_REF
from sci_ai_verifier.documentary import validate_assessment,RUBRIC,RUBRIC_REF,review_valid
from sci_ai_verifier.local_evaluators import qualify,validate_spec


class ScienceTests(unittest.TestCase):
    def setUp(self):
        self.cases=[{"case_id":str(i)} for i in range(3)]
        self.review={"candidate_fingerprint":"a"*64,"scope":"fixture","reviewer":"independent synthetic fixture",
            "reviewed_at":"2026-09-11","provenance":"test fixture, not a real approval","grades":["A","B","C"],
            "independent":True,"scientific_basis":"fixture","coverage":"fixture","uncertainty":"fixture",
            "independence":"fixture","trial_policy":"all-trials-v1","minimum_trials":1,
            "source_digest":"b"*64,"environment_digest":"c"*64,"model_ids":["fixture-model"]}
        self.audit={"review":self.review,"policy_ref":POLICY_REF}

    def rows(self,n,status="pass"):
        return [{"case_id":case["case_id"],"trial":trial,"comparison_status":status,"model_ids":["fixture-model"]} for case in self.cases for trial in range(1,n+1)]

    def test_unanimous_failure_and_success_have_equal_grade(self):
        for status in ("pass","fail"):
            result=decide(self.audit,self.rows(3,status),self.cases,3)
            self.assertEqual(result["evidence_grade"],"A")
            self.assertEqual(result["scientific_status"],status)

    def test_no_self_approval_synthetic_or_unreviewed(self):
        for audit,synthetic in (({"review":None,"policy_ref":POLICY_REF},False),(self.audit,True)):
            result=decide(audit,self.rows(3),self.cases,3,synthetic=synthetic)
            self.assertIsNone(result["evidence_grade"])
            self.assertIsNone(result["scientific_status"])

    def test_single_trial_caps_c_and_c_requires_separate_authorization(self):
        self.assertEqual(decide(self.audit,self.rows(1),self.cases,1)["evidence_grade"],"C")
        self.audit["review"]["grades"]=["A"]
        self.assertIsNone(decide(self.audit,self.rows(1),self.cases,1)["evidence_grade"])

    def test_missing_duplicate_invalid_and_disagreement(self):
        for rows in (self.rows(3)[:-1],self.rows(3)+self.rows(3)[:1]):
            with self.assertRaises(Fault):
                decide(self.audit,rows,self.cases,3)
        for changed in ("invalid","fail"):
            rows=self.rows(3)
            rows[0]["comparison_status"]=changed
            result=decide(self.audit,rows,self.cases,3)
            self.assertIsNone(result["evidence_grade"])
            self.assertEqual(result["trial_counts"]["evaluated"],9)
            self.assertEqual(result["trial_counts"]["invalid"],int(changed=="invalid"))

    def test_review_cannot_have_unbounded_or_duplicate_authority(self):
        validate_reviews([self.review])
        for reviews in ([self.review,self.review],[{**self.review,"independent":False}],[{**self.review,"minimum_trials":0}]):
            with self.assertRaises(Fault):
                validate_reviews(reviews)

    def test_documentary_response_requires_exact_packet_citations(self):
        packet={"evidence":[{"reference_ref":"b"*64,"quote":"Known source text."}]}
        response={"status":"inconclusive","findings":["Evidence bounded"]*3,
                  "citations":[{"reference_ref":"b"*64,"quote":"Known source"}],"limitations":"Documentary only."}
        validate_assessment(response,packet)
        response["citations"][0]["quote"]="Invented source"
        with self.assertRaises(Fault):
            validate_assessment(response,packet)
        with self.assertRaises(Fault):
            review_valid({"rubric_ref":"wrong","reviewer":"fixture","reviewed_at":"today","provenance":"fixture","independent":True})

    def test_python_candidate_failing_negative_control_is_rejected(self):
        cases=[{"case_id":str(i),"input":"input "+str(i),"expected":str(i),"reference_ref":"b"*64,
                "source_quote":"0 1 2","applicability":"fixture"} for i in range(3)]
        spec={"name":"Fixture","scope":"Fixture","method":"python","code":"print('unused fixture')","limitations":"Synthetic only",
              "cases":cases,"absolute_tolerance":"0","relative_tolerance":"0",
              "controls":[{"case_id":"0","actual":"0","group":group,"expected_status":status}
                for group,status in (("positive","pass"),("negative","fail"),("boundary","pass"),("invalid","invalid"),("held_out","pass"))]}
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
