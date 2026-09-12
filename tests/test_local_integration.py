"""Integrated local paths with real journal/storage and explicitly synthetic subjects."""

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import test_local as fixture
from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import Fault,canonical,digest
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.local_catalog import export_bundle,import_bundle
from sci_ai_verifier.catalog_publication import publish
from sci_ai_verifier.documentary import RUBRIC_REF
from sci_ai_verifier.storage import Store
from sci_ai_verifier.subject_server import TextRuntime


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.h=fixture.LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)

    def full(self):
        h=self.h
        h.subject.settings=load_configuration()
        h.runtime=Runtime(h.base/"full",h.source,fixture.ROOT/"skills/scientific-verifier",profile="local",subject_adapter=h.subject)
        h.data=h.runtime.call("start_verifier_run",{"source_path":str(h.source)})["data"]
        h.call("load_submitted_skill",source_path=str(h.source))
        h.snapshot=h.data["snapshot"]
        h.ready()
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["outcome"],"local_documentary_required")
        self.assertEqual(len(h.subject.requests),9)
        h.data=h.runtime.call("get_verifier_context",{"run_id":h.data["run_id"]})["data"]
        work=h.data["local_work"][h.claim_id]
        reference=work["reference_refs"][0]
        return {"claim_id":h.claim_id,"evidence":[{"reference_ref":reference,"quote":fixture.REFERENCE}],"limitations":"Synthetic documentary check only."}

    def test_repeated_trials_independent_packet_and_ungraded_assessment(self):
        args=self.full()
        def assess(adapter,packet):
            self.assertNotIn("observations",packet)
            self.assertNotIn("candidate",packet)
            self.assertNotIn("planner_conversation",packet)
            return {"assessment":{"status":"inconclusive","findings":["Synthetic fixture"]*3,"citations":args["evidence"],"limitations":"Fixture only"},
                    "session_id":"synthetic-assessor","observed_model_ids":["synthetic"],"rubric_ref":RUBRIC_REF}
        with patch("sci_ai_verifier.documentary.assess",side_effect=assess):
            self.h.call("assess_local_documentary",**args)
        self.h.call("write_report_card")
        row=self.h.data["report"]["claims"][0]
        self.assertIsNone(row["record"]["evidence_grade"])
        self.assertEqual(len(row["tests"]),9)
        self.assertEqual(row["execution_counts"],{"planned":9,"attempted":9,"obtained":9,"evaluated":9,"invalid":0,"missing":0})

    def test_assessor_failure_is_not_masked_by_previous_comparison(self):
        args=self.full()
        with patch("sci_ai_verifier.documentary.assess",side_effect=Fault("assessor_unavailable","fixture")):
            self.h.call("assess_local_documentary",**args)
        self.h.call("write_report_card")
        record=self.h.data["report"]["claims"][0]["record"]
        self.assertEqual(record["code"],"assessor_unavailable")
        self.assertIsNone(record["scientific_status"])
        self.assertEqual(len(record["receipts"]),27)

    def test_catalog_round_trip_requalifies_and_rejects_tampering(self):
        key=self.h.ready()
        raw=export_bundle(self.h.runtime.store,[key],authorization="Synthetic fixture permits redistribution of all included references.")
        other=Store(self.h.base/"other")
        self.assertEqual(import_bundle(other,raw,load_configuration())["candidate_refs"],[key])
        self.assertFalse(import_bundle(other,raw,load_configuration())["scientific_approval_imported"])
        broken=json.loads(raw)
        broken["objects"][key]=base64.b64encode(b"altered").decode()
        with self.assertRaises(Fault):
            import_bundle(other,canonical(broken),load_configuration())
        with self.assertRaises(Fault):
            export_bundle(self.h.runtime.store,[key],authorization="")

    def test_publication_lost_reply_reconciles_without_new_commit(self):
        key=self.h.ready()
        raw=export_bundle(self.h.runtime.store,[key],authorization="Synthetic fixture redistribution permission for this test only.")
        file=self.h.base/"proposal.json"
        file.write_bytes(raw)
        posted=False
        commits=0
        def fake(command,**kwargs):
            nonlocal posted,commits
            endpoint=command[4]
            body=json.loads(kwargs["prompt"]) if kwargs["prompt"] else None
            if "pulls?" in endpoint:
                result=[{"html_url":"https://github.com/fixture/repo/pull/1"}] if posted else []
            elif endpoint.endswith("git/ref/heads/main"):
                result={"object":{"sha":"base"}}
            elif endpoint.endswith("git/commits/base"):
                result={"tree":{"sha":"base-tree"}}
            elif endpoint.endswith("git/trees"):
                self.assertEqual(body["base_tree"],"base-tree")
                self.assertEqual(len(body["tree"]),1)
                result={"sha":"new-tree"}
            elif endpoint.endswith("git/commits"):
                commits+=1
                result={"sha":"new-commit"}
            elif "matching-refs" in endpoint:
                result=[]
            elif endpoint.endswith("git/refs"):
                result={}
            elif endpoint.endswith("pulls"):
                self.assertTrue(body["draft"])
                posted=True
                return 1,b"",b"lost reply"
            else:
                self.fail(endpoint)
            return 0,canonical(result),b""
        with patch("shutil.which",return_value="gh.exe"):
            with self.assertRaises(Fault):
                publish(file,"fixture/repo",approved=False,process=fake)
            with self.assertRaises(Fault):
                publish(file,"fixture/repo",approved=True,process=fake)
            result=publish(file,"fixture/repo",approved=True,process=fake)
        self.assertEqual(commits,1)
        self.assertTrue(result["pull_request_url"].endswith("/1"))

    def test_text_reader_refuses_host_paths_before_read(self):
        root=self.h.source
        (root/"note.md").write_text("allowed content")
        runtime=TextRuntime(root)
        self.assertEqual(runtime.call("read_submitted_file",{"path":"note.md"})["status"],"ok")
        for path in ("../outside","C:/Windows/win.ini","/etc/passwd"):
            self.assertEqual(runtime.call("read_submitted_file",{"path":path})["status"],"unavailable")

    def test_generated_evaluator_trials_and_binary_artifacts_retain_their_pins(self):
        h=self.h
        h.subject.settings={**load_configuration(),"sandbox_image":"sha256:"+"a"*64,"documentary_assessment":False}
        h.runtime=Runtime(h.base/"generated",h.source,fixture.ROOT/"skills/scientific-verifier",profile="local",subject_adapter=h.subject)
        h.data=h.runtime.call("start_verifier_run",{"source_path":str(h.source)})["data"]
        h.call("load_submitted_skill",source_path=str(h.source))
        h.snapshot=h.data["snapshot"]
        h.extract()
        key=h.candidate()
        original=h.runtime.store.get_json(key)
        spec={key:original[key] for key in ("name","scope","limitations","cases")}
        spec.update(method="python",code="print('test scorer is replaced, never executed')",absolute_tolerance="0",relative_tolerance="0",
                    controls=[{"case_id":"alpha","actual":actual,"expected_status":status,"group":group}
                        for group,actual,status in (("positive","1.0","pass"),("negative","2.0","fail"),("boundary","1.0","pass"),("invalid","bad","invalid"),("held_out","1.0","pass"))])
        artifact=b"\0generated fixture"
        original_observe=h.subject.observe
        def observe(**request):
            return {**original_observe(**request),"artifacts":[{"path":"results/output.bin","sha256":digest(artifact),"base64":base64.b64encode(artifact).decode()}]}
        h.subject.observe=observe
        artifact_scores=[]
        def score(spec,case,actual,settings,**kwargs):
            if kwargs.get("artifacts"):
                self.assertEqual(base64.b64decode(kwargs["artifacts"][0]["base64"]),artifact)
                artifact_scores.append(case["case_id"])
            return {"status":"invalid" if actual=="bad" else "pass" if actual==case["expected"] else "fail",
                    "code_sha256":digest(spec["code"].encode()),"image_id":settings["sandbox_image"],"packet_sha256":"c"*64}
        with patch("sci_ai_verifier.local_evaluators.score",side_effect=score):
            h.call("qualify_local_evaluator",claim_id=h.claim_id,specification_json=canonical(spec).decode())
            generated=h.data["candidate_ref"]
            h.call("select_local_candidate",claim_id=h.claim_id,candidate_ref=generated,applicability="Synthetic fixture")
            self.assertEqual(h.runtime.store.get_json(h.data["selection_ref"])["method_version"],"local-python-comparison-1")
            h.call("execute_local_claim",claim_id=h.claim_id)
        h.call("write_report_card")
        self.assertEqual(len(artifact_scores),9)
        row=h.data["report"]["claims"][0]
        self.assertIsNone(row["record"]["evidence_grade"])
        self.assertEqual(row["execution_counts"]["obtained"],9)
        self.assertTrue(h.data["report"]["catalog_inventory_ref"])
        for trial in row["tests"]:
            self.assertEqual(Path(trial["artifacts"][0]["saved_path"]).read_bytes(),artifact)
        self.assertIn("Generated files:",Path(h.data["report_markdown_path"]).read_text())


if __name__=="__main__":
    unittest.main()
