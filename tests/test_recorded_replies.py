"""The independent-session boundary, driven by replies a real session actually sent.

Every other test in this suite hands `validate_critique` and `validate_assessment` a
dict written by the test author, so those tests cannot observe a disagreement between
what the code demands and what a fresh Claude session emits. That disagreement is
exactly what discarded three completed critiques in local run a392ea65. The recordings
under `tests/recorded/` are real CLI output and are never edited to suit the code.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.claude_runner import NO_SUBSTITUTION, ClaudeCode, parse_events, refusal_category
from sci_ai_verifier.common import Fault, canonical, digest
from sci_ai_verifier.documentary import (CRITIC_TIMEOUT_SECONDS, CRITIQUE_RUBRIC, RUBRIC, critique,
    parse_reply, validate_assessment, validate_critique)
from sci_ai_verifier.local_candidates import SECRET_BYTES
from sci_ai_verifier.local_config import load_configuration

RECORDED = Path(__file__).resolve().parent / "recorded"
# Grade and revision count are properties of the recording, not of the parser. They are
# asserted so an edited recording fails loudly instead of quietly weakening the test.
CRITIC_RECORDINGS = {"critic-fenced-revision-list.jsonl": ("B", 5, True),
                     "critic-fenced-revision-list-2.jsonl": ("B", 4, True),
                     "critic-bare-empty-revisions.jsonl": ("A", 0, False),
                     # Answered all five criteria, then added a sixth observation that fitted
                     # none of them. Refusing this cost run e035eef6 a grade A and 27 trials.
                     "critic-extra-finding.jsonl": ("A", 0, False)}
# Run 0a243b7e: two complete v5 replies, both supporting B, each with one extra empty key
# inside a case verdict. Refusing both lost claim 1. Mapped to the key each one added.
CASE_VERDICT_RECORDINGS = {"critic-case-verdict-extra-key.jsonl": "verdict_note",
                           "critic-case-verdict-extra-key-2.jsonl": "case_id_note"}
# Streams that are not critic replies, exercised by their own tests.
OTHER_RECORDINGS = ["assessor-bare.jsonl", "subject-safety-refusal.jsonl", "planner-session-limit.jsonl",
                    "subject-refusal-fallback.jsonl", "subject-refusal-recovered.jsonl"]
# Every critic recording answered rubric v2, which had five criteria; v3 appended a sixth,
# and v4 added the per-case verdict keys. A reply is judged against the rubric it was
# answering -- judging it against a later one would fail real replies for a question nobody
# had asked them. Criteria are append-only and v4 only added keys, so each earlier rubric is
# reconstructed from the live one, and the digests below were taken before the later
# versions existed: they prove each reconstruction is the exact rubric those sessions saw.
# v5 as runs b0955d2f, 3dc02567 and 84e90683 recorded it. v6 added one key and widened the
# `beyond_scope` definition, so removing the key and restoring that definition gives v5,
# and every earlier rubric is rebuilt from v5 rather than from the live one.
V6_KEYS = ("verdict_consistency",)
V5 = {**{key: value for key, value in CRITIQUE_RUBRIC.items() if key not in V6_KEYS},
      "id": "local-evidence-critique-v5",
      "case_verdicts": {**CRITIQUE_RUBRIC["case_verdicts"],
                        "beyond_scope": "Asks a consequence or fact the claim never states"}}
V5_REF = "bf9442695413d32d8e95cb7f9786f638071f9d037eeff9db4a3a682fe718ef56"
V4_KEYS = ("case_verdicts", "case_requirements", "case_replacement")
BEFORE_V4 = {key: value for key, value in V5.items() if key not in V4_KEYS}
ANSWERED = {**BEFORE_V4, "id": "local-evidence-critique-v2", "criteria": CRITIQUE_RUBRIC["criteria"][:5]}
ANSWERED_REF = "91f33b72c208817675e458838093f10c73d156067e64d10e299509fe8feacd36"
# v3 as run d87a6d5c recorded it on all five of its critiques.
V3 = {**BEFORE_V4, "id": "local-evidence-critique-v3"}
V3_REF = "07140328e5a3cbdd4eec803717fa0c71e0b05c0c5394d4f73b72b1f581c8663e"
# v4 as run 28d19f8a recorded it on all five of its critiques. v5 changed only the wording
# of the `duplicate` verdict, so restoring that one definition must give v4's exact digest.
V4 = {**V5, "id": "local-evidence-critique-v4",
      "case_verdicts": {**V5["case_verdicts"],
                        "duplicate": "Tests the same fact as an earlier case in this design, so it adds no "
                                     "independent evidence; the reason names that earlier case, which keeps its own verdict"}}
V4_REF = "be80e6974bde1cb6c02de6145b1cffe87ef0505a16b45a4f0fb736eee8956a14"


def recorded(name):
    return (RECORDED / name).read_bytes()


def probe_stream(command, model="claude-opus-5", text="OK"):
    """A minimal successful stream for the startup probe. Hand-written: no run recorded one."""
    session = command[command.index("--session-id") + 1]
    events = [{"type": "system", "subtype": "init", "session_id": session, "model": model},
              {"type": "assistant", "session_id": session,
               "message": {"model": model, "role": "assistant", "content": [{"type": "text", "text": text}]}},
              {"type": "result", "subtype": "success", "is_error": False, "session_id": session, "result": text}]
    return b"".join(canonical(event) + b"\n" for event in events)


def session_of(raw):
    for line in raw.splitlines():
        event = json.loads(line)
        if event.get("type") == "result":
            return event["session_id"]
    raise AssertionError("recording has no result event")


class RecordedReplyTests(unittest.TestCase):
    def test_recordings_are_present_and_carry_no_credential_bytes(self):
        names = sorted(path.name for path in RECORDED.glob("*.jsonl"))
        self.assertEqual(names, sorted([*CRITIC_RECORDINGS, *CASE_VERDICT_RECORDINGS, *OTHER_RECORDINGS]))
        for path in RECORDED.iterdir():
            if path.suffix in {".jsonl", ".json"}:
                with self.subTest(recording=path.name):
                    self.assertIsNone(SECRET_BYTES.search(path.read_bytes()))
                    self.assertNotIn(b"\r\n", path.read_bytes())

    def test_recorded_critiques_survive_the_whole_parse_and_validate_path(self):
        """parse_events -> parse_reply -> validate_critique, on bytes a real session sent."""
        for name, (grade, revisions, fenced) in CRITIC_RECORDINGS.items():
            with self.subTest(recording=name):
                raw = recorded(name)
                response = parse_events(raw, expected_session=session_of(raw))
                self.assertFalse(response["tool_calls"], "a no-tool session must call no tools")
                self.assertEqual(response["text"].strip().startswith("```"), fenced)
                value = validate_critique(parse_reply(response["text"]), ANSWERED)
                self.assertEqual(value["supported_grade"], grade)
                self.assertGreaterEqual(len(value["findings"]), len(ANSWERED["criteria"]))
                self.assertEqual(len(value["required_revisions"]), revisions)
                self.assertIsInstance(value["required_revisions"], list)

    def test_recorded_case_verdicts_with_an_extra_key_are_complete_answers(self):
        """Both replies answered every question rubric v5 asks and added one empty key
        inside a verdict. They are judged against the packet they were given, whose rubric
        was v5, and the extra key is kept, not read."""
        packet = json.loads((RECORDED / "critic-case-verdict-packet.json").read_bytes())
        self.assertEqual(digest(canonical(packet["rubric"])), V5_REF)
        case_ids = [case["case_id"] for case in packet["evidence"]["cases"]]
        for name, extra in CASE_VERDICT_RECORDINGS.items():
            with self.subTest(recording=name):
                raw = recorded(name)
                response = parse_events(raw, expected_session=session_of(raw))
                self.assertFalse(response["tool_calls"])
                value = validate_critique(parse_reply(response["text"]), V5, case_ids)
                self.assertEqual(value["supported_grade"], "B")
                self.assertEqual([item["case_id"] for item in value["case_verdicts"]], case_ids)
                carrying = [item for item in value["case_verdicts"] if extra in item]
                self.assertTrue(carrying)
                self.assertTrue(all(item[extra] == "" for item in carrying))

    def test_recorded_assessment_cites_its_own_real_packet(self):
        raw = recorded("assessor-bare.jsonl")
        packet = json.loads((RECORDED / "assessor-packet.json").read_bytes())
        response = parse_events(raw, expected_session=session_of(raw))
        self.assertFalse(response["tool_calls"])
        value = validate_assessment(parse_reply(response["text"]), packet)
        self.assertEqual(value["status"], "inconclusive")
        self.assertEqual(len(value["findings"]), len(RUBRIC["criteria"]))
        # Every quote really is a substring of the packet it was given, not a paraphrase.
        for citation in value["citations"]:
            self.assertTrue(any(citation["reference_ref"] == item["reference_ref"]
                                and citation["quote"] in item["quote"] for item in packet["evidence"]))

    def test_critique_end_to_end_over_a_replayed_recording(self):
        """The whole public entry point, with only the child process replaced by a recording."""
        raw = recorded("critic-fenced-revision-list.jsonl")

        def replay(command, **kwargs):
            # The critique's own deadline reaches the process, not the assessor's two minutes.
            self.assertEqual(kwargs["timeout"], CRITIC_TIMEOUT_SECONDS)
            # Rewrite the recorded session id to the one this call generated, so the
            # identity check in parse_events is exercised rather than bypassed.
            recorded_session = session_of(raw)
            return 0, raw.replace(recorded_session.encode(), command[command.index("--session-id") + 1].encode()), b""

        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            value = critique(ClaudeCode(auth="subscription", process=replay), {"claim": "fixture packet"},
                             rubric=ANSWERED)
        self.assertEqual(value["supported_grade"], "B")
        # Recorded under the rubric it answered, so the audit trail names the right one.
        self.assertEqual(value["rubric_ref"], ANSWERED_REF)
        self.assertEqual(value["independence"], "fresh host-selected no-tool session; no planner conversation")
        self.assertTrue(value["ai_judgment"])

    def test_every_rubric_criterion_is_answered_and_an_extra_note_is_kept(self):
        """The criteria are a floor. A sixth finding is one more answer, not a broken reply."""
        raw = recorded("critic-extra-finding.jsonl")
        value = validate_critique(parse_reply(parse_events(raw, expected_session=session_of(raw))["text"]),
                                  ANSWERED)
        self.assertEqual(len(value["findings"]), len(ANSWERED["criteria"]) + 1)
        self.assertEqual(value["supported_grade"], "A")
        # The extra is retained verbatim, not folded into objections or dropped.
        self.assertIn("test facts the claim does not print", value["findings"][-1])

    def test_the_rubric_the_recordings_answered_is_reconstructed_exactly(self):
        """If this fails, a criterion was inserted or reordered rather than appended."""
        self.assertEqual(digest(canonical(ANSWERED)), ANSWERED_REF)
        self.assertEqual(digest(canonical(V3)), V3_REF)
        self.assertEqual(digest(canonical(V4)), V4_REF)
        self.assertEqual(digest(canonical(V5)), V5_REF)

    def test_the_live_rubric_refuses_real_replies_that_never_judged_case_scope(self):
        """The scope criterion is enforced, not advisory. These three real critiques answered
        every question v2 asked and nothing about whether their cases stayed inside the claim;
        under v3 that is an unanswered criterion, so each is an operational failure, not a
        grade. Their rejection is the point of this test, not a regression."""
        for name in ("critic-fenced-revision-list.jsonl", "critic-fenced-revision-list-2.jsonl",
                     "critic-bare-empty-revisions.jsonl"):
            with self.subTest(recording=name, rubric="v3"):
                raw = recorded(name)
                text = parse_events(raw, expected_session=session_of(raw))["text"]
                with self.assertRaises(Fault) as caught:
                    validate_critique(parse_reply(text), V3)
                self.assertEqual(caught.exception.code, "critic_response_invalid")
        for name in ("critic-fenced-revision-list.jsonl", "critic-fenced-revision-list-2.jsonl",
                     "critic-bare-empty-revisions.jsonl"):
            with self.subTest(recording=name):
                raw = recorded(name)
                text = parse_events(raw, expected_session=session_of(raw))["text"]
                with self.assertRaises(Fault) as caught:
                    validate_critique(parse_reply(text))
                self.assertEqual(caught.exception.code, "critic_response_invalid")

    def test_the_one_critique_that_raised_scope_unprompted_answers_the_new_criterion(self):
        """Run e035eef6's reviewer answered v2's five criteria, then added an observation no
        criterion covered: that the cases "test facts the claim does not print". That is the
        v3 scope criterion, found by a real reviewer before it existed. Findings map by
        position, so under v3 its sixth finding is the answer to the sixth criterion."""
        raw = recorded("critic-extra-finding.jsonl")
        value = validate_critique(parse_reply(parse_events(raw, expected_session=session_of(raw))["text"]), V3)
        self.assertEqual(len(value["findings"]), len(CRITIQUE_RUBRIC["criteria"]))
        self.assertIn("test facts the claim does not print", value["findings"][len(CRITIQUE_RUBRIC["criteria"]) - 1])

    def test_fewer_findings_than_criteria_is_still_refused(self):
        """Tolerating an extra answer must not tolerate an unanswered criterion."""
        short = {"supported_grade": "A", "objections": [], "required_revisions": [], "case_verdicts": [],
                 "findings": ["f"] * (len(CRITIQUE_RUBRIC["criteria"]) - 1)}
        with self.assertRaises(Fault) as caught:
            validate_critique(short)
        self.assertEqual(caught.exception.code, "critic_response_invalid")

    def test_a_recorded_safety_refusal_is_named_and_not_a_crash(self):
        """A provider refusal is its own operational outcome, never a scientific result."""
        self.assertEqual(refusal_category(recorded("subject-safety-refusal.jsonl")), "bio")
        # The same detector must not see a refusal in an ordinary completed session.
        for name in ("critic-bare-empty-revisions.jsonl", "assessor-bare.jsonl"):
            with self.subTest(recording=name):
                self.assertIsNone(refusal_category(recorded(name)))

    def test_observe_names_a_recorded_refusal_instead_of_calling_it_incomplete(self):
        """The whole subject path over the real refusal stream, exit code and all.

        The provider refused, so the session exits non-zero exactly as a crash would.
        Only the stream distinguishes them, and the report is only honest if it says
        which one happened.
        """
        raw = recorded("subject-safety-refusal.jsonl")
        settings = {**load_configuration(), "sandbox_image": None}

        def replay(command, **kwargs):
            return 1, raw, b""

        subject = ClaudeCode(auth="subscription", process=replay, settings=settings)
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            with self.assertRaises(Fault) as caught:
                subject.observe(source=[{"path": "SKILL.md", "content": "Return the supplied text."}],
                                case_input={"input": "case"}, config=subject.identity, timeout_seconds=2)
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

        subject = ClaudeCode(auth="subscription", process=replay, settings={**load_configuration(), "sandbox_image": None})
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            observation = subject.observe(source=[{"path": "SKILL.md", "content": "Return the supplied text."}],
                                          case_input={"input": "case"}, config=subject.identity, timeout_seconds=2)
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
        settings = {**load_configuration(), "sandbox_image": None}

        def replay(command, **kwargs):
            return 1, b"", b""

        subject = ClaudeCode(auth="subscription", process=replay, settings=settings)
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
            with self.assertRaises(Fault) as caught:
                subject.observe(source=[{"path": "SKILL.md", "content": "Return the supplied text."}],
                                case_input={"input": "case"}, config=subject.identity, timeout_seconds=2)
        self.assertEqual(caught.exception.code, "claude_incomplete")

    def test_a_recording_from_the_wrong_session_is_an_operational_failure(self):
        """The recording proves the happy path; identity checking must still reject a mismatch."""
        raw = recorded("critic-bare-empty-revisions.jsonl")
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

        root = Path(__file__).resolve().parents[1]
        (root / ".verifier/test-work").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="recovery-", dir=root / ".verifier/test-work",
                                         ignore_cleanup_errors=True) as temporary:
            source, workspace = Path(temporary) / "source", Path(temporary) / "workspace"
            source.mkdir()
            workspace.mkdir()
            (source / "SKILL.md").write_text("Return a plain decimal.", encoding="utf-8")
            with patch.object(local_entry, "ClaudeCode", Replay), \
                    patch.object(local_entry, "sweep_stale_directories", lambda log: None), \
                    patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-for-boundary-test"}):
                result = local_entry.verify(source, workspace=workspace, model="claude-opus-5", timeout=120,
                                            instructions=root / "skills/scientific-verifier")
            self.assertEqual(result["status"], "incomplete", result)
            self.assertEqual(result["error"]["code"], "planner_incomplete")
            self.assertIn("HTTP 429", result["error"]["reason"])
            run_directory = Path(result["error"]["run_directory"])
            outcomes = [json.loads(path.read_bytes()) for path in (run_directory / "operational-outcomes").glob("*.json")]
            self.assertEqual([outcome["category"] for outcome in outcomes], ["agent_unavailable"])
            self.assertIn("You've hit your session limit", outcomes[0]["reason"])
            self.assertNotIn("operator", outcomes[0]["reason"])
            self.assertIn("Reason: ", (run_directory / "partial-report.md").read_text(encoding="utf-8"))


class ReplyShapeTests(unittest.TestCase):
    """The two shapes the recordings proved real, plus what must still be refused."""

    def base(self, **changes):
        return {"supported_grade": "B", "findings": ["f"] * len(CRITIQUE_RUBRIC["criteria"]),
                "objections": [], "required_revisions": [],
                "case_verdicts": [{"case_id": "c1", "verdict": "counts", "reason": "in scope", "replacement": ""}],
                **changes}

    def test_fence_around_a_whole_reply_is_the_same_answer(self):
        for text in ('{"a": 1}', '```json\n{"a": 1}\n```', '```\n{"a": 1}\n```',
                     '  ```json\n{"a": 1}\n```  '):
            with self.subTest(text=text):
                self.assertEqual(parse_reply(text), {"a": 1})

    def test_prose_outside_the_json_is_still_refused(self):
        for text in ("Here is my verdict: {\"a\": 1}", '```json\n{"a": 1}\n``` and my note',
                     "```json\n{\"a\": 1}", "not json at all", ""):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_reply(text)

    def test_required_revisions_accepts_a_list_and_normalises_a_lone_string(self):
        self.assertEqual(validate_critique(self.base(required_revisions=["one", "two"]))["required_revisions"],
                         ["one", "two"])
        # A critique that wrote one revision as a bare string said the same thing.
        self.assertEqual(validate_critique(self.base(required_revisions="one"))["required_revisions"], ["one"])
        self.assertEqual(validate_critique(self.base(required_revisions=""))["required_revisions"], [])
        self.assertEqual(validate_critique(self.base(required_revisions="   "))["required_revisions"], [])

    def test_shapes_that_are_not_a_rubric_answer_are_refused(self):
        for broken in (self.base(supported_grade="A+"), self.base(supported_grade=None),
                       self.base(findings=["only one"]), self.base(findings="not a list"),
                       self.base(objections="not a list"), self.base(objections=[""]),
                       self.base(required_revisions=[""]), self.base(required_revisions=[1]),
                       self.base(required_revisions={"a": "b"}), self.base(required_revisions=["x"] * 9),
                       self.base(objections=["x"] * 9), self.base(extra="field"),
                       {k: v for k, v in self.base().items() if k != "required_revisions"}):
            with self.subTest(broken=canonical(broken)[:90]), self.assertRaises(Fault) as caught:
                validate_critique(broken)
            self.assertEqual(caught.exception.code, "critic_response_invalid")

    def test_none_becomes_an_absent_grade_not_the_string_none(self):
        self.assertIsNone(validate_critique(self.base(supported_grade="none"))["supported_grade"])

    def verdict(self, case_id, verdict="counts", replacement=""):
        return {"case_id": case_id, "verdict": verdict, "reason": "because", "replacement": replacement}

    def test_every_packet_case_gets_one_verdict_returned_in_packet_order(self):
        given = [self.verdict("c2", "leaked", "Ask it without naming the function."), self.verdict("c1")]
        value = validate_critique(self.base(case_verdicts=given), case_ids=["c1", "c2"])
        self.assertEqual([item["case_id"] for item in value["case_verdicts"]], ["c1", "c2"])
        # `null` for a counting case's replacement is the empty description it meant.
        value = validate_critique(self.base(case_verdicts=[{**self.verdict("c1"), "replacement": None}]),
                                  case_ids=["c1"])
        self.assertEqual(value["case_verdicts"][0]["replacement"], "")

    def test_case_verdicts_that_do_not_match_the_packet_are_refused(self):
        rejected = self.verdict("c2", "beyond_scope", "Ask what the claim states.")
        for label, given in (("missing case", [self.verdict("c1")]),
                             ("unknown case", [self.verdict("c1"), self.verdict("c9")]),
                             ("duplicate", [self.verdict("c1"), self.verdict("c1"), rejected]),
                             ("unknown verdict", [self.verdict("c1"), self.verdict("c2", "fine")]),
                             ("rejected without replacement", [self.verdict("c1"), self.verdict("c2", "naming")]),
                             ("counted with replacement", [self.verdict("c1", replacement="x"), rejected]),
                             ("empty reason", [{**self.verdict("c1"), "reason": " "}, rejected]),
                             ("extra key that is not a string", [{**self.verdict("c1"), "note": {"a": 1}}, rejected]),
                             ("too many extra keys", [{**self.verdict("c1"), **{"n%d" % i: "" for i in range(5)}},
                                                      rejected]),
                             ("missing required key", [{k: v for k, v in self.verdict("c1").items() if k != "reason"},
                                                       rejected]),
                             ("not a list", "all count")):
            with self.subTest(label), self.assertRaises(Fault) as caught:
                validate_critique(self.base(case_verdicts=given), case_ids=["c1", "c2"])
            self.assertEqual(caught.exception.code, "critic_response_invalid")
        with self.assertRaises(Fault):
            validate_critique({key: value for key, value in self.base().items() if key != "case_verdicts"})

    def test_a_few_extra_string_or_null_keys_in_a_verdict_are_kept_and_never_read(self):
        given = [{**self.verdict("c1"), "verdict_note": "", "note": None, "grade": "A"},
                 self.verdict("c2", "leaked", "Ask it without naming the key.")]
        value = validate_critique(self.base(case_verdicts=given), case_ids=["c1", "c2"])
        self.assertEqual(value["case_verdicts"][0]["verdict_note"], "")
        self.assertIsNone(value["case_verdicts"][0]["note"])
        # Only `verdict` decides whether a case counts; an extra "grade" changes nothing.
        self.assertEqual([item["verdict"] for item in value["case_verdicts"]], ["counts", "leaked"])


if __name__ == "__main__":
    unittest.main()
