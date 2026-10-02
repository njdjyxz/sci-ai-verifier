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
        # Every case reaches its key from the claim alone unless a test says otherwise: the real
        # probe starts Claude Code sessions, which the fixture subject cannot run.
        self.probed=[]
        patcher=patch("sci_ai_verifier.documentary.claim_probe",side_effect=self.probe())
        patcher.start()
        self.addCleanup(patcher.stop)
        # The AI reader agrees with Python's reader unless a test scripts it: the real reader starts
        # Claude Code sessions, which the fixture subject cannot run.
        from sci_ai_verifier import documentary
        self.readings,self.reading,self.isolated=[],None,documentary.isolated_answer
        reader=patch("sci_ai_verifier.documentary.isolated_answer",side_effect=self.reader)
        reader.start()
        self.addCleanup(reader.stop)
        # Three trials of a retrieved, token-exact, installed-method comparison: ceiling A.
        self.key=self.build(3)

    def reader(self,adapter,packet,*,role,**kwargs):
        """One AI reading: `self.reading(packet)` when a test scripts one, otherwise agreement. Every
        other session role goes to the real function, as it did before the reader existed."""
        if role!="reader":
            return self.isolated(adapter,packet,role=role,**kwargs)
        self.readings.append(packet)
        value=self.reading(packet) if self.reading else {"reading":"differs","answer":packet["reply"].strip(),
                                                          "reason":"Scripted agreement."}
        return ({"structured_output":value,"observed_model_ids":["fixture-model"],"usage":None,
                 "total_cost_usd":0.01},"reader-"+str(len(self.readings)))

    def probe(self,missed=()):
        """Claim-only answers shaped as documentary.claim_probe returns them; `missed` names the
        cases every answer got wrong."""
        def run(adapter,claim,candidate,cache=None):
            self.probed.append({"claim":claim,"cases":[case["case_id"] for case in candidate["cases"]],
                                "cache":sorted(cache or {})})
            return {"kind":"claim-probe","prompt_ref":"fixture","samples_per_case":2,
                    "cases":[{"case_id":case["case_id"],"case_ref":"ref-"+case["case_id"],"expected":case["expected"],
                              "outcome":"missed" if case["case_id"] in missed else "reached",
                              "samples":[{"answer":"UNDETERMINED" if case["case_id"] in missed else case["expected"],
                                          "status":"invalid" if case["case_id"] in missed else "pass"}]*2}
                             for case in candidate["cases"]]}
        return run

    def build(self, trial_count, name="graded", **settings):
        h=self.h
        # A non-synthetic subject identity is what makes a grade reachable at all.
        h.subject.identity={"adapter_id":"local-fixture","model_id":"fixture-model","synthetic":False}
        h.subject.settings={**load_configuration(),"trial_count":trial_count,**settings}
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
        # The critique judges the comparison rule, so it sees each case's answer type.
        self.assertEqual({case["answer_type"] for case in self.packets[0]["evidence"]["cases"]},{"numeric"})
        self.assertIn("term",self.packets[0]["rubric"]["answer_types"])
        self.assertEqual(h.data["audit"]["evidence_ceiling"],"A")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"A")
        self.assertEqual(h.data["audit"]["critique_rounds"],1)
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(result["evidence_grade"],"A")
        self.assertEqual(result["scientific_status"],"pass")
        self.assertEqual(result["grade_limit_reasons"],[])
        self.assertFalse(result["ai_involvement"]["verdict"])
        # A trial Python's reader passed is never read again.
        self.assertEqual(self.readings,[])
        self.assertEqual(result["reading_summary"]["read"],0)
        h.call("write_report_card")
        self.assertIn("evidence grade: A",Path(h.data["report_markdown_path"]).read_text(encoding="utf-8"))

    def test_the_critique_judges_searches_by_python_s_record_of_the_planner_s_stream(self):
        """Run 26312681's critiques took two claims' described searches as made, and no search had
        sought their untested facts. The packet now carries what the planner's own stream shows."""
        from sci_ai_verifier.runlog import WorkflowLog
        h=self.h
        log=WorkflowLog(h.base)
        h.subject.log=log

        def planner(*blocks,kind="assistant",role="planner"):
            log.emit("claude_event",role=role,session_id=role+"-session",
                     payload={"type":kind,"message":{"content":list(blocks)}})

        def use(index,name,**given):
            return {"type":"tool_use","id":"use-"+str(index),"name":name,"input":given}

        def result(index,reply):
            return {"type":"tool_result","tool_use_id":"use-"+str(index),"content":[{"type":"text","text":json.dumps(reply)}]}

        planner(use(1,"WebSearch",query="before any claim was named"))
        planner(use(2,"mcp__verifier_internal__list_local_candidates",claim_id=h.claim_id))
        planner(use(3,"WebSearch",query="fixture table alpha beta gamma"))
        planner(use(4,"mcp__verifier_internal__fetch_local_reference",claim_id=h.claim_id,url="https://example.org/reference"))
        planner(result(4,{"status":"ok","data":{"outcome":"reference_fetched","untrusted_reference":{"text_bytes_total":96}}}),
                kind="user")
        planner(use(5,"mcp__verifier_internal__fetch_local_reference",claim_id="claim-other",url="https://example.org/blocked"))
        planner(result(5,{"status":"retryable","error":{"code":"reference_unavailable"}}),kind="user")
        planner(use(6,"WebSearch",query="another claim's source"))
        # Only the planner's stream counts: a subject session's tool calls are not the planner's searches.
        planner(use(7,"WebSearch",query="a subject's search"),role="subject")
        # A result in no expected shape is reported as such; it never fails the selection.
        planner(use(8,"mcp__verifier_internal__fetch_local_reference",claim_id=h.claim_id,url="https://example.org/odd"))
        planner({"type":"tool_result","tool_use_id":"use-8","content":"not a reply"},kind="user")
        planner(use(9,"mcp__verifier_internal__fetch_local_reference",claim_id=h.claim_id,url="https://example.org/plain"))
        planner(result(9,{"status":"retryable","error":"a bare string"}),kind="user")
        planner({"type":"tool_use","id":["not","a","string"],"name":"mcp__verifier_internal__fetch_local_reference",
                 "input":"not an object"})
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        record=self.packets[0]["python_checked"]["search_record"]
        self.assertTrue(record["recorded"])
        self.assertEqual(record["searches"],[{"query":"before any claim was named","for":"no claim yet"},
                                             {"query":"fixture table alpha beta gamma","for":"this claim"},
                                             {"query":"another claim's source","for":"another claim"}])
        self.assertEqual(record["fetches"],[
            {"tool":"fetch_local_reference","url":"https://example.org/reference","for":"this claim",
             "outcome":"reference_fetched, 96 bytes of text"},
            {"tool":"fetch_local_reference","url":"https://example.org/blocked","for":"another claim",
             "outcome":"refused: reference_unavailable"},
            {"tool":"fetch_local_reference","url":"https://example.org/odd","for":"this claim",
             "outcome":"unreadable result"},
            {"tool":"fetch_local_reference","url":"https://example.org/plain","for":"this claim",
             "outcome":"refused: retryable"},
            {"tool":"fetch_local_reference","url":"operator-resource:","for":"no claim yet",
             "outcome":"no result recorded"}])
        self.assertEqual((record["searches_total"],record["fetches_total"]),(3,5))
        # Counted over the whole stream, not the listed entries, so a long run still shows a new search.
        self.assertEqual(record["this_claim"],{"searches":1,"fetches":3})
        # The rubric tells the critique to judge a described search by this record.
        self.assertIn("search_record",self.packets[0]["rubric"]["coverage"])

    def agreeing(self,supported,gaps=()):
        """A critique that agrees with the proposal, naming `gaps` as coverage_gaps."""
        def run(adapter,packet):
            self.packets.append(packet)
            return critic_reply(packet,supported,coverage_gaps=gaps)
        return run

    def planner_log(self):
        """A workflow log on the subject adapter, with the planner already working on this claim."""
        from sci_ai_verifier.runlog import WorkflowLog
        log=WorkflowLog(self.h.base)
        self.h.subject.log=log
        self.planner(log,{"type":"tool_use","id":"use-0","name":"mcp__verifier_internal__list_local_candidates",
                          "input":{"claim_id":self.h.claim_id}})
        return log

    def planner(self,log,*blocks):
        log.emit("claude_event",role="planner",session_id="planner-session",
                 payload={"type":"assistant","message":{"content":list(blocks)}})

    GAP="Emin as the bottom plateau is untested; the fetched Prism page states it, so ask what Bottom is."

    def test_an_agreeing_critique_that_names_gaps_sends_the_claim_back_once(self):
        """Run 3303fd93's C3: three cases for a twelve-fact claim, proposed at B, and a critique that
        agreed while naming a fetched page that could key two more facts. Nothing reached the planner."""
        h=self.h
        log=self.planner_log()
        three=h.candidate(lookup=False,rows=fixture.ROWS)
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.agreeing("B",[self.GAP])):
            h.select(three,target_grade="B")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            self.assertEqual((h.data["settled_grade"],h.data["coverage_gaps"]),("B",[self.GAP]))
            self.assertIn("once per claim",h.data["message"])
            self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
            # Accepting B at once is the planner saying it searched; Python's record says it did not.
            h.select(three,target_grade="B")
            self.assertEqual((h.data["outcome"],h.data["reason"]),("local_grade_proposal_refused","return_unsearched"))
            self.assertEqual(h.data["coverage_gaps"],[self.GAP])
            self.assertEqual(len(self.packets),1,"a refused acceptance spends no session")
            # One search for this claim since the return, and the same grade is accepted with no new session.
            self.planner(log,{"type":"tool_use","id":"use-1","name":"WebSearch",
                              "input":{"query":"four-parameter logistic Bottom plateau meaning"}})
            h.select(three,target_grade="B")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"B")
        self.assertEqual(len(self.packets),1)
        h.call("execute_local_claim",claim_id=h.claim_id)
        h.call("write_report_card")
        report=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Returned once for coverage gaps",report)
        self.assertIn("Coverage gap: "+self.GAP,report)

    def test_the_gap_return_comes_once_and_the_next_design_is_judged_as_usual(self):
        h=self.h
        three=h.candidate(lookup=False,rows=fixture.ROWS)
        four=h.candidate(lookup=False,rows=fixture.ROWS+("zeta",))
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.agreeing("B",[self.GAP])):
            h.select(three,target_grade="B")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            h.select(four,target_grade="B")
        # A revised design that still leaves a gap is fixed: the return comes once per claim.
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        # Its critique was told what the earlier one found untested, to check the revision against it.
        self.assertIn("An earlier version left a fact untested: "+self.GAP,self.packets[1]["prior_objections"])

    def test_no_return_without_gaps_or_for_a_plan_at_a(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.agreeing("A",[self.GAP])):
            h.select(self.key,target_grade="A")
        # A is the strongest grade, and its critique judged the coverage enough for it.
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        key=self.build(3,name="no-gaps")
        three=h.candidate(lookup=False,rows=fixture.ROWS)
        self.assertTrue(key)
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.agreeing("B")):
            h.select(three,target_grade="B")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")

    REQUEST="Add a case for the zeta row, keyed to the retrieved table."

    def first_round_below(self):
        """Round one: the five-row design proposed at A and settled at B, with one required revision."""
        def run(adapter,packet):
            self.packets.append(packet)
            return critic_reply(packet,"B",objections=["Three rows do not cover the scope."],
                                required_revisions=[self.REQUEST])
        with patch("sci_ai_verifier.documentary.critique",side_effect=run):
            self.h.select(self.key,target_grade="A")
        self.assertEqual(self.h.data["outcome"],"local_grade_revision_required")

    def second_round(self,verdict,*,rows=fixture.ROWS,grade="B",name="Fixture table, revised"):
        """Round two: a revised design whose critique agrees with its grade and gives the carried
        request `verdict`."""
        revised=self.h.candidate(lookup=False,rows=rows,name=name)
        def run(adapter,packet):
            self.packets.append(packet)
            return critic_reply(packet,grade,prior={"zeta row":verdict})
        with patch("sci_ai_verifier.documentary.critique",side_effect=run):
            self.h.select(revised,target_grade=grade)
        return revised

    def test_an_agreeing_critique_that_finds_a_required_revision_unanswered_sends_the_claim_back(self):
        """Run 3303fd93's fourth claim answered two of the five revisions its first critique required,
        and its second critique, never shown them, agreed with B."""
        h=self.h
        log=self.planner_log()
        self.first_round_below()
        three=self.second_round("unanswered")
        # The next critique is shown what the first required, and judges it.
        self.assertIn("An earlier review required: "+self.REQUEST,self.packets[1]["prior_objections"])
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        self.assertEqual([item["concern"] for item in h.data["unanswered_concerns"]],
                         ["An earlier review required: "+self.REQUEST])
        self.assertIn("earlier review requests",h.data["message"])
        with patch("sci_ai_verifier.documentary.critique",side_effect=AssertionError("must not run")):
            h.select(three,target_grade="B")
            self.assertEqual((h.data["outcome"],h.data["reason"]),("local_grade_proposal_refused","return_unsearched"))
            self.planner(log,{"type":"tool_use","id":"use-2","name":"WebSearch",
                              "input":{"query":"zeta row reference table value"}})
            h.select(three,target_grade="B")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        h.call("execute_local_claim",claim_id=h.claim_id)
        h.call("write_report_card")
        report=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Returned for unanswered concerns",report)
        self.assertIn("Earlier concern left unanswered: An earlier review required: "+self.REQUEST,report)

    def test_a_search_the_record_does_not_show_leaves_the_concern_unanswered(self):
        """`searched_no_source` is the critique reading Python's record, and Python checks it."""
        h=self.h
        self.planner_log()
        self.first_round_below()
        self.second_round("searched_no_source")
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        [concern]=h.data["unanswered_concerns"]
        self.assertEqual(concern["verdict"],"unanswered")
        self.assertIn("no search or fetch for this claim since the previous critique",concern["python_checked"])

    def test_a_recorded_search_lets_a_searched_no_source_verdict_stand(self):
        h=self.h
        log=self.planner_log()
        self.first_round_below()
        self.planner(log,{"type":"tool_use","id":"use-3","name":"WebSearch",
                          "input":{"query":"zeta row independent source"}})
        self.second_round("searched_no_source")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")

    def test_an_answered_request_or_a_plan_at_a_settles_at_once(self):
        h=self.h
        self.first_round_below()
        self.second_round("answered")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        # A is the strongest grade: a critique agreeing with it is not overruled for a concern.
        self.key=self.build(3,name="at-a")
        self.first_round_below()
        self.second_round("unanswered",rows=fixture.FIVE_ROWS,grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")

    def test_with_no_workflow_log_the_returned_grade_is_accepted_unchecked(self):
        """No log means no record to check, so Python cannot refuse on it."""
        h=self.h
        three=h.candidate(lookup=False,rows=fixture.ROWS)
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.agreeing("B",[self.GAP])):
            h.select(three,target_grade="B")
            h.select(three,target_grade="B")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertFalse(self.packets[0]["python_checked"]["search_record"]["recorded"])

    def test_a_calculated_design_is_keyed_in_the_sandbox_graded_and_reported(self):
        """Expected answers Python calculated from a quoted formula ("qualify_local_candidate" in
        tool-contracts.md), through the published tools: keyed at qualification, re-checked from
        its receipts at selection, shown whole to the critique, graded A and reported."""
        h,runs=self.h,[]
        key=self.build(3,name="calculated",sandbox_image="fixture-image")

        def calculate(code,inputs,settings,*,log=None):
            runs.append(list(inputs))
            return {"code_sha256":digest(code.encode("utf-8")),"image_id":"sha256:"+"2"*64,
                    "outputs":{value:str(fixture.FIVE_ROWS.index(value)+1)+".0" for value in inputs}}

        # The worked example sits on its own page, so selection must load the anchors' pages too.
        worked="Worked example page: alpha is 1.0 exactly."
        with patch("sci_ai_verifier.local_candidates.fetch_public",return_value=(worked.encode(),worked)):
            h.call("fetch_local_reference",claim_id=h.claim_id,url="https://example.org/worked",
                   version="fixture-v1",license="Unknown; private analysis only")
        calculation={"code":"print('fixture calculation')","reference_ref":h.reference_ref,
                     "formula_quote":"alpha is 1.0, beta is 2.0","anchors":[
                         {"arguments":"alpha","expected":"1.0","reference_ref":h.data["reference_ref"],
                          "source_quote":"alpha is 1.0 exactly"}]}
        cases=[{"case_id":name,"input":name,"arguments":name,"decimals":1,"applicability":"Fixture table row"}
               for name in fixture.FIVE_ROWS]
        with patch("sci_ai_verifier.local_evaluators.calculate",side_effect=calculate):
            key=h.candidate(lookup=False,name="Fixture table, calculated",cases=cases,calculation=calculation)
        self.assertEqual(h.data["outcome"],"qualified_local",h.data["candidate"]["qualification_problems"])
        self.assertEqual([case["expected"] for case in h.data["candidate"]["cases"]],["1.0","2.0","3.0","4.0","5.0"])
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(len(runs),1,"selection re-checks the receipts without running the program again")
        shown=self.packets[-1]["evidence"]
        self.assertEqual(shown["calculation"]["code"],calculation["code"])
        self.assertEqual(shown["calculation"]["anchors"][0]["output"],"1.0")
        self.assertTrue(all(case["calculated"] for case in shown["cases"]))
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual((result["evidence_grade"],result["scientific_status"]),("A","pass"))
        self.assertIn("wrote the program that calculated 5 of the 5",result["ai_involvement"]["evidence_generation"])
        h.call("write_report_card")
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Calculated answers: 5 expected answers were calculated",markdown)
        self.assertIn("- https://example.org/worked; version: fixture-v1",markdown)
        row=json.loads(Path(h.data["report_json_path"]).read_bytes())["claims"][0]
        self.assertEqual(row["calculation"]["receipts"]["anchors"][0]["reproduced"],True)
        self.assertEqual(row["tests"][0]["calculated"],{"arguments":"alpha","decimals":1})

    def test_a_wrong_skill_earns_the_same_grade_with_a_failing_verdict(self):
        h=self.h
        h.subject.mode="wrong"
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["evidence_grade"],"A")
        self.assertEqual(h.data["result"]["scientific_status"],"fail")
        # Every failed trial was read again, and the readings that it differs changed nothing.
        self.assertEqual(len(self.readings),15)
        summary=h.data["result"]["reading_summary"]
        self.assertEqual((summary["read"],summary["changed"],summary["used"]),(15,0,15))
        self.assertEqual(summary["python_reader"]["scientific_status"],"fail")
        self.assertFalse(h.data["result"]["ai_involvement"]["verdict"])

    def test_the_ai_reader_decides_trials_python_cannot_read_and_the_grade_stays(self):
        """A right number inside a sentence is never extracted by Python ("Reading a reply",
        tool-contracts.md). The AI reader reads it, its reading decides those trials, and the
        report says so beside the status Python's reader alone would give."""
        h=self.h
        h.subject.mode="prose"
        self.reading=lambda packet:{"reading":"matches","answer":packet["reply"].rsplit(" ",1)[-1],
                                    "reason":"The sentence gives the expected value."}
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual((result["evidence_grade"],result["scientific_status"]),("A","pass"))
        summary=result["reading_summary"]
        self.assertEqual((summary["read"],summary["changed"],summary["changes"]),(15,15,{"invalid to pass":15}))
        self.assertEqual(summary["python_reader"]["scientific_status"],"inconclusive")
        self.assertEqual(summary["python_reader"]["accuracy"]["matched"],0)
        self.assertIn("trials_decided_by_ai_reader",result["execution_limit_reasons"])
        self.assertIn("By Python's reader alone the status would be inconclusive",result["ai_involvement"]["verdict"])
        # The reader saw the question, its answer form, the key and the reply: never the claim.
        packet=self.readings[0]
        self.assertEqual(set(packet),{"question","answer_format","answer_type","expected_answer","reply"})
        self.assertEqual((packet["answer_type"],packet["expected_answer"],packet["reply"]),("numeric","1.0","The value is 1.0"))
        h.call("write_report_card")
        row=json.loads(Path(h.data["report_json_path"]).read_bytes())["claims"][0]
        test=row["tests"][0]
        self.assertEqual((test["comparison_status"],test["python_status"],test["read_by"]),("pass","invalid","ai_reader"))
        self.assertEqual((test["reading"]["reading"],test["reading"]["answer"]),("matches","1.0"))
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("AI reader: read 15 counted trials Python's reader did not pass, and changed 15 (15 invalid to pass)",markdown)
        self.assertIn("By Python's reader alone the status would be inconclusive, accuracy 0 of 15.",markdown)
        self.assertIn("| pass | AI reader: matches (Python: invalid) |",markdown)
        self.assertIn("- Case alpha, trial 1: used -- matches, answer &#x27;1.0&#x27;: The sentence gives the expected value.",markdown)

    def test_a_reading_python_can_contradict_is_refused_and_the_trial_keeps_its_verdict(self):
        """A reader that calls 999 the expected 1.0 is overruled by Python's own reading of 999."""
        h=self.h
        h.subject.mode="wrong"
        self.reading=lambda packet:{"reading":"matches","answer":"999","reason":"Mistaken."}
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(result["scientific_status"],"fail")
        self.assertEqual((result["reading_summary"]["refused"],result["reading_summary"]["changed"]),(15,0))
        self.assertNotIn("trials_decided_by_ai_reader",result["execution_limit_reasons"])
        self.assertFalse(result["ai_involvement"]["verdict"])

    def test_a_reader_session_that_fails_leaves_python_s_verdict(self):
        h=self.h
        h.subject.mode="prose"
        def fail(packet):
            raise Fault("reader_unavailable","fixture")
        self.reading=fail
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(result["scientific_status"],"inconclusive")
        self.assertEqual((result["reading_summary"]["unavailable"],result["reading_summary"]["changed"]),(15,0))

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
            # Run 84e90683's reviewer counted a case its own objection placed outside the claim.
            self.assertIn("never counts",packet["rubric"]["verdict_consistency"])
            self.assertIn("correctly applying the claim as written",packet["rubric"]["case_verdicts"]["beyond_scope"])
            # Runs 31b67427 and 3b3f3c94: the reviewer lacked the leak shapes and a claim-only test.
            self.assertEqual(len(packet["rubric"]["leak_shapes"]),5)
            self.assertIn("none of these",packet["rubric"]["claim_only_answer"])
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
            # Every case counted, so the count is not what holds the grade down; the reply says so.
            gap=h.data["case_gap"]
            self.assertEqual((gap["counting_needed"],gap["generated_needed"]),(0,0))
            self.assertIn("The critique's own grade, C, is what holds the settled grade down",gap["summary"])
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
        # concerns themselves: the objection and the revision that review required.
        self.assertNotIn("supported_grade",canonical(self.packets[1]).decode())
        self.assertEqual(self.packets[1]["prior_objections"],
                         ["Three rows do not cover the whole stated scope.",
                          "An earlier review required: Add cases drawn from the rest of the table."])

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
        # Run 31b67427's planner accepted B believing it lacked an open case it already had.
        # Python states what A still needs over the counted cases instead.
        gap=h.data["case_gap"]
        self.assertEqual({key:gap[key] for key in ("grade","counting_counted","generated_counted",
                                                    "counting_needed","generated_needed")},
                         {"grade":"A","counting_counted":3,"generated_counted":3,
                          "counting_needed":2,"generated_needed":0})
        self.assertIn("add at least 2 more counting cases of either form",gap["summary"])
        self.assertNotIn("critique's own grade",gap["summary"])
        # The critique saw every case, each with its ID and the design's answer form.
        self.assertEqual([case["case_id"] for case in self.packets[0]["evidence"]["cases"]],list(fixture.FIVE_ROWS))
        self.assertEqual({case["answer_form"] for case in self.packets[0]["evidence"]["cases"]},{"generated"})

    def test_a_case_the_claim_alone_does_not_settle_does_not_count_whatever_the_critique_says(self):
        """Run 3b3f3c94: critiques counted "lone ring atoms", a key narrower than the claim, and a
        subject applying the skill answered "none of these". Sessions given only the claim miss
        such a key, so Python withholds the case from the count. The critique's own verdict is
        kept, and the critique never sees the claim-only answers."""
        h=self.h
        with patch("sci_ai_verifier.documentary.claim_probe",side_effect=self.probe(missed={"eta"})), \
             patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        self.assertEqual(h.data["audit"]["counted_cases"],["alpha","beta","gamma","zeta"])
        self.assertEqual(h.data["settled_grade"],"B")
        replaced=h.data["case_replacements"]
        self.assertEqual([(item["case_id"],item["verdict"],item.get("source")) for item in replaced],
                         [("eta","beyond_scope","claim_probe")])
        self.assertIn("Fresh sessions given only the claim answered 'UNDETERMINED' and 'UNDETERMINED' where the key is",
                      replaced[0]["reason"])
        self.assertTrue(replaced[0]["replacement"])
        self.assertEqual(h.data["case_gap"]["counting_needed"],1)
        verdicts={item["case_id"]:item["verdict"] for item in h.data["audit"]["critique"]["case_verdicts"]}
        self.assertEqual(verdicts["eta"],"counts")
        self.assertEqual(self.probed[-1]["claim"]["statement"],h.claims[0]["statement"])
        self.assertNotIn("UNDETERMINED",canonical(self.packets[0]).decode())
        self.assertNotIn("claim_probe",canonical(self.packets[0]).decode())
        # Accepting B settles on that same critique and its claim-only answers, with no new probe.
        before=len(self.probed)
        with patch("sci_ai_verifier.documentary.critique",side_effect=AssertionError("must not run")):
            h.select(self.key,target_grade="B")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(len(self.probed),before)
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(result["evidence_grade"],"B")
        self.assertEqual([item["case_id"] for item in result["uncounted_cases"]],["eta"])
        h.call("write_report_card")
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Case eta not counted (beyond_scope, from the claim-only answers)",markdown)
        self.assertIn("Claim-only answers: 4 of 5 cases reached their key from the claim alone; 1 missed.",markdown)

    def test_a_changed_design_reuses_the_claim_only_answers_of_its_unchanged_cases(self):
        """A revision usually replaces one or two cases, so only those are asked again."""
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.rejecting("A",{"eta":"duplicate"})):
            h.select(self.key,target_grade="A")
            replaced=h.candidate(lookup=False,rows=fixture.FIVE_ROWS,name="Fixture table, eta replaced")
            h.select(replaced,target_grade="A")
        self.assertEqual(self.probed[0]["cache"],[])
        self.assertEqual(self.probed[1]["cache"],["ref-"+name for name in sorted(fixture.FIVE_ROWS)])

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

    def test_a_note_telling_the_reviewer_an_earlier_outcome_is_refused_before_any_session(self):
        """Run b0955d2f: the planner's own notes told reviewers what earlier ones decided."""
        h=self.h
        # Its real words, from a justification and from a case's applicability.
        told_grade="The previous round settled at C because both generated cases leaked their answers."
        told_verdict="Two independent critiques have given this case the verdict counts."
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A",stronger_grade_considered=told_grade)
            self.assertEqual(h.data["outcome"],"local_grade_proposal_refused")
            self.assertEqual(h.data["reason"],"prior_review_in_packet")
            self.assertEqual((h.data["field"],h.data["phrase"]),("stronger_grade_considered","previous round"))
            self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
            # A note fixed at qualification needs a revised candidate.
            cases=[{"case_id":name,"input":name,"expected":str(index)+".0","reference_ref":h.reference_ref,
                    "source_quote":fixture.REFERENCE,"applicability":told_verdict if index==1 else "Fixture table row"}
                   for index,name in enumerate(fixture.FIVE_ROWS,1)]
            noted=h.candidate(lookup=False,name="Fixture table, annotated",cases=cases)
            h.select(noted,target_grade="A")
            self.assertEqual((h.data["field"],h.data["phrase"]),("applicability of alpha","critiques"))
            self.assertFalse(self.packets)
            # A review article is not an earlier review, and neither refusal spent a round.
            h.select(self.key,target_grade="A",oracle_independence="A peer-reviewed review article retrieved by Python.")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["critique_rounds"],1)
        self.assertEqual(len(self.packets),1)

    def test_only_settled_at_marks_an_earlier_outcome(self):
        """Run 3dc02567: bare "settled" refused an innocent sentence about the design."""
        from sci_ai_verifier.local import PRIOR_REVIEW
        self.assertIsNone(PRIOR_REVIEW.search("No two cases are settled by the same discriminating fact."))
        self.assertTrue(PRIOR_REVIEW.search("The previous round settled at C."))
        self.assertTrue(PRIOR_REVIEW.search("This design settled at B once."))

    def stop_first(self, code, calls=1):
        """The subject raises `code` on its first `calls` trials, then answers normally."""
        h=self.h
        answer=h.subject.observe
        count=[0]

        def observe(**request):
            count[0]+=1
            if count[0]<=calls:
                h.subject.requests.append(request)
                raise Fault(code,"Fixture "+code+".")
            return answer(**request)
        h.subject.observe=observe

    def stopped(self, code, key=None, target="A"):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic(target)):
            h.select(key or self.key,target_grade=target)
        self.stop_first(code)
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["outcome"],code)
        self.assertEqual(len(h.subject.requests),1)

    def test_a_claim_a_refusal_stopped_is_re_run_once_at_the_end_with_both_attempts_reported(self):
        h=self.h
        self.stopped("subject_refused")
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual((row["record"]["evidence_grade"],row["record"]["scientific_status"]),("A","pass"))
        self.assertEqual((row["retry"]["status"],row["retry"]["fault"],row["retry"]["outcome"]),
                         ("retried","subject_refused","local_comparison_complete"))
        self.assertEqual(row["retry"]["first_attempt"]["code"],"subject_refused")
        self.assertIsNone(row["fallback"])  # the re-run cleared it, so nothing stands in
        self.assertEqual(len(h.subject.requests),16)  # one refused, then all fifteen once more
        self.assertIn("Re-run once at the end of the run",Path(h.data["report_markdown_path"]).read_text(encoding="utf-8"))
        # The re-run's trials sit apart from the first attempt's.
        runs=h.runtime.store.root/"subject-runs"/h.data["run_id"]
        self.assertEqual(len(list(runs.glob("claim-*-retry/*-request.json"))),15)
        self.assertEqual(len([path for path in runs.glob("claim-*/*-request.json") if "-retry" not in path.parent.name]),1)

    def test_a_wrong_answer_is_never_re_run(self):
        h=self.h
        h.subject.mode="wrong"
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        h.call("execute_local_claim",claim_id=h.claim_id)
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["record"]["scientific_status"],"fail")
        self.assertIsNone(row["retry"])
        self.assertIsNone(row["fallback"])
        self.assertEqual(len(h.subject.requests),15)

    def test_a_security_fault_is_never_re_run(self):
        h=self.h
        self.stopped("subject_boundary_violation")
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["record"]["code"],"subject_boundary_violation")
        self.assertIsNone(row["retry"])
        self.assertIsNone(row["fallback"])  # a security fault is not a trial fault a D may stand in for
        self.assertEqual(len(h.subject.requests),1)

    def test_a_re_run_the_time_left_cannot_cover_is_skipped_and_says_why(self):
        import os,time
        from sci_ai_verifier.local import DEADLINE_ENV
        h=self.h
        self.stopped("subject_refused")
        with patch.dict(os.environ,{DEADLINE_ENV:str(int(time.time())+60)}):
            h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["retry"]["status"],"skipped")
        self.assertIn("Too little time",row["retry"]["reason"])
        self.assertEqual(row["record"]["code"],"subject_refused")
        self.assertEqual(len(h.subject.requests),1)
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Not re-run: Too little time",markdown)
        # The fallback needs time too, and says so rather than overrunning the deadline.
        self.assertEqual(row["fallback"]["status"],"not_assessed")
        self.assertIn("No fallback documentary assessment: Too little time",markdown)

    def test_a_re_run_the_call_budget_cannot_cover_is_skipped(self):
        h=self.h
        key=self.build(3,name="budget",max_subject_calls=15)
        self.stopped("subject_refused",key=key)
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["retry"]["status"],"skipped")
        self.assertIn("subject-call budget",row["retry"]["reason"])

    def test_an_ungraded_plan_is_not_re_run_because_its_documentary_step_needs_the_planner(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("none")):
            h.select(self.key,target_grade="A")
            h.select(self.key,target_grade="A")
        self.assertIsNone(h.data["audit"]["settled_ceiling"])
        self.stop_first("subject_refused")
        h.call("execute_local_claim",claim_id=h.claim_id)
        packets,assess=self.assessed()
        with patch("sci_ai_verifier.documentary.assess",side_effect=assess):
            h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["retry"]["status"],"skipped")
        self.assertIn("settled no execution grade",row["retry"]["reason"])
        # Its documentary step no longer waits on the planner: Python assembles the fallback.
        self.assertEqual((row["record"]["evidence_grade"],row["fallback"]["status"]),("D","assessed"))

    def assessed(self, status="inconclusive"):
        """An assessor double that keeps every packet it is given and cites its first excerpt."""
        packets=[]

        def assess(adapter,packet):
            packets.append(packet)
            first=packet["evidence"][0]
            return assessor_reply(packet,status,[{"reference_ref":first["reference_ref"],"quote":first["quote"]}])
        return packets,assess

    def timed_out_twice(self, key=None):
        """The first attempt's first trial times out, and so does the re-run's."""
        self.stopped("claude_timeout",key=key)
        self.stop_first("claude_timeout")

    def test_a_claim_its_re_run_did_not_clear_gets_a_fallback_d_that_keeps_the_fault(self):
        """Run 84e90683: both attempts of the ring-option claim timed out and it reported nothing."""
        h=self.h
        self.timed_out_twice()
        packets,assess=self.assessed()
        with patch("sci_ai_verifier.documentary.assess",side_effect=assess):
            h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        record=row["record"]
        self.assertEqual((record["evidence_grade"],record["scientific_status"]),("D","inconclusive"))
        self.assertEqual((record["fault"],record["fallback_for"]["fault"]),("claude_timeout","claude_timeout"))
        self.assertEqual({record[axis] for axis in ("accuracy","consistency","completeness")},{"not_obtained"})
        self.assertEqual((row["retry"]["status"],row["retry"]["outcome"]),("retried","claude_timeout"))
        self.assertEqual(row["fallback"]["status"],"assessed")
        self.assertTrue(row["documentary_assessment"]["ai_judgment"])
        # Python builds the packet from the cases' own quotes, deduplicated; no answer enters it.
        self.assertEqual(set(packets[0]),{"claim","evidence","rubric","limitations"})
        self.assertEqual(packets[0]["evidence"],[{"reference_ref":h.reference_ref,"quote":fixture.REFERENCE,
                                                  "url":"https://example.org/reference","version":"fixture-v1",
                                                  "license":"Unknown; private analysis only"}])
        self.assertEqual(len(h.subject.requests),2)  # one trial per attempt, none after
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Fallback documentary assessment: no execution evidence was obtained",markdown)
        self.assertIn("Runner fault: claude_timeout",markdown)
        self.assertIn("no trial below enters accuracy, status or grade",markdown)

    def test_an_assessor_failure_leaves_the_fault_as_the_outcome(self):
        h=self.h
        self.timed_out_twice()
        with patch("sci_ai_verifier.documentary.assess",side_effect=Fault("assessor_unavailable","fixture")):
            h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual((row["record"]["code"],row["record"]["evidence_grade"]),("claude_timeout",None))
        self.assertEqual(row["fallback"]["status"],"not_assessed")
        self.assertIn("did not complete (assessor_unavailable)",row["fallback"]["reason"])

    def test_no_fallback_is_attempted_while_documentary_assessment_is_off(self):
        h=self.h
        self.timed_out_twice(key=self.build(3,name="no-documentary",documentary_assessment=False))
        with patch("sci_ai_verifier.documentary.assess",side_effect=AssertionError("must not run")):
            h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["record"]["code"],"claude_timeout")
        self.assertEqual(row["fallback"]["status"],"not_assessed")
        self.assertIn("disabled",row["fallback"]["reason"])

    def test_a_timeout_names_the_trial_and_the_limit_it_reached(self):
        """Run 84e90683 said only that no observation returned, while its subject was still working."""
        h=self.h
        self.stopped("claude_timeout")
        reason=h.data["limitation"]["reason"]
        limit=load_configuration()["subject_timeout_seconds"]
        self.assertIn("Trial 1 of case alpha reached this verifier's per-trial limit of "+str(limit)
                      +" s (subject_timeout_seconds)",reason)
        self.assertIn("not a property of the skill",reason)
        self.assertNotIn("does not retry",reason)

    def test_a_long_resource_preview_reaches_the_planner_cut(self):
        from sci_ai_verifier.local_candidates import REPLY_TEXT_BYTES
        h=self.h
        path=h.base/"long-table.txt"
        text="compound,value\n"+"CHEMBL1,1.0\n"*6000
        path.write_bytes(text.encode())  # Bytes, so Windows adds no carriage returns.
        resource={"path":str(path.resolve()),"sha256":digest(path.read_bytes()),"version":"fixture-v1",
                  "license":"Unknown; private analysis only","units":"none","description":"Long fixture table"}
        self.build(3,name="resource",resources={"table":resource})
        h.call("load_local_resource",claim_id=h.claim_id,resource_name="table",format="text")
        shown=h.data["untrusted_reference"]
        self.assertTrue(shown["text_truncated"])
        self.assertEqual(shown["text_bytes_total"],len(text.encode()))
        self.assertLessEqual(len(shown["text"].encode()),REPLY_TEXT_BYTES)

    def test_accepting_a_settled_grade_is_not_checked_because_no_reviewer_reads_it(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique",side_effect=self.critic("C")):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            # Run b0955d2f's claim 1 accepted its grade in words like these.
            h.select(self.key,target_grade="C",
                     stronger_grade_considered="A was proposed on this design and the independent critique settled it at C.")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(len(self.packets),1)

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
        # Only counted trials are read again, so the uncounted case's failures were not.
        self.assertEqual(self.readings,[])
        # Its source supports A; only its four independent cases held it at B, and the report says so.
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["size_limited"],{"source_supports":"A","settled":"B","counting":4,"generated":4,
                                              "counting_needed":5,"generated_needed":2})
        self.assertIn("Limited by its number of independent cases, not its source: the source supports A, but 4 "
                      "cases counted, 4 of them generated, where A needs 5 with 2 generated.",
                      Path(h.data["report_markdown_path"]).read_text(encoding="utf-8"))

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
