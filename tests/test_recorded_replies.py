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

from sci_ai_verifier.claude_runner import ClaudeCode, parse_events, refusal_category
from sci_ai_verifier.common import Fault, canonical, digest
from sci_ai_verifier.documentary import (CRITIQUE_RUBRIC, RUBRIC, critique, parse_reply,
    validate_assessment, validate_critique)
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
# Streams that are not critic replies, exercised by their own tests.
OTHER_RECORDINGS = ["assessor-bare.jsonl", "subject-safety-refusal.jsonl"]
# Every critic recording answered rubric v2, which had five criteria; v3 appended a sixth,
# and v4 added the per-case verdict keys. A reply is judged against the rubric it was
# answering -- judging it against a later one would fail real replies for a question nobody
# had asked them. Criteria are append-only and v4 only added keys, so each earlier rubric is
# reconstructed from the live one, and the digests below were taken before the later
# versions existed: they prove each reconstruction is the exact rubric those sessions saw.
V4_KEYS = ("case_verdicts", "case_requirements", "case_replacement")
BEFORE_V4 = {key: value for key, value in CRITIQUE_RUBRIC.items() if key not in V4_KEYS}
ANSWERED = {**BEFORE_V4, "id": "local-evidence-critique-v2", "criteria": CRITIQUE_RUBRIC["criteria"][:5]}
ANSWERED_REF = "91f33b72c208817675e458838093f10c73d156067e64d10e299509fe8feacd36"
# v3 as run d87a6d5c recorded it on all five of its critiques.
V3 = {**BEFORE_V4, "id": "local-evidence-critique-v3"}
V3_REF = "07140328e5a3cbdd4eec803717fa0c71e0b05c0c5394d4f73b72b1f581c8663e"
# v4 as run 28d19f8a recorded it on all five of its critiques. v5 changed only the wording
# of the `duplicate` verdict, so restoring that one definition must give v4's exact digest.
V4 = {**CRITIQUE_RUBRIC, "id": "local-evidence-critique-v4",
      "case_verdicts": {**CRITIQUE_RUBRIC["case_verdicts"],
                        "duplicate": "Tests the same fact as an earlier case in this design, so it adds no "
                                     "independent evidence; the reason names that earlier case, which keeps its own verdict"}}
V4_REF = "be80e6974bde1cb6c02de6145b1cffe87ef0505a16b45a4f0fb736eee8956a14"


def recorded(name):
    return (RECORDED / name).read_bytes()


def session_of(raw):
    for line in raw.splitlines():
        event = json.loads(line)
        if event.get("type") == "result":
            return event["session_id"]
    raise AssertionError("recording has no result event")


class RecordedReplyTests(unittest.TestCase):
    def test_recordings_are_present_and_carry_no_credential_bytes(self):
        names = sorted(path.name for path in RECORDED.glob("*.jsonl"))
        self.assertEqual(names, sorted([*CRITIC_RECORDINGS, *OTHER_RECORDINGS]))
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
        self.assertIn("not retried", str(caught.exception))

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
                             ("extra key", [{**self.verdict("c1"), "grade": "A"}, rejected]),
                             ("not a list", "all count")):
            with self.subTest(label), self.assertRaises(Fault) as caught:
                validate_critique(self.base(case_verdicts=given), case_ids=["c1", "c2"])
            self.assertEqual(caught.exception.code, "critic_response_invalid")
        with self.assertRaises(Fault):
            validate_critique({key: value for key, value in self.base().items() if key != "case_verdicts"})


if __name__ == "__main__":
    unittest.main()
