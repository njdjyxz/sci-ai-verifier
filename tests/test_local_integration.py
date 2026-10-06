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
        # Three trials of three tasks quoted from a retrieved page: ceiling A. Synthetic, so it
        # stays ungraded either way.
        h.ready(target_grade="A")
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

    def test_a_trial_s_binary_files_are_saved_with_their_pins(self):
        h=self.h
        artifact=b"\0generated fixture"
        original=h.subject.observe

        def observe(**request):
            observation=original(**request)
            return {**observation,"artifacts":observation["artifacts"]+[{
                "path":"results/output.bin","sha256":digest(artifact),"bytes":len(artifact),
                "base64":base64.b64encode(artifact).decode()}]}
        h.subject.observe=observe
        h.ready()
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["comparison_status"],"pass")
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertTrue(h.data["report"]["catalog_inventory_ref"])
        for trial in row["tests"]:
            saved={Path(item["saved_path"]).name:Path(item["saved_path"]).read_bytes() for item in trial["artifacts"]}
            self.assertEqual(saved["output.bin"],artifact)
        self.assertIn("Generated files:",Path(h.data["report_markdown_path"]).read_text())


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

class GradeNegotiationTests(unittest.TestCase):
    """The grade is settled by Python's facts and a fresh critique, with no human review."""

    def setUp(self):
        self.h=fixture.LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.packets=[]
        # Three trials of five tasks quoted from a retrieved page: ceiling A.
        self.key=self.build(3)

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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=AssertionError("must not run")):
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual([case["case_id"] for case in self.packets[0]["evidence"]["tasks"]],list(fixture.FIVE_ROWS))
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

    def test_the_critique_judges_searches_by_python_s_record_of_what_the_planner_ran(self):
        """Run 26312681's critiques took two claims' described searches as made, and no search had
        sought their untested facts. The packet now carries the planner's searches from its own
        stream and its fetches from Python's record of each call. Run 1d1c3b6e's record read the
        fetches from the planner's copy of each reply, which the log cuts at 16,000 characters,
        and called five of ten successful fetches unreadable."""
        from sci_ai_verifier.runlog import MAX_TEXT,WorkflowLog,recorded_call
        h=self.h
        log=WorkflowLog(h.base)
        h.subject.log=log

        def planner(*blocks,kind="assistant",role="planner"):
            log.emit("claude_event",role=role,session_id=role+"-session",
                     payload={"type":kind,"message":{"content":list(blocks)}})

        def use(index,name,**given):
            return {"type":"tool_use","id":"use-"+str(index),"name":name,"input":given}

        class Server:
            """Python's tool server, answering a call with `reply` or raising it."""
            def __init__(self,reply):
                self.reply=reply

            def call(self,name,arguments,call_id=None):
                if isinstance(self.reply,BaseException):
                    raise self.reply
                return self.reply

        def fetch(index,reply,tool="fetch_local_reference",**given):
            planner(use(index,"mcp__verifier_internal__"+tool,**given))
            try:
                recorded_call(log,Server(reply),tool,given)
            except Fault:
                pass

        long_page={"status":"ok","data":{"outcome":"reference_fetched","untrusted_reference":{"text":"x"*MAX_TEXT}}}
        planner(use(1,"WebSearch",query="before any claim was named"))
        planner(use(2,"mcp__verifier_internal__list_local_candidates",claim_id=h.claim_id))
        planner(use(3,"WebSearch",query="fixture table alpha beta gamma"))
        fetch(4,{"status":"ok","data":{"outcome":"reference_fetched"}},claim_id=h.claim_id,url="https://example.org/reference")
        # The log keeps no whole copy of a long reply; the fetch still succeeded.
        fetch(5,long_page,claim_id=h.claim_id,url="https://example.org/long")
        planner({"type":"tool_result","tool_use_id":"use-5","content":[{"type":"text","text":json.dumps(long_page)}]},
                kind="user")
        fetch(6,{"status":"retryable","error":{"code":"reference_unavailable"}},claim_id="claim-other",
              url="https://example.org/blocked")
        planner(use(7,"WebSearch",query="another claim's source"))
        # Only the planner's stream counts: a subject session's tool calls are not the planner's searches.
        planner(use(8,"WebSearch",query="a subject's search"),role="subject")
        fetch(9,Fault("resource_timeout","slow"),tool="load_local_resource",claim_id=h.claim_id,resource_name="table")
        # A call that never reached Python's tools fetched nothing.
        planner(use(10,"mcp__verifier_internal__fetch_local_reference",claim_id=h.claim_id,url="https://example.org/unserved"))
        # Shapes in no expected form never fail the selection.
        log.emit("tool_started",tool="fetch_local_asset",invocation_id=["not","a","string"],arguments="not an object")
        log.emit("tool_finished",tool="fetch_local_asset",invocation_id=None,status="ok",outcome="asset_fetched")
        planner({"type":"tool_use","id":["not","a","string"],"name":"mcp__verifier_internal__fetch_local_reference",
                 "input":"not an object"})
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        record=self.packets[0]["python_checked"]["search_record"]
        self.assertTrue(record["recorded"])
        self.assertEqual(record["searches"],[{"query":"before any claim was named","for":"no claim yet"},
                                             {"query":"fixture table alpha beta gamma","for":"this claim"},
                                             {"query":"another claim's source","for":"another claim"}])
        self.assertEqual(record["fetches"],[
            {"tool":"fetch_local_reference","url":"https://example.org/reference","for":"this claim",
             "outcome":"reference_fetched"},
            {"tool":"fetch_local_reference","url":"https://example.org/long","for":"this claim",
             "outcome":"reference_fetched"},
            {"tool":"fetch_local_reference","url":"https://example.org/blocked","for":"another claim",
             "outcome":"refused: reference_unavailable"},
            {"tool":"load_local_resource","url":"operator-resource:table","for":"this claim",
             "outcome":"failed: resource_timeout"},
            {"tool":"fetch_local_asset","url":"operator-resource:","for":"no claim yet",
             "outcome":"no result recorded"}])
        self.assertEqual((record["searches_total"],record["fetches_total"]),(3,5))
        # Counted over the whole log, not the listed entries, so a long run still shows a new search.
        self.assertEqual(record["this_claim"],{"searches":1,"fetches":3})
        # The rubric tells the critique to judge a described search by this record.
        self.assertIn("python_checked.search_record",self.packets[0]["rubric"]["criteria"][3])

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

    GAP="The r-squared threshold of Step 3 is untested: no task gives a poor fit, so add one that must be flagged."

    def test_an_agreeing_critique_that_names_gaps_sends_the_claim_back_once_even_at_a(self):
        """Run f84c131c: four critiques agreed with A while naming untested parts of every claim, and the
        question-era return, which skipped A, would not have asked the planner anything."""
        h=self.h
        log=self.planner_log()
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.agreeing("A",[self.GAP])):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            self.assertEqual((h.data["settled_grade"],h.data["coverage_gaps"]),("A",[self.GAP]))
            self.assertIn("once per claim",h.data["message"])
            self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
            # Accepting A at once is the planner saying it searched; Python's record says it did not.
            h.select(self.key,target_grade="A")
            self.assertEqual((h.data["outcome"],h.data["reason"]),("local_grade_proposal_refused","return_unsearched"))
            self.assertEqual(h.data["coverage_gaps"],[self.GAP])
            self.assertEqual(len(self.packets),1,"a refused acceptance spends no session")
            # One search for this claim since the return, and the same grade is accepted with no new session.
            self.planner(log,{"type":"tool_use","id":"use-1","name":"WebSearch",
                              "input":{"query":"dose-response r-squared acceptance threshold"}})
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"A")
        self.assertEqual(len(self.packets),1)
        h.call("execute_local_claim",claim_id=h.claim_id)
        h.call("write_report_card")
        report=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Returned once for coverage gaps: the critique in round 1",report)
        self.assertIn("Coverage gap: "+self.GAP,report)

    def test_the_gap_return_comes_once_and_the_next_design_is_judged_as_usual(self):
        h=self.h
        four=h.candidate(lookup=False,rows=fixture.ROWS+("zeta",),name="Fixture table, four rows")
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.agreeing("A",[self.GAP])):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            h.select(four,target_grade="A")
        # A revised design that still leaves a gap is fixed: the return comes once per claim.
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        # Its critique was told what the earlier one found untested, to check the revision against it.
        self.assertIn("An earlier version left untested: "+self.GAP,self.packets[1]["prior_objections"])

    def test_with_no_workflow_log_the_returned_grade_is_accepted_unchecked(self):
        """No log means no record to check, so Python cannot refuse on it."""
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.agreeing("A",[self.GAP])):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertFalse(self.packets[0]["python_checked"]["search_record"]["recorded"])

    def test_no_return_without_gaps_or_below_an_agreeing_grade(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.agreeing("A")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        # A critique below the proposal sends the claim back as it always did, carrying its gaps.
        key=self.build(3,name="lower")
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.agreeing("B",[self.GAP])):
            h.select(key,target_grade="A")
        self.assertEqual((h.data["outcome"],h.data["settled_grade"]),("local_grade_revision_required","B"))
        self.assertEqual(h.data["coverage_gaps"],[self.GAP])
        self.assertNotIn("message",h.data)

    def test_a_wrong_skill_earns_the_same_grade_with_a_failing_verdict(self):
        h=self.h
        h.subject.mode="wrong"
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A")
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["evidence_grade"],"A")
        self.assertEqual(h.data["result"]["scientific_status"],"fail")
        self.assertFalse(h.data["result"]["ai_involvement"]["verdict"])

    def test_critique_lowers_the_grade_and_the_planner_settles_at_what_it_supports(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("C")):
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
            self.assertIn("correctly following the skill",packet["rubric"]["case_verdicts"]["beyond_scope"])
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("C")):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            # Every task counted, so the count is not what holds the grade down; the reply says so.
            gap=h.data["case_gap"]
            self.assertEqual(gap["tasks_needed"],0)
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("A")):
            h.select(key,target_grade="C")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        self.assertEqual(h.data["audit"]["evidence_ceiling"],"C")
        self.assertEqual(h.data["audit"]["settled_ceiling"],"C")
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["evidence_grade"],"C")

    def test_a_changed_design_earns_a_new_round_that_sees_the_prior_objections(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("C")):
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

    def test_rejected_tasks_cap_the_grade_even_when_the_critique_supports_a(self):
        """Run d87a6d5c: the critique counted two of five cases and still supported A."""
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",
                   side_effect=self.rejecting("A",{"gamma":"duplicate","zeta":"beyond_scope","eta":"leaked"})):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        self.assertEqual(h.data["supported_grade"],"A")
        self.assertEqual(h.data["settled_grade"],"B")
        self.assertEqual(h.data["audit"]["counted_cases"],["alpha","beta"])
        self.assertEqual([item["case_id"] for item in h.data["case_replacements"]],["gamma","zeta","eta"])
        self.assertTrue(all(item["replacement"] for item in h.data["case_replacements"]))
        self.assertEqual(h.data["replacement_rounds_remaining"],1)
        # Run 31b67427's planner accepted B believing it lacked a case it already had.
        # Python states what A still needs over the counted tasks instead.
        gap=h.data["case_gap"]
        self.assertEqual({key:gap[key] for key in ("grade","tasks_required","tasks_counted","tasks_needed")},
                         {"grade":"A","tasks_required":3,"tasks_counted":2,"tasks_needed":1})
        self.assertIn("add at least 1 more task.",gap["summary"])
        self.assertNotIn("critique's own grade",gap["summary"])
        # The critique saw every task, each with its ID.
        self.assertEqual([case["case_id"] for case in self.packets[0]["evidence"]["tasks"]],list(fixture.FIVE_ROWS))

    def test_the_next_reviewer_is_told_which_tasks_were_not_counted_and_why(self):
        h=self.h
        # Three of five not counted leaves two, short of A, so a revision is asked for.
        rejected={"gamma":"duplicate","zeta":"leaked","eta":"duplicate"}
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.rejecting("A",rejected)):
            h.select(self.key,target_grade="A")
            replaced=h.candidate(lookup=False,rows=fixture.FIVE_ROWS,name="Fixture table, three replaced")
            h.select(replaced,target_grade="A")
        self.assertEqual(self.packets[0]["prior_objections"],[])
        carried=self.packets[1]["prior_objections"]
        self.assertEqual(len(carried),3)
        self.assertIn("task eta was not counted (duplicate)",carried[2])
        self.assertIn("Suggested replacement:",carried[2])
        # A verdict is not a grade, and no grade travels with it.
        self.assertNotIn("supported_grade",canonical(self.packets[1]).decode())

    def test_a_note_telling_the_reviewer_an_earlier_outcome_is_refused_before_any_session(self):
        """Run b0955d2f: the planner's own notes told reviewers what earlier ones decided."""
        h=self.h
        # Its real words, from a justification and from a case's applicability.
        told_grade="The previous round settled at C because both generated cases leaked their answers."
        told_verdict="Two independent critiques have given this case the verdict counts."
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("A")):
            h.select(self.key,target_grade="A",stronger_grade_considered=told_grade)
            self.assertEqual(h.data["outcome"],"local_grade_proposal_refused")
            self.assertEqual(h.data["reason"],"prior_review_in_packet")
            self.assertEqual((h.data["field"],h.data["phrase"]),("stronger_grade_considered","previous round"))
            self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
            # A note fixed at qualification needs a revised candidate.
            cases=[{**fixture.task(name,h.claims[0]["sections"],h.reference_ref),
                    "applicability":told_verdict if index==1 else "Fixture table row"}
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic(target)):
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("A")):
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("none")):
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
        self.assertIn("Trial 1 of task alpha reached this verifier's per-trial limit of "+str(limit)
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("C")):
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

    def test_two_replacement_rounds_then_the_counting_tasks_settle_the_grade(self):
        h=self.h
        rejected={"gamma":"duplicate","zeta":"beyond_scope","eta":"unsound"}
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.rejecting("A",rejected)):
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
        # Uncounted tasks still run, but their trials do not decide the claim.
        h.call("execute_local_claim",claim_id=h.claim_id)
        result=h.data["result"]
        self.assertEqual(len(h.subject.requests),15)
        self.assertEqual(result["evidence_grade"],"B")
        # The card says why: the limit is recorded over the counted tasks, not the proposal's.
        self.assertIn("fewer_than_three_counting_tasks",result["grade_limit_reasons"])
        self.assertEqual(result["accuracy"]["evaluated"],6)
        self.assertEqual(result["completeness"]["planned_cases"],2)
        self.assertEqual([item["case_id"] for item in result["uncounted_cases"]],["gamma","zeta","eta"])
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual({case["case_id"] for case in row["tests"] if not case["counted"]},{"gamma","zeta","eta"})
        self.assertEqual(len(row["tests"]),15)
        markdown=Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Task zeta not counted (beyond_scope)",markdown)

    def test_an_uncounted_task_that_fails_cannot_fail_the_claim(self):
        """A task outside the claim measures something else; its fail would be a false fail."""
        h=self.h
        original=h.subject.observe
        wrong=fixture.results(999.0)

        def observe(**request):
            observation=original(**request)
            if fixture.row_of(request["case_input"])!="eta":
                return observation
            return {**observation,"artifacts":[{"path":fixture.RESULTS_FILE,"sha256":digest(wrong),"bytes":len(wrong),
                                                "base64":base64.b64encode(wrong).decode()}]}
        h.subject.observe=observe
        rejected={"gamma":"duplicate","zeta":"leaked","eta":"beyond_scope"}
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.rejecting("A",rejected)):
            h.select(self.key,target_grade="A")
            self.assertEqual(h.data["outcome"],"local_grade_revision_required")
            h.select(self.key,target_grade="B")
        self.assertEqual(h.data["outcome"],"local_plan_fixed")
        h.call("execute_local_claim",claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["scientific_status"],"pass")
        self.assertEqual(h.data["result"]["comparison_status"],"pass")
        self.assertEqual(h.data["result"]["accuracy"],{"matched":6,"evaluated":6,"ratio":1.0})
        # Its source supports A; only its two independent tasks held it at B, and the report says so.
        h.call("write_report_card")
        row=h.data["report"]["claims"][0]
        self.assertEqual(row["size_limited"],{"source_supports":"A","settled":"B","unit":"tasks","counting":2,
                                              "counting_needed":3})
        self.assertIn("Limited by its number of independent tasks, not its source: the source supports A, but 2 "
                      "tasks counted, where A needs 3.",
                      Path(h.data["report_markdown_path"]).read_text(encoding="utf-8"))

    def test_critique_supporting_no_grade_leaves_the_comparison_ungraded(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("none")):
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("D")):
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
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("D")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"local_grade_revision_required")
        self.assertEqual(h.data["claim_states"][h.claim_id],"local_discovery")
        reference=h.runtime.store.get_json(self.key)["cases"][0]["outputs"][0]["reference_ref"]
        refused=h.runtime.call("assess_local_documentary",
                               {"run_id":h.data["run_id"],"state_token":h.data["state_token"],
                                "claim_id":h.claim_id,"limitations":"Skipping execution.",
                                "evidence":[{"reference_ref":reference,"quote":fixture.REFERENCE}]})
        self.assertEqual(refused["status"],"retryable")
        self.assertEqual(refused["error"]["code"],"stronger_evidence_available")

    def test_unavailable_critic_is_operational_and_never_a_grade(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=Fault("critic_unavailable","fixture")):
            h.select(self.key,target_grade="A")
        self.assertEqual(h.data["outcome"],"critic_unavailable")
        self.assertEqual(h.data["limitation"]["asserted_by"],"runtime")
        self.assertIsNone(h.data["limitation"]["scientific_status"])

    def test_completed_independent_assessment_is_grade_d_without_any_operator_review(self):
        h=self.h
        with patch("sci_ai_verifier.documentary.critique_tasks",side_effect=self.critic("none")):
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
                             evidence=[{"reference_ref":h.runtime.store.get_json(key)["cases"][0]["outputs"][0]["reference_ref"],
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
