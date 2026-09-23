"""Integrated local paths with real journal/storage and explicitly synthetic subjects."""

import base64
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import test_local as fixture
from independent_double import INDEPENDENCE,assessor_reply,critic_reply
from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import Fault,canonical,digest
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.local_catalog import export_bundle,import_bundle
from sci_ai_verifier.catalog_publication import publish,review
from sci_ai_verifier.documentary import RUBRIC_REF
from sci_ai_verifier.storage import Store
from sci_ai_verifier.subject_server import TextRuntime

REDISTRIBUTION="Synthetic fixture reference; licence unknown, redistribution assessed as test-only."


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
        # Three trials of a retrieved token-exact design with three cases: ceiling B, since
        # A needs five counting cases. Synthetic, so it stays ungraded either way.
        h.ready(target_grade="B")
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
            # Built through validate_assessment against this very packet, so the fixture
            # citations must really quote the evidence the runtime supplied.
            return assessor_reply(packet,"inconclusive",args["evidence"])
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
        raw=export_bundle(self.h.runtime.store,[key],redistribution=REDISTRIBUTION)
        other=Store(self.h.base/"other")
        self.assertEqual(import_bundle(other,raw,load_configuration())["candidate_refs"],[key])
        self.assertFalse(import_bundle(other,raw,load_configuration())["scientific_approval_imported"])
        broken=json.loads(raw)
        broken["objects"][key]=base64.b64encode(b"altered").decode()
        with self.assertRaises(Fault):
            import_bundle(other,canonical(broken),load_configuration())
        # The preparer must still record what it assessed; it just no longer needs a sign-off.
        with self.assertRaises(Fault):
            export_bundle(self.h.runtime.store,[key],redistribution="")


class PublicationTests(unittest.TestCase):
    """The draft pull request is the review request; a person merges it."""

    def setUp(self):
        self.h=fixture.LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.key=self.h.ready()
        self.file=self.h.base/"proposal.json"
        self.file.write_bytes(export_bundle(self.h.runtime.store,[self.key],redistribution=REDISTRIBUTION))
        self.posted=False
        self.commits=[]
        self.branch_head=None
        self.patches=[]
        self.opened=0
        self.lose_reply=False

    def revise(self):
        """Re-export the same candidate with a different recorded assessment."""
        self.file.write_bytes(export_bundle(self.h.runtime.store,[self.key],
                                            redistribution=REDISTRIBUTION+" Revised after review."))

    def fake(self,command,**kwargs):
        endpoint=command[4]
        method=command[command.index("--method")+1] if "--method" in command else None
        body=json.loads(kwargs["prompt"]) if kwargs["prompt"] else None
        if method=="PATCH":
            self.patches.append(body["sha"])
            self.branch_head=body["sha"]
            result={}
        elif "pulls?" in endpoint:
            result=[{"html_url":"https://github.com/fixture/repo/pull/1"}] if self.posted else []
        elif endpoint.endswith("git/ref/heads/main"):
            result={"object":{"sha":"base"}}
        elif endpoint.endswith("git/commits/base") or endpoint.endswith("git/commits/commit-1"):
            result={"tree":{"sha":endpoint.rsplit("/",1)[-1]+"-tree"}}
        elif endpoint.endswith("git/trees"):
            self.assertEqual(len(body["tree"]),1)
            self.paths=[*getattr(self,"paths",[]),body["tree"][0]["path"]]
            result={"sha":"new-tree"}
        elif endpoint.endswith("git/commits"):
            self.commits.append(body["parents"][0])
            result={"sha":"commit-"+str(len(self.commits))}
        elif "matching-refs" in endpoint:
            result=[{"ref":"refs/heads/"+endpoint.rsplit("heads/",1)[-1],
                     "object":{"sha":self.branch_head}}] if self.branch_head else []
        elif endpoint.endswith("git/refs"):
            self.branch_head=body["sha"]
            result={}
        elif endpoint.endswith("pulls"):
            self.assertTrue(body["draft"])
            self.assertIn("not scientific approval",body["body"])
            self.posted=True
            self.opened+=1
            if self.lose_reply:
                return 1,b"",b"lost reply"
            result={"html_url":"https://github.com/fixture/repo/pull/1"}
        else:
            self.fail(endpoint)
        return 0,canonical(result),b""

    def publish(self):
        with patch("shutil.which",return_value="gh.exe"):
            return publish(self.file,"fixture/repo",process=self.fake)

    def test_prepared_bundle_opens_one_draft_pull_request_without_a_prior_sign_off(self):
        result=self.publish()
        self.assertTrue(result["pull_request_url"].endswith("/1"))
        self.assertEqual(self.commits,["base"])
        self.assertEqual(self.paths,["catalog/proposals/"+result["proposal_id"]+".json"])
        # A repeat of the same unchanged proposal pushes nothing.
        self.assertEqual(self.publish()["pull_request_url"],result["pull_request_url"])
        self.assertEqual(self.commits,["base"])
        self.assertEqual(self.opened,1)

    def test_lost_reply_reconciles_instead_of_opening_a_second_pull_request(self):
        self.lose_reply=True
        with self.assertRaises(Fault):
            self.publish()
        self.lose_reply=False
        result=self.publish()
        self.assertEqual(self.commits,["base"])
        self.assertEqual(self.opened,1)
        self.assertTrue(result["pull_request_url"].endswith("/1"))

    def test_revision_after_review_updates_the_same_branch_and_pull_request(self):
        first=self.publish()
        self.revise()
        second=self.publish()
        self.assertEqual(second["pull_request_url"],first["pull_request_url"])
        self.assertEqual(second["branch"],first["branch"])
        self.assertEqual(self.opened,1)
        # The revision is a second commit whose parent is the branch head, not main.
        self.assertEqual(self.commits,["base","commit-1"])
        self.assertEqual(self.patches,["commit-2"])
        self.assertEqual(len(second["revisions"]),2)

    def test_revision_recreates_a_branch_the_reviewer_deleted(self):
        self.publish()
        self.branch_head=None  # GitHub deletes the branch on merge.
        self.revise()
        self.publish()
        self.assertEqual(self.commits,["base","base"])
        self.assertEqual(self.patches,[])
        self.assertEqual(self.branch_head,"commit-2")
        self.assertEqual(self.opened,1)

    def test_foreign_branch_is_never_overwritten(self):
        self.branch_head="someone-elses-commit"
        with patch("shutil.which",return_value="gh.exe"),self.assertRaises(Fault) as caught:
            publish(self.file,"fixture/repo",process=self.fake)
        self.assertEqual(caught.exception.code,"publication_conflict")

    def test_review_returns_the_human_comments_to_address(self):
        self.publish()
        def replies(command,**kwargs):
            endpoint=command[4]
            if endpoint.endswith("pulls/1"):
                result={"state":"open","draft":True,"merged":False,"mergeable_state":"clean"}
            elif "pulls/1/comments" in endpoint:
                result=[{"path":"catalog/proposals/x.json","line":3,"body":"Coverage claim is too strong.",
                         "user":{"login":"reviewer"}}]
            elif "pulls/1/reviews" in endpoint:
                result=[{"state":"CHANGES_REQUESTED","body":"See inline.","user":{"login":"reviewer"}}]
            elif "issues/1/comments" in endpoint:
                result=[]
            else:
                self.fail(endpoint)
            return 0,canonical(result),b""
        with patch("shutil.which",return_value="gh.exe"):
            found=review(self.file,"fixture/repo",process=replies)
        self.assertEqual(found["reviews"][0]["state"],"CHANGES_REQUESTED")
        self.assertEqual(found["inline_comments"][0]["author"],"reviewer")
        self.assertFalse(found["merged"])
        self.assertIn("revision",found["next_step"])

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
            h.select(generated,target_grade="B")
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


class GradeNegotiationTests(unittest.TestCase):
    """The grade is settled by Python's facts and a fresh critique, with no human review."""

    def setUp(self):
        self.h=fixture.LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.packets=[]
        # Three trials of a retrieved, token-exact, installed-method comparison: ceiling A.
        self.key=self.build(3)

    def build(self, trial_count, name="graded"):
        h=self.h
        # A non-synthetic subject identity is what makes a grade reachable at all.
        h.subject.identity={"adapter_id":"local-fixture","model_id":"fixture-model","synthetic":False}
        h.subject.settings={**load_configuration(),"trial_count":trial_count}
        h.runtime=Runtime(h.base/name,h.source,fixture.ROOT/"skills/scientific-verifier",
                          profile="local",subject_adapter=h.subject)
        h.data=h.runtime.call("start_verifier_run",{"source_path":str(h.source)})["data"]
        h.call("load_submitted_skill",source_path=str(h.source))
        h.snapshot=h.data["snapshot"]
        h.extract()
        return h.candidate(rows=fixture.FIVE_ROWS)

    def critic(self,supported):
        def run(adapter,packet):
            self.packets.append(packet)
            # Built through validate_critique, so this reply is one the runtime would accept.
            return critic_reply(packet,supported,
                                objections=[] if supported=="A" else ["Three rows do not cover the whole stated scope."],
                                required_revisions=[] if supported=="A" else ["Add cases drawn from the rest of the table."])
        return run

    def test_overclaimed_grade_is_refused_before_any_critique_runs(self):
        h=self.h
        # One trial per case cannot support A or B, whatever the source is.
        key=self.build(1,name="single-trial")
        with patch("sci_ai_verifier.documentary.critique",side_effect=AssertionError("must not run")):
            h.select(key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_grade_proposal_refused")
        self.assertEqual(h.data["reason"],"above_evidence_ceiling")
        self.assertEqual(h.data["evidence_ceiling"],"C")
        self.assertIn("model_subject_trial_count_below_three",h.data["evidence_limits"])
        self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
        self.assertFalse(self.packets)
        # A grade outside the plan range is rejected by the published tool schema.
        response=h.runtime.call("select_local_candidate",{
            "run_id":h.data["run_id"],"state_token":h.data["state_token"],
            "claim_id":h.claim_id,"candidate_ref":key,"target_grade":"D",
            "applicability":"x","oracle_independence":"x","coverage":"x","tolerance_basis":"x",
            "uncertainty":"x","stronger_grade_considered":"x"})
        self.assertEqual(response["status"],"retryable")
        self.assertEqual(response["error"]["code"],"invalid_arguments")

    def test_retrieved_oracle_and_agreeing_critique_reach_grade_a_with_no_human_step(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["evidence_ceiling"],"A")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"A")
        self.assertEqual(h.data["audit"]["critique_rounds"],1)
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(result["evidence_grade"],"A")
        self.assertEqual(result["scientific_status"],"pass")
        self.assertEqual(result["grade_limit_reasons"],[])
        self.assertFalse(result["ai_involvement"]["verdict"])
        h.call("write_report_card")
        self.assertIn("evidence grade: A",Path(h.data["report_markdown_path"]).read_text(encoding="utf-8"))

    def test_a_wrong_skill_earns_the_same_grade_with_a_failing_verdict(self):
        h=self.h
        h.subject.mode="wrong"
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["evidence_grade"],"A")
        self.assertEqual(h.data["result"]["scientific_status"],"fail")

    def test_critique_lowers_the_grade_and_the_planner_settles_at_what_it_supports(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("C")):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            self.assertEqual(h.data["supported_grade"],"C")
            self.assertTrue(h.data["objections"])
            self.assertEqual(h.data["audit"]["evidence_ceiling"],"A")
            self.assertEqual(h.data["rounds_remaining"],4)
            h.select(self.key,target_grade="C")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"C")
        self.assertEqual(h.data["audit"]["critique_rounds"],2)
        # Accepting the grade this exact design was critiqued at spends no second session.
        self.assertEqual(len(self.packets),1)
        # The critique never sees the planning conversation or the subject's answers.
        for packet in self.packets:
            self.assertEqual(set(packet),{"claim","proposed_grade","rubric","prior_objections",
                                          "evidence","justification","python_checked"})
            self.assertNotIn("observations",canonical(packet).decode())
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(result["evidence_grade"],"C")
        self.assertEqual(result["scientific_status"],"pass")
        self.assertEqual(result["proposed_grade"],"C")
        h.call("write_report_card")
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("evidence grade: C",markdown)
        self.assertIn("Independent critique supported grade C",markdown)
        self.assertNotIn("SYNTHETIC",markdown)

    def test_arguing_without_changing_the_design_spends_no_session_or_round(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("C")):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            for _ in range(3):
                h.select(self.key,target_grade="A")
                self.assertEqual(h.data["outcome"],"local_design_unchanged")
        self.assertEqual(len(self.packets),1)
        self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
        self.assertTrue(h.data["objections"])

    def test_a_critique_naming_more_than_the_facts_support_is_still_capped(self):
        h=self.h
        key=self.build(1,name="single-trial")  # One trial per case: ceiling C.
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(key,target_grade="C")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["evidence_ceiling"],"C")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"C")
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["evidence_grade"],"C")

    def test_a_changed_design_earns_a_new_round_that_sees_the_prior_objections(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("C")):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            # Strengthening the evidence is what buys another round.
            stronger=h.candidate(lookup=False,rows=fixture.FIVE_ROWS,name="Fixture table, wider coverage",
                                 limitations="Fictional reference; coverage extended after review.")
            h.select(stronger,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        self.assertEqual(h.data["audit"]["critique_rounds"],2)
        self.assertEqual(len(self.packets),2)
        # The second reviewer is told what was objected to, and never what grade was given.
        self.assertEqual(self.packets[0]["prior_objections"],[])
        self.assertTrue(self.packets[1]["prior_objections"])
        # The rubric names every grade, so the packet is bound to contain the letters. What
        # it must not carry is a field holding the earlier verdict, or anything beyond the
        # objection text itself.
        self.assertNotIn("supported_grade",canonical(self.packets[1]).decode())
        self.assertEqual(self.packets[1]["prior_objections"],
                         ["Three rows do not cover the whole stated scope."])

    def rejecting(self,supported,rejected):
        def run(adapter,packet):
            self.packets.append(packet)
            return critic_reply(packet,supported,rejected=rejected)
        return run

    def test_rejected_cases_cap_the_grade_even_when_the_critique_supports_a(self):
        """Run d87a6d5c: the critique counted two of five cases and still supported A."""
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",
                   side_effect=self.rejecting("A",{"zeta":"beyond_scope","eta":"leaked"})):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        self.assertEqual(h.data["supported_grade"],"A")
        self.assertEqual(h.data["settled_grade"],"B")
        self.assertEqual(h.data["audit"]["counted_cases"],["alpha","beta","gamma"])
        self.assertEqual([item["case_id"] for item in h.data["case_replacements"]],["zeta","eta"])
        self.assertTrue(all(item["replacement"] for item in h.data["case_replacements"]))
        self.assertEqual(h.data["replacement_rounds_remaining"],1)
        # The critique saw every case, each with its ID and the design's answer form.
        self.assertEqual([case["case_id"] for case in self.packets[0]["evidence"]["cases"]],list(fixture.FIVE_ROWS))
        self.assertEqual({case["answer_form"] for case in self.packets[0]["evidence"]["cases"]},{"generated"})

    def test_the_next_reviewer_is_told_which_cases_were_not_counted_and_why(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",
                   side_effect=self.rejecting("A",{"eta":"duplicate"})):
            h.select(self.key,target_grade="A")
            replaced=h.candidate(lookup=False,rows=fixture.FIVE_ROWS,name="Fixture table, eta replaced")
            h.select(replaced,target_grade="A")
        self.assertEqual(self.packets[0]["prior_objections"],[])
        carried=self.packets[1]["prior_objections"]
        self.assertEqual(len(carried),1)
        self.assertIn("case eta was not counted (duplicate)",carried[0])
        self.assertIn("Suggested replacement:",carried[0])
        # A verdict is not a grade, and no grade travels with it.
        self.assertNotIn("supported_grade",canonical(self.packets[1]).decode())

    def test_carried_concerns_keep_the_latest_round_when_they_overflow(self):
        from sci_ai_verifier.local import prior_objections
        rounds=[{"critique":{"objections":["round %d objection %d"%(number,index) for index in range(8)],
                             "case_verdicts":[{"case_id":"c%d"%index,"verdict":"leaked","reason":"r%d"%number,
                                               "replacement":"x"} for index in range(6)]}} for number in (1,2)]
        carried=prior_objections(rounds)
        self.assertEqual(len(carried),16)
        # Round 2's concerns are what the next design must answer; none of them is dropped.
        self.assertTrue(all(any("round 2 objection %d"%index==item for item in carried) for index in range(8)))
        self.assertEqual(sum("(leaked): r2" in item for item in carried),6)

    def test_a_mixed_design_reaches_a_with_two_open_cases_among_five(self):
        h=self.h
        options=fixture.LocalTests.OPTIONS
        cases=[{"case_id":name,"input":name,"expected":str(index)+".0","reference_ref":h.reference_ref,
                "source_quote":fixture.REFERENCE,"applicability":"Fixture table row","method":"numeric"}
               for index,name in enumerate(("alpha","beta"),1)]
        # Answers may not all sit at one position, so the middle case answers option 2.
        cases+=[{"case_id":"choice-"+str(index),"method":"choice","expected":"2" if index==1 else "1","options":options,
                 "input":"Row %d? %s"%(index,"; ".join(options)),"reference_ref":h.reference_ref,
                 "source_quote":fixture.REFERENCE,"applicability":"Fixture table row"} for index in range(3)]
        # Without its two open cases the design is recognised-only and stops at C. A refused
        # proposal spends no session and leaves the claim in discovery.
        extra=[{**cases[2],"case_id":"choice-"+tag,"input":"Row "+tag+"? "+"; ".join(options)} for tag in ("x","y")]
        recognised=h.candidate(lookup=False,method="mixed",cases=cases[2:]+extra)
        h.select(recognised,target_grade="A")
        self.assertEqual(h.data["reason"],"above_evidence_ceiling")
        self.assertEqual(h.data["evidence_ceiling"],"C")
        self.assertIn("no_generated_case",h.data["evidence_limits"])
        key=h.candidate(lookup=False,method="mixed",cases=cases)
        self.assertEqual(h.data["outcome"],"qualified_local")
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"A")
        forms=[case["answer_form"] for case in self.packets[0]["evidence"]["cases"]]
        self.assertEqual(forms,["generated"]*2+["recognised"]*3)
        # A choice case travels with its options, so the critique can read what index 1 names.
        self.assertEqual(self.packets[0]["evidence"]["cases"][2]["options"],options)
        self.assertNotIn("options",self.packets[0]["evidence"]["cases"][0])

    def test_two_replacement_rounds_then_the_counting_cases_settle_the_grade(self):
        h=self.h
        rejected={"zeta":"beyond_scope","eta":"naming"}
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.rejecting("A",rejected)):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["replacement_rounds_remaining"],1)
            first=h.candidate(lookup=False,rows=fixture.FIVE_ROWS,name="Fixture table, first replacement")
            h.select(first,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            self.assertEqual(h.data["replacement_rounds_remaining"],0)
            second=h.candidate(lookup=False,rows=fixture.FIVE_ROWS,name="Fixture table, second replacement")
            h.select(second,target_grade="A")
        # Both replacement rounds are spent, so the third rejection settles instead of asking again.
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"B")
        self.assertEqual(h.data["audit"]["critique_rounds"],3)
        self.assertEqual(len(self.packets),3)
        # Uncounted cases still run, but neither their trials nor their answers decide the claim.
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(len(h.subject.requests),15)
        self.assertEqual(result["evidence_grade"],"B")
        # The card says why: the limit is recorded over the counted cases, not the proposal's.
        self.assertIn("fewer_than_five_counting_cases",result["grade_limit_reasons"])
        self.assertEqual(result["accuracy"]["evaluated"],9)
        self.assertEqual(result["completeness"]["planned_cases"],3)
        self.assertEqual([item["case_id"] for item in result["uncounted_cases"]],["zeta","eta"])
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual({case["case_id"] for case in row["tests"] if not case["counted"]},{"zeta","eta"})
        self.assertEqual(len(row["tests"]),15)
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Case zeta not counted (beyond_scope)",markdown)

    def test_an_uncounted_case_that_fails_cannot_fail_the_claim(self):
        """A case outside the claim measures something else; its fail would be a false fail."""
        h=self.h
        original=h.subject.observe
        def observe(**request):
            observation=original(**request)
            return {**observation,"text":"999"} if request["case_input"]["input"]=="eta" else observation
        h.subject.observe=observe
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.rejecting("B",{"eta":"beyond_scope"})):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            h.select(self.key,target_grade="B")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["scientific_status"],"pass")
        self.assertEqual(h.data["result"]["comparison_status"],"pass")
        self.assertEqual(h.data["result"]["accuracy"],{"matched":12,"evaluated":12,"ratio":1.0})

    def test_critique_supporting_no_grade_leaves_the_comparison_ungraded(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("none")):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            self.assertIsNone(h.data["supported_grade"])
            # There is no grade to accept, so reproposing the ceiling accepts that.
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(len(self.packets),1)
        self.assertIsNone(h.data["audit"]["settled_ceiling"])
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["outcome"],"local_documentary_required")
        self.assertIsNone(h.data["result"]["evidence_grade"])
        self.assertIsNone(h.data["result"]["scientific_status"])
        self.assertEqual(h.data["result"]["next_target_grade"],"D")

    def test_a_critique_supporting_d_can_be_accepted_and_the_plan_still_runs(self):
        """For an execution design, D means what "none" means: no execution grade. It used
        to be unacceptable -- D cannot be proposed, and reproposing the ceiling on the same
        design was refused as unchanged -- so run b43780be's planner could neither accept
        the verdict nor run the plan, and abandoned it for documentary."""
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("D")):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            self.assertEqual(h.data["supported_grade"],"D")
            # As with "none": reproposing the ceiling accepts a verdict of no execution grade.
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(len(self.packets),1)  # accepting spends no second session
        self.assertIsNone(h.data["audit"]["settled_ceiling"])
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["outcome"],"local_documentary_required")
        self.assertIsNone(h.data["result"]["evidence_grade"])

    def test_a_selected_plan_cannot_skip_to_documentary_without_running(self):
        """workflow.md refuses documentary while a claim holds a candidate it qualified and
        never executed. The guard asked whether one was *selected* instead, so a plan the
        critique held below its proposal could be abandoned; b43780be lost 18 trials so."""
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("D")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
        reference=h.runtime.store.get_json(self.key)["cases"][0]["reference_ref"]
        refused=h.runtime.call("assess_local_documentary",
                               {"run_id":h.data["run_id"],"state_token":h.data["state_token"],
                                "claim_id":h.claim_id,"limitations":"Skipping execution.",
                                "evidence":[{"reference_ref":reference,"quote":fixture.REFERENCE}]})
        self.assertEqual(refused["status"],"retryable")
        self.assertEqual(refused["error"]["code"],"stronger_evidence_available")

    def test_unavailable_critic_is_operational_and_never_a_grade(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=Fault("critic_unavailable","fixture")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"critic_unavailable")
        self.assertEqual(h.data["limitation"]["asserted_by"],"runtime")
        self.assertIsNone(h.data["limitation"]["scientific_status"])

    def test_completed_independent_assessment_is_grade_d_without_any_operator_review(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("none")):
            h.select(self.key,target_grade="A")
            h.select(self.key,target_grade="A")
        self.assertIsNone(h.data["audit"]["settled_ceiling"])
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["outcome"],"local_documentary_required")
        work=h.runtime.call("get_verifier_context",{"run_id":h.data["run_id"]})["data"]["local_work"][h.claim_id]
        reference=work["reference_refs"][0]

        def assess(adapter,packet):
            return assessor_reply(packet,"pass",[{"reference_ref":reference,"quote":fixture.REFERENCE}])

        with patch("sci_ai_verifier.documentary.assess",side_effect=assess):
            h.call("assess_local_documentary",claim_id=h.claim_id,
                   evidence=[{"reference_ref":reference,"quote":fixture.REFERENCE}],
                   limitations="Documentary consistency only.")
        self.assertEqual(h.data["result"]["evidence_grade"],"D")
        self.assertEqual(h.data["result"]["scientific_status"],"pass")
        # The D rests on an AI judgment in a session that never saw the planning, and the
        # report must disclose both rather than let the grade imply a human reviewed it.
        h.call("write_report_card")
        disclosed=h.data["report"]["claims"][0]["documentary_assessment"]
        self.assertTrue(disclosed["ai_judgment"])
        self.assertEqual(disclosed["independence"],INDEPENDENCE)
        self.assertEqual(disclosed["rubric_ref"],RUBRIC_REF)
        self.assertEqual(h.data["report"]["claims"][0]["record"]["ai_involvement"],
                         {"orchestration":True,"evidence_generation":True,"verdict":True})


class GateTests(unittest.TestCase):
    """Terminal outcomes stay behind evidence Python actually observed."""

    def setUp(self):
        self.h=fixture.LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.h.extract()

    def attempt(self,tool,**args):
        """Call a tool that is expected to be refused, keeping the rotated token usable."""
        h=self.h
        response=h.runtime.call(tool,{"run_id":h.data["run_id"],"state_token":h.data["state_token"],
                                      "claim_id":h.claim_id,**args})
        h.data=response["data"] if response["status"]=="ok" else {**h.data,**{
            key:value for key,value in response["error"].items() if key=="state_token"}}
        return response

    def test_unverified_needs_a_search_python_saw(self):
        h=self.h
        h.call("list_local_candidates",claim_id=h.claim_id)
        refused=self.attempt("record_local_unverified",search_account="I looked and found nothing.",
                             missing_evidence="No sources exist.")
        self.assertEqual(refused["error"]["code"],"evidence_search_required")
        # A retrieved reference is what makes the search account checkable.
        with patch("sci_ai_verifier.local_candidates.fetch_public",return_value=(fixture.REFERENCE.encode(),fixture.REFERENCE)):
            h.call("fetch_local_reference",claim_id=h.claim_id,url="https://example.org/reference",
                   version="fixture-v1",license="Unknown")
        allowed=self.attempt("record_local_unverified",search_account="Retrieved the table; it does not state this value.",
                             missing_evidence="No independent expected answer for the claim's scope.")
        self.assertEqual(allowed["status"],"ok")
        self.assertEqual(allowed["data"]["result"]["evidence_grade"],"U")

    def test_documentary_is_refused_while_a_qualified_candidate_is_unused(self):
        h=self.h
        key=h.candidate()
        self.assertEqual(h.data["outcome"],"qualified_local")
        refused=self.attempt("assess_local_documentary",
                             evidence=[{"reference_ref":h.runtime.store.get_json(key)["cases"][0]["reference_ref"],
                                        "quote":fixture.REFERENCE}],
                             limitations="Skipping execution.")
        self.assertEqual(refused["error"]["code"],"stronger_evidence_available")

    def test_a_fixed_plan_cannot_be_abandoned_by_assertion(self):
        h=self.h
        h.select(h.candidate())
        self.assertEqual(h.data["claim_states"][h.claim_id],"local_ready")
        self.assertEqual(h.data["next_legal_tools"],["execute_local_claim"])
        refused=self.attempt("record_local_limitation",code="claim_not_mechanically_testable",
                             reason="Changed my mind after the audit.")
        self.assertEqual(refused["error"]["code"],"illegal_transition")


if __name__=="__main__":
    unittest.main()
