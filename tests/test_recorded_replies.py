"""The independent-session boundary, driven by replies a real session actually sent.

Every other test in this suite hands the reply validators a dict written by the test author,
so those tests cannot observe a disagreement between what the code demands and what a fresh
Claude session emits. That disagreement is exactly what discarded three completed critiques
in local run a392ea65. The recordings under `tests/recorded/` are real CLI output and are
never edited to suit the code.
"""

import json
import os
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.claude_runner import NO_SUBSTITUTION, ClaudeCode, parse_events, refusal_category
from sci_ai_verifier.common import Fault, canonical, digest, validate
from sci_ai_verifier.documentary import (CRITIC_TIMEOUT_SECONDS, REPLY_TOOL, TASK_CRITIQUE_REF, TASK_CRITIQUE_RUBRIC,
                                         critique_tasks, task_critique_schema, validate_assessment,
                                         validate_task_critique)
from sci_ai_verifier.local_candidates import SECRET_BYTES
from sci_ai_verifier.local_config import load_configuration
from test_claude_runner import IMAGE, FakeSandbox

ROOT = Path(__file__).resolve().parents[1]
RECORDED = ROOT / "tests/recorded"
# The verifier's own sessions answering through their reply schemas, captured live through the
# code that reads them. Where the first reply broke the schema and the session corrected it, the
# recording maps to the key its refused reply added. The question critique and the claim-only answer
# were given schemas retired with question tests on 2026-10-05; they stay as more live evidence of
# Claude Code's correction loop, which every structured session relies on.
STRUCTURED_RECORDINGS = {"assessor-structured.jsonl": None, "critic-task-structured.jsonl": "two_inhibitors",
                         "critic-structured.jsonl": "StructuredOutput", "claim-probe-structured.jsonl": "a"}
# Streams that are not the verifier's own replies, exercised by their own tests.
OTHER_RECORDINGS = ["subject-safety-refusal.jsonl", "planner-session-limit.jsonl",
                    "subject-refusal-fallback.jsonl", "subject-refusal-recovered.jsonl"]
TASK = {"task": "Return the supplied text.", "results_file": "/work/results.json"}


def recorded(name):
    return (RECORDED / name).read_bytes()


def packet(name):
    return json.loads(recorded(name))


def probe_stream(command, model="claude-opus-5", text="OK"):
    """A minimal successful stream for the startup probe. Hand-written: no run recorded one."""
    session = command[command.index("--session-id") + 1]
    events = [{"type": "system", "subtype": "init", "session_id": session, "model": model},
              {"type": "assistant", "session_id": session,
               "message": {"model": model, "role": "assistant", "content": [{"type": "text", "text": text}]}},
              {"type": "result", "subtype": "success", "is_error": False, "session_id": session, "result": text}]
    return b"".join(canonical(event) + b"\n" for event in events)


def structured_stream(command, value, model="claude-opus-5"):
    """A minimal accepted structured reply. Hand-written, for a shape the recorded task critique does not
    show: a critique supporting no grade."""
    session = command[command.index("--session-id") + 1]
    events = [{"type": "assistant", "session_id": session, "message": {"model": model, "role": "assistant", "content": [
                  {"type": "tool_use", "id": "reply-1", "name": REPLY_TOOL, "input": value}]}},
              {"type": "user", "session_id": session, "message": {"content": [
                  {"type": "tool_result", "tool_use_id": "reply-1", "content": "Structured output provided successfully"}]}},
              {"type": "result", "subtype": "success", "is_error": False, "session_id": session, "result": "",
               "structured_output": value, "total_cost_usd": 0.0, "usage": {}}]
    return b"".join(canonical(event) + b"\n" for event in events)


def session_of(raw):
    for line in raw.splitlines():
        event = json.loads(line)
        if event.get("type") == "result":
            return event["session_id"]
    raise AssertionError("recording has no result event")


def reply_attempts(raw):
    """Each reply the session offered through the reply tool, with the verdict Claude Code returned."""
    calls, results = [], {}
    for line in raw.splitlines():
        content = (json.loads(line).get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use":
                calls.append(block)
            elif block.get("type") == "tool_result":
                results[block["tool_use_id"]] = block
    return [(call["name"], call["input"], results[call["id"]]) for call in calls]


def subject(process):
    """A subject whose trial container is faked, so a recorded stream replays through `observe`."""
    return ClaudeCode(auth="subscription", process=process, settings={**load_configuration(), "sandbox_image": IMAGE})


class RecordedReplyTests(unittest.TestCase):
    def setUp(self):
        sandbox = patch("sci_ai_verifier.sandbox.DockerSandbox", FakeSandbox)
        sandbox.start()
        self.addCleanup(sandbox.stop)

    def test_recordings_are_present_and_carry_no_credential_bytes(self):
        names = sorted(path.name for path in RECORDED.glob("*.jsonl"))
        self.assertEqual(names, sorted([*STRUCTURED_RECORDINGS, *OTHER_RECORDINGS]))
        for path in RECORDED.iterdir():
            if path.suffix in {".jsonl", ".json"}:
                with self.subTest(recording=path.name):
                    self.assertIsNone(SECRET_BYTES.search(path.read_bytes()))
                    self.assertNotIn(b"\r\n", path.read_bytes())

    def test_each_reply_arrives_through_the_one_reply_tool(self):
        for name in STRUCTURED_RECORDINGS:
            with self.subTest(recording=name):
                raw = recorded(name)
                response = parse_events(raw, expected_session=session_of(raw))
                self.assertTrue(response["tool_calls"])
                self.assertEqual({call["name"] for call in response["tool_calls"]}, {REPLY_TOOL})
                self.assertIsInstance(response["structured_output"], dict)

    def test_a_reply_the_schema_refused_was_corrected_in_the_same_session(self):
        """The slips a free-text reader met one lost claim at a time. Run 0a243b7e lost a claim to an
        empty extra key; here a claim-only answer added a stray `a`, and a critique a stray
        `StructuredOutput`, as earlier ones added `evidence_limits`, `evidence_ceiling` and wrapped
        their reply in `$PARAMETER_NAME`; Git history keeps them. Claude Code refused each and the
        session resent it."""
        for name, stray in STRUCTURED_RECORDINGS.items():
            with self.subTest(recording=name):
                attempts = reply_attempts(recorded(name))
                if stray is None:
                    self.assertEqual(len(attempts), 1)
                    self.assertFalse(attempts[0][2].get("is_error"))
                    continue
                (_, refused, verdict), (_, accepted, final) = attempts
                self.assertIn(stray, refused)
                self.assertTrue(verdict["is_error"])
                self.assertIn("must NOT have additional properties", json.dumps(verdict["content"]))
                self.assertNotIn(stray, accepted)
                self.assertFalse(final.get("is_error"))

    def test_the_recorded_assessment_cites_its_own_real_packet(self):
        raw, sent = recorded("assessor-structured.jsonl"), packet("assessor-packet.json")
        value = validate_assessment(parse_events(raw, expected_session=session_of(raw))["structured_output"], sent)
        self.assertEqual(value["status"], "inconclusive")
        # Every quote really is a substring of the packet it was given, not a paraphrase.
        for citation in value["citations"]:
            self.assertTrue(any(citation["reference_ref"] == item["reference_ref"]
                                and citation["quote"] in item["quote"] for item in sent["evidence"]))

    def test_the_recorded_task_critique_is_a_complete_answer_to_its_real_packet(self):
        """A three-task design that today's code qualified in the operator's image, judged by the pinned model
        under the live rubric: B, every task counted, with five objections it could name. Its first reply put
        the verdicts beside the other fields instead of under case_verdicts, and was refused and resent."""
        raw, sent = recorded("critic-task-structured.jsonl"), packet("critic-task-packet.json")
        self.assertEqual(digest(canonical(sent["rubric"])), TASK_CRITIQUE_REF)
        case_ids = [case["case_id"] for case in sent["evidence"]["tasks"]]
        value = validate_task_critique(parse_events(raw, expected_session=session_of(raw))["structured_output"],
                                       case_ids)
        self.assertEqual(value["supported_grade"], "B")
        self.assertEqual([item["case_id"] for item in value["case_verdicts"]], case_ids)
        self.assertEqual({item["verdict"] for item in value["case_verdicts"]}, {"counts"})
        self.assertEqual(len(value["findings"]), len(TASK_CRITIQUE_RUBRIC["criteria"]))
        self.assertEqual(len(value["objections"]), 5)

    def test_task_critique_end_to_end_over_a_replayed_recording(self):
        """critique_tasks with only the child process replaced: the recorded packet is exactly what it sends,
        under the schema and deadline it sets."""
        raw, sent = recorded("critic-task-structured.jsonl"), packet("critic-task-packet.json")
        seen = {}

        def replay(command, **kwargs):
            seen.update(command=command, prompt=kwargs["prompt"], timeout=kwargs["timeout"])
            return 0, raw.replace(session_of(raw).encode(), command[command.index("--session-id") + 1].encode()), b""

        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            value = critique_tasks(ClaudeCode(auth="subscription", process=replay), sent)
        self.assertEqual((value["supported_grade"], value["rubric_ref"]), ("B", TASK_CRITIQUE_REF))
        self.assertEqual(value["independence"], "fresh host-selected no-tool session; no planner conversation")
        self.assertEqual((json.loads(seen["prompt"]), seen["timeout"]), (sent, CRITIC_TIMEOUT_SECONDS))
        command = seen["command"]
        case_ids = [case["case_id"] for case in sent["evidence"]["tasks"]]
        self.assertEqual(json.loads(command[command.index("--json-schema") + 1]), task_critique_schema(case_ids))

    def test_a_recorded_safety_refusal_is_named_and_not_a_crash(self):
        """A provider refusal is its own operational outcome, never a scientific result."""
        self.assertEqual(refusal_category(recorded("subject-safety-refusal.jsonl")), "bio")
        # The same detector must not see a refusal in an ordinary completed session.
        for name in STRUCTURED_RECORDINGS:
            with self.subTest(recording=name):
                self.assertIsNone(refusal_category(recorded(name)))

    def test_observe_names_a_recorded_refusal_instead_of_calling_it_incomplete(self):
        """The whole subject path over the real refusal stream, exit code and all.

        The provider refused, so the session exits non-zero exactly as a crash would.
        Only the stream distinguishes them, and the report is only honest if it says
        which one happened.
        """
        raw = recorded("subject-safety-refusal.jsonl")
        trial = subject(lambda command, **kwargs: (1, raw, b""))
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            with self.assertRaises(Fault) as caught:
                trial.observe(source=[{"path": "SKILL.md", "content": "Return the supplied text."}],
                              case_input=TASK, config=trial.identity, timeout_seconds=2)
        self.assertEqual(caught.exception.code, "subject_refused")
        self.assertIn("bio", str(caught.exception))
        # It no longer claims the refusal would recur: run 3dc02567's Opus 5 answered a case
        # it had refused moments earlier.
        self.assertIn("safety grounds", str(caught.exception))

    def replay_subject(self, name):
        """The whole subject path over a recorded successful stream; returns it and the env."""
        raw, seen = recorded(name), {}

        def replay(command, **kwargs):
            seen["env"] = kwargs["env"]
            return 0, raw.replace(session_of(raw).encode(), command[command.index("--session-id") + 1].encode()), b""

        trial = subject(replay)
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            observation = trial.observe(source=[{"path": "SKILL.md", "content": "Return the supplied text."}],
                                        case_input=TASK, config=trial.identity, timeout_seconds=2)
        return observation, seen

    def test_an_answer_another_model_wrote_after_a_refusal_is_a_refusal(self):
        """Run 3dc02567: Opus 5 refused, Opus 4.8 answered, and the trial was scored as Opus 5's."""
        with self.assertRaises(Fault) as caught:
            self.replay_subject("subject-refusal-fallback.jsonl")
        self.assertEqual(caught.exception.code, "subject_refused")
        self.assertIn("claude-opus-4-8", str(caught.exception))
        self.assertIn("not used", str(caught.exception))

    def test_a_refusal_the_pinned_model_answered_itself_counts_and_is_noted(self):
        observation, seen = self.replay_subject("subject-refusal-recovered.jsonl")
        self.assertEqual(observation["text"], "R1")
        self.assertEqual(observation["observed_model_ids"], ["<synthetic>", "claude-opus-5"])
        self.assertEqual([(item["subtype"], item["fallback_model"]) for item in observation["refusals"]],
                         [("model_refusal_no_fallback", None)])
        # Substitution is also switched off at the source.
        self.assertEqual({key: seen["env"].get(key) for key in NO_SUBSTITUTION}, NO_SUBSTITUTION)

    def test_the_startup_probe_asks_the_pinned_model_with_substitution_off(self):
        from sci_ai_verifier.local_entry import PROBE_PROMPT, probe_model
        seen = {}

        def process(command, **kwargs):
            seen.update(command=command, env=kwargs["env"], prompt=kwargs["prompt"])
            return 0, probe_stream(command), b""

        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            probe = probe_model(ClaudeCode(auth="subscription", model="claude-opus-5", process=process))
        self.assertEqual(probe, {"model_requested": "claude-opus-5", "observed_model_ids": ["claude-opus-5"]})
        command = seen["command"]
        self.assertEqual((command[command.index("--tools") + 1], command[command.index("--max-turns") + 1]), ("", "1"))
        self.assertEqual(seen["prompt"], PROBE_PROMPT)
        self.assertEqual({key: seen["env"].get(key) for key in NO_SUBSTITUTION}, NO_SUBSTITUTION)

    def test_a_model_the_cli_cannot_serve_stops_before_the_planner(self):
        """Run a8036722's planner died three seconds in; the probe now stops the run first."""
        from sci_ai_verifier.local_entry import probe_model
        # Hand-written in the shape of the CLI's error result; no run recorded one.
        failed = canonical({"type": "result", "subtype": "success", "is_error": True, "api_error_status": 400,
                            "terminal_reason": "api_error",
                            "result": "API Error: 400 [claude-code:unrecognized_model] claude-opus-5-5"}) + b"\n"
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            with self.assertRaises(Fault) as caught:
                probe_model(ClaudeCode(auth="subscription", model="claude-opus-5-5",
                                       process=lambda command, **kwargs: (1, failed, b"")))
        self.assertEqual(caught.exception.code, "model_unavailable")
        self.assertIn("unrecognized_model", str(caught.exception))
        self.assertIn("HTTP 400", str(caught.exception))

    def test_a_non_zero_exit_without_a_refusal_stays_incomplete(self):
        """Only a real refusal gets the refusal name; an ordinary crash must not."""
        trial = subject(lambda command, **kwargs: (1, b"", b""))
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            with self.assertRaises(Fault) as caught:
                trial.observe(source=[{"path": "SKILL.md", "content": "Return the supplied text."}],
                              case_input=TASK, config=trial.identity, timeout_seconds=2)
        self.assertEqual(caught.exception.code, "claude_incomplete")

    def test_a_recording_from_the_wrong_session_is_an_operational_failure(self):
        """The recording proves the happy path; identity checking must still reject a mismatch."""
        raw = recorded("assessor-structured.jsonl")
        with self.assertRaises(Fault) as caught:
            parse_events(raw, expected_session="00000000-0000-0000-0000-000000000000")
        self.assertEqual(caught.exception.code, "claude_identity_error")

    def test_a_planner_stopped_by_the_session_limit_is_not_the_operators_cancellation(self):
        """Run 7f88fbef: its planner hit the subscription limit and was recorded as cancelled."""
        from sci_ai_verifier.local_entry import closing_for, planner_stop
        stop = planner_stop(recorded("planner-session-limit.jsonl"))
        self.assertEqual(stop, "api_error (HTTP 429): You've hit your session limit · resets 11:20am "
                               "(America/Los_Angeles)")
        category, reason = closing_for(Fault("planner_incomplete", "The planner stopped. It reported " + stop))
        self.assertEqual(category, "agent_unavailable")
        self.assertIn("HTTP 429", reason)
        # The operator's own cancellation keeps its wording, and a deadline is a timeout.
        self.assertIsNone(closing_for(Fault("verification_cancelled", "Cancelled.")))
        self.assertIsNone(closing_for(KeyboardInterrupt()))
        self.assertEqual(closing_for(Fault("verification_timeout", "Deadline."))[0], "timeout")
        # A stream with no result event has nothing to report.
        self.assertIsNone(planner_stop(b"not json\n"))

    def test_the_runner_saves_a_session_limited_planner_truthfully(self):
        """The whole recovery path over the real 7f88fbef stream, exit code to saved record."""
        import tempfile
        from sci_ai_verifier import local_entry
        raw = recorded("planner-session-limit.jsonl")

        def process(command, **kwargs):
            # The startup probe is answered; the planner then stops as 7f88fbef's did.
            if kwargs["prompt"] == local_entry.PROBE_PROMPT:
                return 0, probe_stream(command), b""
            return 1, raw, b""

        class Replay(ClaudeCode):
            def __init__(self, **options):
                super().__init__(process=process, **options)

            def preflight(self):
                return {"executable": self.executable, "version": "2.1.268", "auth": self.auth,
                        "model_requested": self.model, "live_execution_tested": False}

        (ROOT / ".verifier/test-work").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="recovery-", dir=ROOT / ".verifier/test-work",
                                         ignore_cleanup_errors=True) as temporary:
            source, workspace = Path(temporary) / "source", Path(temporary) / "workspace"
            source.mkdir()
            workspace.mkdir()
            (source / "SKILL.md").write_text("Return a plain decimal.", encoding="utf-8")
            with patch.object(local_entry, "ClaudeCode", Replay), \
                    patch.object(local_entry, "sweep_stale_directories", lambda log: None), \
                    patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
                result = local_entry.verify(source, workspace=workspace, model="claude-opus-5", timeout=120,
                                            instructions=ROOT / "skills/scientific-verifier")
            self.assertEqual(result["status"], "incomplete", result)
            self.assertEqual(result["error"]["code"], "planner_incomplete")
            self.assertIn("HTTP 429", result["error"]["reason"])
            run_directory = Path(result["error"]["run_directory"])
            outcomes = [json.loads(path.read_bytes()) for path in (run_directory / "operational-outcomes").glob("*.json")]
            self.assertEqual([outcome["category"] for outcome in outcomes], ["agent_unavailable"])
            self.assertIn("You've hit your session limit", outcomes[0]["reason"])
            self.assertNotIn("operator", outcomes[0]["reason"])
            self.assertIn("Reason: ", (run_directory / "partial-report.md").read_text(encoding="utf-8"))


class TaskCritiqueShapeTests(unittest.TestCase):
    """Python checks a task critique against the schema Claude Code enforced, and refuses every
    shape that schema refuses, including each one the free-text reader used to accept."""

    def base(self, **changes):
        return {"supported_grade": "B", "findings": ["f"] * len(TASK_CRITIQUE_RUBRIC["criteria"]),
                "objections": [], "required_revisions": [],
                "case_verdicts": {"t1": self.verdict(), "t2": self.verdict("leaked", "Name the columns plainly.")},
                **changes}

    def verdict(self, verdict="counts", replacement=""):
        return {"verdict": verdict, "reason": "because", "replacement": replacement}

    def refused(self, value, case_ids=("t1", "t2")):
        with self.assertRaises(Fault):
            validate(value, task_critique_schema(list(case_ids)), "critique")

    def test_verdicts_leave_in_packet_order_and_none_is_no_grade(self):
        packet = {"evidence": {"tasks": [{"case_id": "t2"}, {"case_id": "t1"}]}, "rubric": TASK_CRITIQUE_RUBRIC}
        seen = {}

        def process(command, **kwargs):
            seen.update(command=command, timeout=kwargs["timeout"])
            return 0, structured_stream(command, self.base(supported_grade="none")), b""

        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            value = critique_tasks(ClaudeCode(auth="subscription", process=process), packet)
        self.assertIsNone(value["supported_grade"])
        self.assertEqual([(item["case_id"], item["verdict"]) for item in value["case_verdicts"]],
                         [("t2", "leaked"), ("t1", "counts")])
        self.assertEqual((value["rubric_ref"], seen["timeout"]), (TASK_CRITIQUE_REF, CRITIC_TIMEOUT_SECONDS))
        command = seen["command"]
        self.assertEqual(json.loads(command[command.index("--json-schema") + 1]), task_critique_schema(["t2", "t1"]))
        self.assertEqual(command[command.index("--tools") + 1], "")

    def test_the_shapes_a_free_text_reader_once_tolerated_are_refused(self):
        """A lone string for a one-item list, an extra finding, a `null` replacement and an extra key
        in a verdict each cost a live reply before the schema; now the session corrects them."""
        verdicts = self.base()["case_verdicts"]
        for label, broken in (
                ("lone string", self.base(required_revisions="one")),
                ("extra finding", self.base(findings=["f"] * (len(TASK_CRITIQUE_RUBRIC["criteria"]) + 1))),
                ("null replacement", self.base(case_verdicts={**verdicts, "t1": {**self.verdict(), "replacement": None}})),
                ("extra key in a verdict", self.base(case_verdicts={**verdicts, "t1": {**self.verdict(), "verdict_note": ""}}))):
            with self.subTest(label):
                self.refused(broken)

    def test_shapes_that_are_not_a_rubric_answer_are_refused(self):
        for broken in (self.base(supported_grade="A+"), self.base(supported_grade=None),
                       self.base(findings=["only one"]), self.base(findings="not a list"),
                       self.base(findings=["f"] * (len(TASK_CRITIQUE_RUBRIC["criteria"]) - 1)),
                       self.base(objections="not a list"), self.base(objections=[""]), self.base(objections=["  "]),
                       self.base(required_revisions=[""]), self.base(required_revisions=[1]),
                       self.base(required_revisions={"a": "b"}), self.base(required_revisions=["x"] * 9),
                       self.base(objections=["x"] * 9), self.base(extra="field"),
                       {key: value for key, value in self.base().items() if key != "required_revisions"},
                       {key: value for key, value in self.base().items() if key != "case_verdicts"}):
            with self.subTest(broken=canonical(broken)[:90]):
                self.refused(broken)

    def test_case_verdicts_that_do_not_match_the_packet_are_refused(self):
        rejected = self.verdict("beyond_scope", "Ask what the claim states.")
        for label, given in (("missing task", {"t1": self.verdict()}),
                             ("unknown task", {"t1": self.verdict(), "t2": rejected, "t9": self.verdict()}),
                             ("unknown verdict", {"t1": self.verdict(), "t2": self.verdict("fine")}),
                             ("a retired verdict", {"t1": self.verdict(), "t2": self.verdict("naming", "x")}),
                             ("rejected without replacement", {"t1": self.verdict(), "t2": self.verdict("unsound")}),
                             ("counted with replacement", {"t1": self.verdict(replacement="x"), "t2": rejected}),
                             ("blank reason", {"t1": {**self.verdict(), "reason": " "}, "t2": rejected}),
                             ("missing reason", {"t1": {"verdict": "counts", "replacement": ""}, "t2": rejected}),
                             ("a list, as before the schema", [{"case_id": "t1", **self.verdict()},
                                                               {"case_id": "t2", **rejected}]),
                             ("not an object", "all count")):
            with self.subTest(label):
                self.refused(self.base(case_verdicts=given))

    def test_the_task_rubric_mirrors_the_table_that_owns_it(self):
        """"Cases each grade requires" in evidence-rubric.md owns the verdicts and the task counts."""
        from sci_ai_verifier.local_science import TASK_DIRECT, TASK_MINIMUM
        self.assertEqual(TASK_CRITIQUE_RUBRIC["id"], "local-task-critique-v2")
        # A described search is judged by what Python recorded the planner running ("Critique" in local-contract.md).
        self.assertIn("python_checked.search_record", TASK_CRITIQUE_RUBRIC["criteria"][3])
        owner = (ROOT / "skills/scientific-verifier/references/evidence-rubric.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^\| `(\w+)` \|", owner, re.MULTILINE), list(TASK_CRITIQUE_RUBRIC["case_verdicts"]))
        for grade, count in (("A", TASK_DIRECT), ("B", TASK_MINIMUM), ("C", TASK_MINIMUM)):
            self.assertIn("| " + grade + " | at least " + str(count) + " |", owner)


if __name__ == "__main__":
    unittest.main()
