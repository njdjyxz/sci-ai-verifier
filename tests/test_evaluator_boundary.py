"""What an evaluator program prints is untrusted output, so parse it like untrusted output.

Every other test patches `local_evaluators.score` out, because the real one needs a
container, so the rule that turns an evaluator's stdout into a scientific status has
never been exercised against bytes a program would actually print. That is the same
blind spot that let `critic_response_invalid` through: a strict shape rule on one side
of a boundary, and no test on the other side of it.

The container is injectable, so the rule can be tested without Docker.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.common import Fault
from sci_ai_verifier.local_evaluators import score

SPEC = {"code": "print('unused in these tests')", "absolute_tolerance": "0", "relative_tolerance": "0"}
CASE = {"input": "alpha", "expected": "1.0"}
SETTINGS = {"sandbox_image": "sha256:" + "a" * 64, "max_artifact_bytes": 1024,
            "max_file_bytes": 1024, "max_artifacts": 4}
PACKET_KEYS = ["absolute_tolerance", "actual", "artifact_root", "artifacts",
               "expected", "input", "relative_tolerance"]


class ScoringBoundaryTests(unittest.TestCase):
    def sandbox(self, stdout, exit_code=0):
        outer = self

        class FakeSandbox:
            image = SETTINGS["sandbox_image"]

            def __init__(self, source, settings, *, timeout=None, log=None):
                self.source = source

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def command(self, command, *, timeout=None, stdin=""):
                # The scoring program really is handed the case, the observation and the oracle.
                outer.assertEqual(sorted(json.loads(stdin)), PACKET_KEYS)
                return {"exit_code": exit_code, "stdout": stdout, "stderr": ""}

        return FakeSandbox

    def run_score(self, stdout, exit_code=0):
        return score(SPEC, CASE, "1.0", SETTINGS, sandbox_factory=self.sandbox(stdout, exit_code))

    def test_a_bare_status_object_is_the_evaluator_result(self):
        for status in ("pass", "fail", "invalid"):
            with self.subTest(status=status):
                result = self.run_score(json.dumps({"status": status}))
                self.assertEqual(result["status"], status)
                self.assertEqual(result["image_id"], SETTINGS["sandbox_image"])
                self.assertEqual(len(result["packet_sha256"]), 64)
                self.assertEqual(len(result["code_sha256"]), 64)

    def test_the_newline_print_adds_is_tolerated(self):
        """An evaluator that uses print() must not fail for the newline print appends."""
        self.assertEqual(self.run_score('{"status": "pass"}' + chr(10))["status"], "pass")
        self.assertEqual(self.run_score("  " + '{"status": "pass"}' + "  " + chr(10) * 2)["status"], "pass")

    def test_output_that_is_not_exactly_one_status_object_is_operational(self):
        two_objects = '{"status": "pass"}' + chr(10) + '{"status": "fail"}'
        fenced = "```json" + chr(10) + '{"status": "pass"}' + chr(10) + "```"
        for stdout, note in (("", "no output at all"),
                             ("pass", "a bare word"),
                             ('{"status": "ok"}', "a status outside the allowed set"),
                             ('{"status": "pass", "detail": "why"}', "an extra key"),
                             ('{"status": ["pass"]}', "status is not a string"),
                             ("{}", "no status at all"),
                             (two_objects, "two objects"),
                             (fenced, "a code fence is not a program's output")):
            with self.subTest(note=note), self.assertRaises(Fault) as caught:
                self.run_score(stdout)
            self.assertEqual(caught.exception.code, "evaluator_failed")

    def test_a_failing_program_is_operational_even_when_it_prints_a_status(self):
        """A non-zero exit means the scoring never completed, whatever landed on stdout."""
        with self.assertRaises(Fault) as caught:
            self.run_score('{"status": "pass"}', exit_code=1)
        self.assertEqual(caught.exception.code, "evaluator_failed")

    def test_python_scoring_refuses_to_run_without_a_pinned_image(self):
        for image in (None, ""):
            with self.subTest(image=image), self.assertRaises(Fault) as caught:
                score(SPEC, CASE, "1.0", {**SETTINGS, "sandbox_image": image},
                      sandbox_factory=self.sandbox('{"status": "pass"}'))
            self.assertEqual(caught.exception.code, "sandbox_configuration_required")

    def test_the_oracle_reaches_the_evaluator_and_not_the_observation_field(self):
        """Scoring is the only stage that may see the expected answer; it must see the real one."""
        seen = {}

        def capture(source, settings, *, timeout=None, log=None):
            sandbox = self.sandbox('{"status": "pass"}')(source, settings, timeout=timeout, log=log)
            original = sandbox.command

            def command(cmd, *, timeout=None, stdin=""):
                seen.update(json.loads(stdin))
                return original(cmd, timeout=timeout, stdin=stdin)

            sandbox.command = command
            return sandbox

        score(SPEC, CASE, "observed-text", SETTINGS, sandbox_factory=capture)
        self.assertEqual(seen["expected"], CASE["expected"])
        self.assertEqual(seen["actual"], "observed-text")
        self.assertEqual(seen["input"], CASE["input"])


if __name__ == "__main__":
    unittest.main()
