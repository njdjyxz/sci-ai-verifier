"""Task tests ("local-tasks.md"): designs that run the skill on input Python built.

Docker and every Claude session are faked: the runner, the subject and the critique below stand in
for them, so these tests check Python's own rules. A live check needs the operator's image.
"""

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import test_local as fixture
from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.common import Fault, canonical, digest
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier import local_tasks
from sci_ai_verifier.local_tasks import (RESULTS_FILE, RecordedRunner, check, qualify, recheck, score, task_input,
                                         traceable)

IMAGE = "sha256:" + "a" * 64
MODEL = "Fixture model: the response is the dose times the slope."
RULE = "A compound that needs a lower dose for the same response is the more potent one."
PAGE = "Independent fixture page. " + MODEL + " " + RULE + " Published value: the slope of compound Z is 2.5."


class FakeRunner:
    """Stands in for the operator's container: the generator writes a dose table from its arguments, and
    the solver fits the slope from the table. Neither program's code is run; `faults` injects failures."""

    def __init__(self, settings=None, *, log=None, sandbox_factory=None):
        self.generated, self.solved, self.faults = [], [], {}

    def generate(self, code, arguments):
        self.generated.append(arguments)
        if "generator" in self.faults:
            raise self.faults["generator"]
        given = json.loads(arguments)
        rows = "".join(f"{dose},{dose * given['slope']}\n" for dose in given["doses"])
        files = {"doses.csv": ("dose,response\n" + rows).encode()}
        if given.get("nested"):
            files["sub/extra.csv"] = b"x"
        planted = {"slope": given["slope"], "more_potent": given.get("potent", "A"), "flagged": given.get("flag", False)}
        return {"exit_code": given.get("exit", 0), "stdout": "debug line\n" + json.dumps(planted), "stderr": "",
                "files": files, "image_id": IMAGE}

    def solve(self, code, given, files):
        self.solved.append(given)
        if "solver" in self.faults:
            raise self.faults["solver"]
        results = fit(files, given)
        if "solver_wrong" in self.faults:
            results["slope"] = results["slope"] * 1000
        return {"exit_code": 0, "stderr": "", "results": json.dumps(results).encode(), "image_id": IMAGE}


def fit(files, given):
    """A correct analysis of the fixture table, answering every field the task asks for."""
    rows = [line.split(",") for line in files["doses.csv"].decode().splitlines()[1:]]
    slope = sum(float(response) / float(dose) for dose, response in rows) / len(rows)
    found = {"slope": slope, "more_potent": "A", "flagged": False}
    return {field: found[field] for field in given["results_format"]}


def task(case_id, sections, slope=2, **extra):
    return {"case_id": case_id, "job": "Find the slope of the dose table in " + case_id + ".", "sections": sections,
            "arguments": json.dumps({"slope": slope, "doses": [1, 2, 3], **extra}),
            "outputs": [{"field": "slope", "type": "number", "planted": "slope", "relative_tolerance": "0.1"},
                        {"field": "more_potent", "type": "text", "planted": "more_potent",
                         "reference_ref": "REF", "source_quote": RULE}],
            "applicability": "A dose table like the skill's own input."}


def design(cases, ref="REF"):
    text = json.dumps(cases).replace('"REF"', json.dumps(ref))
    return {"name": "Slope tasks", "scope": "Linear dose tables", "limitations": "Synthetic tables only.",
            "generator": {"code": "print('generator')", "reference_ref": ref, "model_quote": MODEL},
            "solver": {"code": "print('solver')"}, "cases": json.loads(text)}


REFERENCES = {"REF": {"url": "https://example.org/model", "version": "v1", "license": "Unknown", "text": PAGE,
                      "raw_ref": "raw", "origin": "retrieved_public_https"}}


class RulesTests(unittest.TestCase):
    """Reading a trial's results and checking a design, without any program run."""

    def test_each_output_type_reads_as_local_tasks_md_says(self):
        number = {"field": "slope", "type": "number", "expected": "2", "relative_tolerance": "0.1"}
        self.assertEqual(check(number, True, 2.19), "pass")
        self.assertEqual(check(number, True, 2.21), "fail")
        self.assertEqual(check({**number, "absolute_tolerance": "0.5"}, True, 2.4), "pass")  # The wider passes.
        self.assertEqual(check({"field": "n", "type": "number", "expected": "2"}, True, 2.0000005), "pass")
        self.assertEqual(check({"field": "n", "type": "number", "expected": "2"}, True, 2.001), "fail")
        for misshapen in ("2", True, None, [2]):
            self.assertEqual(check(number, True, misshapen), "invalid")
        self.assertEqual(check(number, False, None), "invalid")
        text = {"field": "pick", "type": "text", "expected": "Compound A"}
        self.assertEqual(check(text, True, "  compound   a "), "pass")
        self.assertEqual(check(text, True, "B"), "fail")
        self.assertEqual(check(text, True, ""), "invalid")
        flag = {"field": "flag", "type": "boolean", "expected": True}
        self.assertEqual(check(flag, True, True), "pass")
        self.assertEqual(check(flag, True, False), "fail")
        self.assertEqual(check(flag, True, "true"), "invalid")
        items = {"field": "flags", "type": "set", "expected": ["biphasic", "Incomplete curve"]}
        self.assertEqual(check(items, True, ["incomplete curve", "BIPHASIC"]), "pass")
        self.assertEqual(check(items, True, ["biphasic"]), "fail")
        self.assertEqual(check({**items, "expected": []}, True, []), "pass")
        self.assertEqual(check(items, True, "biphasic"), "invalid")

    def test_a_wrong_value_fails_a_trial_even_beside_a_missing_one(self):
        case = {"outputs": [{"field": "slope", "type": "number", "expected": "2"},
                            {"field": "pick", "type": "text", "expected": "A"}]}
        def results(value):
            return {RESULTS_FILE: json.dumps(value).encode()}
        self.assertEqual(score(case, results({"slope": 2, "pick": "a"}))["status"], "pass")
        self.assertEqual(score(case, results({"slope": 3}))["status"], "fail")
        self.assertEqual(score(case, results({"slope": 2}))["status"], "invalid")
        for files, problem in (({}, "No /work/results.json"), ({RESULTS_FILE: b"{not json"}, "not valid"),
                               ({RESULTS_FILE: b"[1]"}, "not one JSON object")):
            scored = score(case, files)
            self.assertEqual(scored["status"], "invalid")
            self.assertIn(problem, scored["results_problem"])
            self.assertFalse(scored["results_found"])
        rows = score(case, results({"slope": 3, "pick": "a"}))["outputs"]
        self.assertEqual([(row["field"], row["found"], row["status"]) for row in rows],
                         [("slope", 3, "fail"), ("pick", "a", "pass")])

    def test_the_subject_input_never_holds_an_expected_value(self):
        case = {"job": "Fit the table.", "files": [{"name": "doses.csv"}],
                "outputs": [{"field": "slope", "type": "number", "planted": "slope", "expected": "2.5"}]}
        given = task_input(case)
        self.assertEqual(given["input_files"], ["/task/doses.csv"])
        self.assertEqual(given["results_file"], "/work/results.json")
        self.assertEqual(given["results_format"], {"slope": "a JSON number"})
        self.assertNotIn("2.5", canonical(given).decode())

    def test_a_design_is_refused_for_each_rule_it_breaks(self):
        good = design([task("t1", ["S1"]), task("t2", ["S2"])])
        problems = []
        local_tasks.check_design(good, REFERENCES, ["S1", "S2"], problems)
        self.assertEqual(problems, [])
        broken = json.loads(json.dumps(good))
        broken["cases"][1]["sections"] = ["S3"]
        broken["cases"][0]["outputs"][1].pop("source_quote")
        broken["cases"][0]["outputs"][1].pop("reference_ref")
        broken["cases"][0]["outputs"].append({"field": "flag", "type": "boolean", "value": "true",
                                              "reference_ref": "REF", "source_quote": RULE})
        broken["cases"][0]["outputs"].append({"field": "z", "type": "number", "value": "3.5",
                                              "reference_ref": "REF", "source_quote": PAGE})
        broken["cases"][0]["outputs"].append({"field": "tol", "type": "text", "planted": "more_potent",
                                              "relative_tolerance": "0.1", "reference_ref": "REF", "source_quote": RULE})
        broken["cases"][1]["outputs"][0]["relative_tolerance"] = "2"
        broken["generator"]["model_quote"] = "A model the page never states."
        problems = []
        local_tasks.check_design(broken, REFERENCES, ["S1", "S2"], problems)
        text = "\n".join(problems)
        for expected in ("sections S3 are not this claim's", "No task uses the claim's sections S2",
                         "a planted text is a judgment", "a boolean is never quoted",
                         "a quoted number must be a complete token", "only a number takes a tolerance",
                         "relative_tolerance must be a decimal string from 0 to 1",
                         "The generator's model_quote must be quoted exactly"):
            self.assertIn(expected, text)

    def test_traceability_follows_where_each_value_came_from(self):
        candidate = {"generator": {"reference_ref": "REF"}}
        planted = {"outputs": [{"field": "slope", "type": "number", "planted": "slope"}]}
        self.assertTrue(traceable(candidate, planted))
        self.assertFalse(traceable({}, planted))
        quoted = {"outputs": [{"field": "z", "type": "number", "value": "2.5", "source_quote": PAGE}]}
        self.assertTrue(traceable({}, quoted))
        self.assertFalse(traceable({}, {"outputs": [{"field": "z", "type": "number", "value": "2", "source_quote": PAGE}]}))


class QualifyTests(unittest.TestCase):
    """Building the tasks: the generator plants values, the solver proves each task fair."""

    def raw(self, ref):
        return self.objects[ref]

    def setUp(self):
        self.objects = {}

    def run_design(self, proposal, runner=None, sections=("S1", "S2")):
        runner = runner or FakeRunner()
        candidate, made = qualify(proposal, REFERENCES, list(sections), runner, self.raw)
        self.objects.update(made)
        return candidate, runner

    def test_a_fair_design_is_built_and_rechecked_from_its_records(self):
        candidate, runner = self.run_design(design([task("t1", ["S1"]), task("t2", ["S2"], slope=4)]))
        self.assertEqual(candidate["status"], "qualified_local", candidate["qualification_problems"])
        first = candidate["cases"][0]
        self.assertEqual(first["planted"], {"slope": 2, "more_potent": "A", "flagged": False})
        self.assertEqual([(output["field"], output["expected"], output["source"]) for output in first["outputs"]],
                         [("slope", "2", "planted"), ("more_potent", "A", "planted")])
        self.assertEqual(first["files"][0]["name"], "doses.csv")
        self.assertEqual(self.objects[first["files"][0]["object_ref"]], b"dose,response\n1,2\n2,4\n3,6\n")
        self.assertEqual({row["status"] for row in first["solver_checks"]}, {"pass"})
        # The solver saw exactly what a subject will see.
        self.assertEqual(runner.solved[0], task_input(first))
        # Selection re-checks the saved design against its receipts, running nothing.
        self.assertIs(recheck(candidate, REFERENCES, self.raw), candidate)
        tampered = json.loads(json.dumps(candidate))
        tampered["task_receipts"]["solver_sha256"] = "0" * 64
        with self.assertRaises(Fault) as caught:
            recheck(tampered, REFERENCES, self.raw)
        self.assertEqual(caught.exception.code, "candidate_integrity")
        self.objects[first["files"][0]["object_ref"]] = b"altered"
        with self.assertRaises(Fault):
            recheck(candidate, REFERENCES, self.raw)

    def test_a_solver_that_misses_an_output_rejects_the_design(self):
        runner = FakeRunner()
        runner.faults["solver_wrong"] = True
        candidate, _ = self.run_design(design([task("t1", ["S1", "S2"])]), runner)
        self.assertEqual(candidate["status"], "rejected")
        self.assertIn("Task t1: the reference solution does not pass: slope (expected \"2\", found 2000.0)",
                      candidate["qualification_problems"][0])

    def test_generator_faults_are_named_for_the_planner(self):
        for extra, named in (({"exit": 3}, "the generator exited with code 3"),
                             ({"nested": True}, "write files by plain names"),
                             ({}, "did not finish within its time limit")):
            runner = FakeRunner()
            if not extra:
                runner.faults["generator"] = Fault("claude_timeout", "fixture")
            with self.subTest(named=named):
                candidate, _ = self.run_design(design([task("t1", ["S1", "S2"], **extra)]), runner)
                self.assertEqual(candidate["status"], "rejected")
                self.assertIn(named, " ".join(candidate["qualification_problems"]))
        # A container that cannot start is operational, never a design problem.
        runner = FakeRunner()
        runner.faults["generator"] = Fault("sandbox_start_failed", "fixture")
        with self.assertRaises(Fault):
            self.run_design(design([task("t1", ["S1", "S2"])]), runner)

    def test_a_planted_value_the_generator_did_not_print_is_refused(self):
        proposal = design([task("t1", ["S1", "S2"])])
        proposal["cases"][0]["outputs"][0]["planted"] = "intercept"
        candidate, _ = self.run_design(proposal)
        self.assertIn("names planted value 'intercept', which the generator did not print",
                      " ".join(candidate["qualification_problems"]))

    def test_a_quoted_task_and_a_reference_file_need_no_generator(self):
        self.objects["raw"] = b"dose,response\n1,2.5\n2,5\n"
        proposal = design([{"case_id": "published", "job": "Fit the published table.", "sections": ["S1", "S2"],
                            "reference_files": [{"name": "doses.csv", "reference_ref": "REF"}],
                            "outputs": [{"field": "slope", "type": "number", "value": "2.5",
                                         "relative_tolerance": "0.05", "reference_ref": "REF", "source_quote": PAGE}],
                            "applicability": "The published table."}])
        proposal.pop("generator")
        candidate, runner = self.run_design(proposal)
        self.assertEqual(candidate["status"], "qualified_local", candidate["qualification_problems"])
        self.assertEqual(runner.generated, [])
        self.assertEqual(candidate["cases"][0]["files"][0]["name"], "doses.csv")
        self.assertEqual(candidate["cases"][0]["outputs"][0]["source"], "quoted")
        self.assertTrue(traceable(candidate, candidate["cases"][0]))


class TaskSubject:
    """A subject that follows the skill on a task's files and writes results.json, or goes wrong as asked."""

    identity = {"adapter_id": "local-fixture", "model_id": "synthetic", "synthetic": True}

    def __init__(self, mode="correct"):
        self.mode, self.requests = mode, []

    def observe(self, *, source, case_input, config, timeout_seconds, task_files=None):
        self.requests.append({"case_input": case_input, "task_files": task_files})
        results = fit(task_files, case_input)
        if self.mode == "wrong":
            results["slope"] = results["slope"] / 1000  # A unit slip: the skill's own input read as micro.
        files = [] if self.mode == "silent" else [json.dumps(results).encode()]
        return {"text": "Wrote the results file.", "response_id": "synthetic-" + str(len(self.requests)),
                "model_id": "synthetic", "invocation_verified": True, "synthetic": True,
                "artifacts": [{"path": RESULTS_FILE, "sha256": digest(raw), "bytes": len(raw),
                               "base64": base64.b64encode(raw).decode()} for raw in files],
                "run_problems": ["missing Python module scipy"] if self.mode == "wrong" else []}


def critique_reply(packet, supported="A", verdicts=None):
    """A task critique as Python receives it, after its schema was checked."""
    ids = [case["case_id"] for case in packet["evidence"]["tasks"]]
    verdicts = verdicts or {}
    return {"supported_grade": supported, "findings": ["Finding."] * 5, "objections": [], "required_revisions": [],
            "case_verdicts": [{"case_id": case_id, "verdict": verdicts.get(case_id, "counts"),
                               "reason": "Fixture.", "replacement": "" if verdicts.get(case_id, "counts") == "counts"
                               else "A fixture replacement."} for case_id in ids],
            "session_id": "critic", "observed_model_ids": ["fixture-model"], "packet_ref": "packet",
            "rubric_ref": "rubric", "usage": None, "total_cost_usd": 0.0, "independence": "fixture", "ai_judgment": True}


class FlowTests(unittest.TestCase):
    """A task design through the planner's tools: qualify, select, execute and report."""

    def setUp(self):
        self.h = fixture.LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        runner = patch("sci_ai_verifier.local_tasks.SandboxRunner", FakeRunner)
        runner.start()
        self.addCleanup(runner.stop)
        self.packets = []

    def start(self, subject, *, count=1, graded=False):
        h = self.h
        h.subject = subject
        if graded:
            subject.identity = {"adapter_id": "local-fixture", "model_id": "fixture-model", "synthetic": False}
        subject.settings = {**load_configuration(), "sandbox_image": IMAGE}
        h.runtime = Runtime(h.base / "tasks", h.source, fixture.ROOT / "skills/scientific-verifier", profile="local",
                            subject_adapter=subject)
        h.data = h.runtime.call("start_verifier_run", {"source_path": str(h.source)})["data"]
        h.call("load_submitted_skill", source_path=str(h.source))
        h.snapshot = h.data["snapshot"]
        h.extract(count)
        h.call("list_local_candidates", claim_id=h.claim_id)
        with patch("sci_ai_verifier.local_candidates.fetch_public", return_value=(PAGE.encode(), PAGE)):
            h.call("fetch_local_reference", claim_id=h.claim_id, url="https://example.org/model", version="v1",
                   license="Unknown; private analysis only")
        return h.data["reference_ref"]

    def qualify(self, ref, cases):
        self.h.call("qualify_local_tasks", claim_id=self.h.claim_id, **design(cases, ref))
        return self.h.data

    def critic(self, supported="A", verdicts=None):
        def run(adapter, packet):
            self.packets.append(packet)
            return critique_reply(packet, supported, verdicts)
        return patch("sci_ai_verifier.documentary.critique_tasks", side_effect=run)

    def select(self, key, grade):
        h = self.h
        return h.select(key, target_grade=grade,
                        coverage="Three tasks, each using its sections.", stronger_grade_considered="None stronger.")

    def test_a_question_design_is_refused_while_tasks_are_required(self):
        h = self.h
        ref = self.start(TaskSubject())
        h.reference_ref = ref
        refused = h.runtime.call("qualify_local_candidate", {
            "run_id": h.data["run_id"], "state_token": h.data["state_token"], "claim_id": h.claim_id,
            "name": "Questions", "scope": "x", "method": "numeric", "limitations": "x",
            "cases": [{"case_id": name, "input": name, "expected": "1.0", "reference_ref": ref,
                       "source_quote": PAGE, "applicability": "x"} for name in ("a", "b", "c")]})
        self.assertEqual(refused["error"]["code"], "tasks_required")
        self.assertIn("qualify_local_tasks", refused["error"]["message"])

    def test_three_fair_tasks_settle_at_a_and_pass_when_the_skill_works(self):
        h = self.h
        subject = TaskSubject()
        ref = self.start(subject, graded=True)
        data = self.qualify(ref, [task("t1", ["S1"]), task("t2", ["S2"], slope=4), task("t3", ["S1", "S2"], slope=8)])
        self.assertEqual(data["outcome"], "qualified_local", data["candidate"]["qualification_problems"])
        # The reply names the programs by digest and shows the start of each file.
        self.assertIn("not repeated", data["candidate"]["solver"]["code"])
        self.assertTrue(data["candidate"]["cases"][0]["files"][0]["start"].startswith("dose,response"))
        key = data["candidate_ref"]
        with self.critic("A"):
            self.select(key, "A")
        self.assertEqual(h.data["outcome"], "local_plan_fixed")
        packet = self.packets[0]
        self.assertEqual([item["section"] for item in packet["claim"]["sections"]], ["S1", "S2"])
        self.assertIn("Notes", [item["heading"] for item in packet["claim"]["sections"]])
        self.assertEqual(packet["evidence"]["generator"]["model_quote"], MODEL)
        self.assertEqual(packet["evidence"]["solver"]["code"], "print('solver')")
        self.assertEqual(len(packet["evidence"]["tasks"]), 3)
        self.assertNotIn("claim_probe", h.data["audit"]["critique"])
        self.assertEqual(h.data["audit"]["settled_ceiling"], "A")
        h.call("execute_local_claim", claim_id=h.claim_id)
        result = h.data["result"]
        self.assertEqual((result["comparison_status"], result["scientific_status"], result["evidence_grade"]),
                         ("pass", "pass", "A"))
        self.assertEqual(result["accuracy"]["matched"], 9)
        self.assertIn("planted by Python", result["ai_involvement"]["evidence_generation"])
        # Every trial got its task's files and no expected value.
        self.assertEqual(len(subject.requests), 9)
        for request in subject.requests:
            self.assertEqual(set(request["task_files"]), {"doses.csv"})
            self.assertNotIn('"expected"', canonical(request["case_input"]).decode())
        h.call("write_report_card")
        row = h.data["report"]["claims"][0]
        self.assertEqual(row["method"], "task")
        test = row["tests"][0]
        self.assertEqual(test["expected"], {"slope": "2", "more_potent": "A"})
        self.assertEqual([item["status"] for item in test["outputs"]], ["pass", "pass"])
        markdown = Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("| t1 | 1 | pass | none | none | yes |", markdown)

    def test_one_wrong_result_fails_the_claim_and_names_the_field(self):
        h = self.h
        ref = self.start(TaskSubject("wrong"), graded=True)
        key = self.qualify(ref, [task("t1", ["S1"]), task("t2", ["S2"], slope=4)])["candidate_ref"]
        with self.critic("B"):
            self.select(key, "B")
        h.call("execute_local_claim", claim_id=h.claim_id)
        self.assertEqual((h.data["result"]["scientific_status"], h.data["result"]["evidence_grade"]), ("fail", "B"))
        h.call("write_report_card")
        test = h.data["report"]["claims"][0]["tests"][0]
        self.assertEqual(test["run_problems"], ["missing Python module scipy"])
        markdown = Path(h.data["report_markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("| t1 | 1 | fail | slope fail (2; 0.002) | missing Python module scipy | yes |", markdown)
        self.assertIn("missing Python module scipy", markdown)

    def test_the_page_shows_each_task_its_checks_and_what_the_skill_lacked(self):
        from sci_ai_verifier.report_html import publish
        h = self.h
        ref = self.start(TaskSubject("wrong"), graded=True)
        key = self.qualify(ref, [task("t1", ["S1"]), task("t2", ["S2"], slope=4)])["candidate_ref"]
        with self.critic("B"):
            self.select(key, "B")
        h.call("execute_local_claim", claim_id=h.claim_id)
        h.call("write_report_card")
        page = Path(publish(h.base / "tasks", h.data["run_id"])["path"]).read_text(encoding="utf-8")
        for expected in ("<h3>The tasks</h3>", "Checked outputs", "slope = 2", "±10%", "fail: slope: 0.002",
                         "missing Python module scipy", "How the input files were made", MODEL,
                         "The reference solution's code", "Task 1 · t1", "<dt>Task</dt>"):
            self.assertIn(expected, page)
        self.assertNotIn("Claim-only check", page)
        # With every section set aside, the page says why each one was.
        h.data = h.runtime.call("start_verifier_run", {"source_path": str(h.source)})["data"]
        h.call("load_submitted_skill", source_path=str(h.source))
        h.snapshot = h.data["snapshot"]
        h.extract(0)
        h.call("write_report_card")
        page = Path(publish(h.base / "tasks", h.data["run_id"])["path"]).read_text(encoding="utf-8")
        self.assertIn("set aside: Synthetic: nothing to test.", page)
        self.assertIn("2 of 2 sections were set aside as having nothing to test", page)

    def test_no_results_file_is_invalid_and_the_claim_inconclusive(self):
        h = self.h
        ref = self.start(TaskSubject("silent"), graded=True)
        key = self.qualify(ref, [task("t1", ["S1"]), task("t2", ["S2"], slope=4)])["candidate_ref"]
        with self.critic("B"):
            self.select(key, "B")
        h.call("execute_local_claim", claim_id=h.claim_id)
        self.assertEqual(h.data["result"]["scientific_status"], "inconclusive")
        self.assertIn("invalid_observations_retained", h.data["result"]["execution_limit_reasons"])

    def test_a_task_the_critique_does_not_count_lowers_the_ceiling(self):
        h = self.h
        ref = self.start(TaskSubject(), graded=True)
        key = self.qualify(ref, [task("t1", ["S1"]), task("t2", ["S2"], slope=4), task("t3", ["S1", "S2"], slope=8)])[
            "candidate_ref"]
        with self.critic("A", {"t3": "duplicate"}):
            self.select(key, "A")
        self.assertEqual(h.data["outcome"], "local_grade_revision_required")
        self.assertEqual(h.data["settled_grade"], "B")
        self.assertEqual(h.data["case_gap"]["tasks_needed"], 1)
        self.assertEqual(h.data["case_replacements"][0]["case_id"], "t3")

    def test_a_task_design_cannot_yet_be_exported(self):
        from sci_ai_verifier.local_catalog import export_bundle
        ref = self.start(TaskSubject())
        key = self.qualify(ref, [task("t1", ["S1"]), task("t2", ["S2"], slope=4)])["candidate_ref"]
        with self.assertRaises(Fault) as caught:
            export_bundle(self.h.runtime.store, [key], redistribution="Synthetic fixture page; test-only, never shared.")
        self.assertEqual(caught.exception.code, "candidate_not_exportable")

    def test_a_design_for_another_claim_s_sections_is_refused_at_selection(self):
        h = self.h
        ref = self.start(TaskSubject(), count=2)
        first = self.qualify(ref, [task("t1", ["S1"]), task("t2", ["S1"], slope=4)])
        self.assertEqual(first["outcome"], "qualified_local", first["candidate"]["qualification_problems"])
        other = h.claims[1]["claim_id"]
        h.call("list_local_candidates", claim_id=other)
        self.assertIn(first["candidate_ref"], [item["candidate_ref"] for item in h.data["candidates"]])
        h.claim_id = other
        with self.critic("B"):
            self.select(first["candidate_ref"], "B")
        self.assertEqual((h.data["outcome"], h.data["reason"]), ("local_grade_proposal_refused", "sections_unused"))
        self.assertEqual((h.data["unused_sections"], h.data["sections_outside_claim"]), (["S2"], ["S1"]))
        self.assertEqual(self.packets, [])


class SandboxInputTests(unittest.TestCase):
    """A task's files reach the container read-only at /task, never copied into /work."""

    def test_task_files_are_mounted_read_only(self):
        from sci_ai_verifier.sandbox import DockerSandbox
        commands = []

        def process(command, **kwargs):
            commands.append(command)
            if "context" in command:
                return 0, canonical("npipe:////./pipe/docker_engine"), b""
            if "inspect" in command:
                return 0, canonical([{"Os": "linux", "Id": IMAGE}]), b""
            return 0, b"[]", b""

        with tempfile.TemporaryDirectory() as temporary:
            settings = {**load_configuration(), "sandbox_image": IMAGE}
            with patch("shutil.which", return_value="docker.exe"), DockerSandbox(
                    Path(temporary), settings, process=process, inputs={"doses.csv": b"dose\n1\n"}) as box:
                run = next(command for command in commands if "run" in command)
                mounts = [run[index + 1] for index, value in enumerate(run) if value == "--mount"]
                self.assertEqual(len(mounts), 2)
                self.assertTrue(mounts[1].endswith("target=/task,readonly"))
                staged = Path(mounts[1].split("source=")[1].split(",target")[0])
                self.assertEqual((staged / "doses.csv").read_bytes(), b"dose\n1\n")
            self.assertFalse(staged.exists())
            with patch("shutil.which", return_value="docker.exe"), self.assertRaises(Fault):
                with DockerSandbox(Path(temporary), settings, process=process, inputs={"../x": b"1"}):
                    self.fail("A path outside the task folder must be refused.")


if __name__ == "__main__":
    unittest.main()
