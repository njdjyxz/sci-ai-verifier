"""Task tests: designs that run the whole skill on input Python built, checked field by field.

`local-tasks.md` owns the rules. A task gives the subject input files, a job and fixed output
fields; Python builds the expected values into the files by running the planner's generator,
proves the task fair by running the planner's reference solution, and reads each trial's
`results.json` itself. Mechanical qualification never grants scientific approval.
"""

import base64
import json
import math
import re
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .answers import TOLERANCE, in_quote, key_items, number, parsed, whole_token_in
from .common import Fault, canonical, digest, utc_now
from .storage import atomic_write

METHOD_VERSION = "local-task-comparison-1"
TYPES = ("number", "text", "boolean", "set")
MAX_TASKS = 6
MAX_OUTPUTS = 12
MAX_FILES = 20
# The subject and the solver write here; Python reads it from the container's new files.
RESULTS_FILE = "results.json"
RESULTS_PATH = "/work/" + RESULTS_FILE
FORMATS = {"number": "a JSON number", "text": "a JSON string", "boolean": "true or false",
           "set": "a JSON array of strings, in any order"}
# The one line Python writes for every task, as the answer-format line of a question.
RESULTS_INSTRUCTION = ("Write " + RESULTS_PATH + ": one JSON object holding exactly the fields of results_format, "
                       "each value in the form given there. Input files are read-only.")
FIELD = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,59}")
FILE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
PLANTED_BYTES = 64 * 1024
STDERR_TAIL = 600
# A program that runs too long or writes too much is a fault of the design, reported to the planner
# like any other; a container that cannot start is operational and stops the call.
DESIGN_FAULTS = {"claude_timeout": "did not finish within its time limit",
                 "sandbox_timeout": "did not finish within its time limit",
                 "claude_output_limit": "printed more than its output limit",
                 "sandbox_artifacts_invalid": "wrote files past the size, count or credential checks"}
# Generous: a generator writes a few small files, and a solver fits a few curves.
GENERATOR_SECONDS = 120
SOLVER_SECONDS = 300
QUALIFICATION_LIMITS = [
    "Mechanical qualification only: Python ran the generator and the reference solution and checked every "
    "quote, but whether the generator implements its quoted model, and whether the solver is a genuine analysis, "
    "is the critique's to judge.",
    "Tasks are illustrative, not a representative scientific benchmark.",
    "Qualification alone carries no scientific verdict or evidence grade; the grade is settled separately.",
]


def task_input(case):
    """What the subject, and the reference solution, receive for one task: never an expected value."""
    from .sandbox import TASK_ROOT  # Imported here: the sandbox module reaches this one through the tool schemas.
    names = [item["name"] for item in case.get("files") or []]
    return {"task": case["job"], "input_files": [TASK_ROOT + "/" + name for name in names],
            "results_file": RESULTS_PATH,
            "results_format": {output["field"]: FORMATS[output["type"]] for output in case["outputs"]},
            "answer_format": RESULTS_INSTRUCTION}


def reference_refs(candidate):
    """Every reference a task design rests on: its model, its quoted and basis values, its input files."""
    refs = []
    if candidate.get("generator"):
        refs.append(candidate["generator"]["reference_ref"])
    for case in candidate["cases"]:
        refs += [item["reference_ref"] for item in case.get("reference_files") or []]
        refs += [output["reference_ref"] for output in case["outputs"] if output.get("reference_ref")]
    return list(dict.fromkeys(refs))


def decimal_text(value):
    """A JSON number as an exact decimal string, or None for anything else (booleans included)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return str(Decimal(repr(value)) if isinstance(value, float) else Decimal(value))


def fits(kind, value):
    """True when a planted or reported JSON value has the shape of an output of `kind`."""
    if kind == "number":
        return decimal_text(value) is not None
    if kind == "text":
        return isinstance(value, str) and bool(value.strip())
    if kind == "boolean":
        return isinstance(value, bool)
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def as_expected(kind, value):
    """A planted value as the record keeps it: a number as its exact decimal string."""
    return decimal_text(value) if kind == "number" else value


def tolerance(output):
    """The absolute distance a number may miss by, for an expected value (`local-tasks.md`)."""
    expected = Decimal(output["expected"])
    allowed = [Decimal(output["absolute_tolerance"])] if output.get("absolute_tolerance") else []
    if output.get("relative_tolerance"):
        allowed.append(Decimal(output["relative_tolerance"]) * abs(expected))
    return max(allowed) if allowed else TOLERANCE


def fold(text):
    return " ".join(text.split()).casefold()


def check(output, present, found):
    """One output's verdict on a reported value: `pass`, `fail`, or `invalid` when absent or misshapen."""
    kind = output["type"]
    if not present or not fits(kind, found):
        return "invalid"
    expected = output["expected"]
    if kind == "number":
        return "pass" if abs(Decimal(decimal_text(found)) - Decimal(expected)) <= tolerance(output) else "fail"
    if kind == "text":
        return "pass" if fold(found) == fold(expected) else "fail"
    if kind == "boolean":
        return "pass" if found is expected else "fail"
    return "pass" if {fold(item) for item in found} == {fold(item) for item in expected} else "fail"


def read_results(files):
    """The results object from a container's new files (path -> bytes), or (None, why not)."""
    raw = files.get(RESULTS_FILE)
    if raw is None:
        return None, "No " + RESULTS_PATH + " was written."
    try:
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError):
        return None, RESULTS_PATH + " is not valid UTF-8 JSON."
    if not isinstance(value, dict):
        return None, RESULTS_PATH + " is not one JSON object."
    return value, None


def score(case, files):
    """A trial's status and each output's verdict ("Reading a trial's results" in local-tasks.md).

    A wrong value of the right shape is a wrong result, so it fails the trial even when another field
    is missing; a trial with nothing wrong and something missing or misshapen is `invalid`.
    """
    value, problem = read_results(files)
    rows = []
    for output in case["outputs"]:
        present = value is not None and output["field"] in value
        found = value.get(output["field"]) if present else None
        verdict = check(output, present, found)
        rows.append({"field": output["field"], "type": output["type"], "expected": output["expected"],
                     **({"tolerance": str(tolerance(output))} if output["type"] == "number" else {}),
                     "present": present, "found": found if present else None, "status": verdict})
    statuses = {row["status"] for row in rows}
    status = "fail" if "fail" in statuses else "invalid" if "invalid" in statuses else "pass"
    return {"status": status, "outputs": rows, "results_found": value is not None,
            **({"results_problem": problem} if problem else {})}


def tail(text):
    return text[-STDERR_TAIL:] if isinstance(text, str) else ""


class SandboxRunner:
    """Runs a design's programs, each in a new container of the operator's image with no network."""

    def __init__(self, settings, *, log=None, sandbox_factory=None):
        if not settings.get("sandbox_image"):
            raise Fault("sandbox_configuration_required", "Task tests need the operator's pinned container image.")
        if sandbox_factory is None:
            from .sandbox import DockerSandbox as sandbox_factory
        self.settings, self.log, self.factory = settings, log, sandbox_factory

    def generate(self, code, arguments):
        with tempfile.TemporaryDirectory(prefix="sci-verifier-generator-") as temporary:
            source = Path(temporary)
            atomic_write(source / "generator.py", code.encode("utf-8"))
            with self.factory(source, self.settings, timeout=GENERATOR_SECONDS + 30, log=self.log) as sandbox:
                result = sandbox.command("mkdir -p /work/out && cd /work/out && python3 -I /work/generator.py",
                                         stdin=arguments, timeout=GENERATOR_SECONDS)
                files = sandbox.collect() if not result["exit_code"] else []
                image = sandbox.image
        written = {}
        for item in files:
            if item["path"].startswith("out/"):
                written[item["path"][4:]] = base64.b64decode(item["base64"], validate=True)
        return {"exit_code": result["exit_code"], "stdout": result["stdout"], "stderr": tail(result["stderr"]),
                "files": written, "image_id": image}

    def solve(self, code, given, files):
        with tempfile.TemporaryDirectory(prefix="sci-verifier-solver-") as temporary:
            source = Path(temporary)
            atomic_write(source / "solver.py", code.encode("utf-8"))
            with self.factory(source, self.settings, timeout=SOLVER_SECONDS + 30, log=self.log,
                              inputs=files) as sandbox:
                result = sandbox.command("cd /work && python3 -I /work/solver.py",
                                         stdin=canonical(given).decode("utf-8"), timeout=SOLVER_SECONDS)
                found = sandbox.collect()
                image = sandbox.image
        written = {item["path"]: base64.b64decode(item["base64"], validate=True) for item in found}
        return {"exit_code": result["exit_code"], "stderr": tail(result["stderr"]),
                "results": written.get(RESULTS_FILE), "image_id": image}


class RecordedRunner:
    """Answers from a saved design's receipts, so selection re-checks it without running anything.

    `objects(ref)` returns a stored object's bytes. A program or argument the receipts do not hold
    means the design changed, which is an integrity fault, never a new run.
    """

    def __init__(self, candidate, objects):
        self.receipts, self.objects = candidate.get("task_receipts") or {}, objects

    def generate(self, code, arguments):
        run = next((item for item in self.receipts.get("generator_runs", []) if item["arguments"] == arguments), None)
        if run is None or digest(code.encode("utf-8")) != self.receipts.get("generator_sha256"):
            raise Fault("candidate_integrity", "A task design's generator or its recorded runs changed.", fatal=True)
        files = {item["name"]: self.objects(item["object_ref"]) for item in run["files"]}
        if any(digest(raw) != item["object_ref"] for item, raw in zip(run["files"], files.values())):
            raise Fault("candidate_integrity", "A task design's recorded file changed.", fatal=True)
        return {"exit_code": run["exit_code"], "stdout": run["stdout"], "stderr": run["stderr"], "files": files,
                "image_id": self.receipts.get("image_id")}

    def solve(self, code, given, files):
        key = digest(canonical({"input": given, "files": {name: digest(raw) for name, raw in files.items()}}))
        run = next((item for item in self.receipts.get("solver_runs", []) if item["key"] == key), None)
        if run is None or digest(code.encode("utf-8")) != self.receipts.get("solver_sha256"):
            raise Fault("candidate_integrity", "A task design's solver or its recorded runs changed.", fatal=True)
        return {"exit_code": run["exit_code"], "stderr": run["stderr"],
                "results": run["results"].encode("utf-8") if isinstance(run["results"], str) else None,
                "image_id": self.receipts.get("image_id")}


def quote_problem(references, ref, quote):
    """Why a quote does not stand, or None: it must occur exactly in a reference this claim fetched."""
    reference = references.get(ref)
    if not reference or not quote or quote not in (reference.get("text") or ""):
        return "must be quoted exactly from a reference fetched for this claim"
    return None


def quoted_value_problem(kind, value, quote):
    """Why a literal expected value is not in its quote, or None."""
    if kind == "boolean":
        return "a boolean is never quoted; plant it with the generator and quote the rule it follows"
    if kind == "number":
        return None if parsed(value) is not None and whole_token_in(value.strip(), quote) else \
            "a quoted number must be a complete token of its quote"
    if kind == "set":
        items = key_items(value)
        return None if items and in_quote("set", value, quote) else \
            "a quoted set gives its items separated by commas, each found in the quote"
    return None if in_quote("term", value, quote) else "a quoted text's words must appear in its quote"


def check_design(proposal, references, claim_sections, problems):
    """The checks that need no program run: shapes, quotes, tolerances and the claim's sections."""
    cases = proposal["cases"]
    if len({case["case_id"] for case in cases}) != len(cases):
        problems.append("Task case_ids must be unique.")
    if len({case["job"] for case in cases}) != len(cases):
        problems.append("Task jobs must be distinct.")
    generator = proposal.get("generator")
    if generator:
        problem = quote_problem(references, generator["reference_ref"], generator["model_quote"])
        if problem:
            problems.append("The generator's model_quote " + problem + ".")
    used = set()
    for case in cases:
        label = "Task " + case["case_id"] + ": "
        outside = [name for name in case["sections"] if name not in claim_sections]
        if outside:
            problems.append(label + "sections " + ", ".join(outside) + " are not this claim's.")
        used.update(case["sections"])
        if "arguments" in case and not generator:
            problems.append(label + "arguments need the design's generator.")
        names = [item["name"] for item in case.get("reference_files") or []]
        if len(set(names)) != len(names) or any(not FILE_NAME.fullmatch(name) for name in names):
            problems.append(label + "reference_files need distinct plain file names.")
        for item in case.get("reference_files") or []:
            if item["reference_ref"] not in references:
                problems.append(label + "reference file " + item["name"] + " must come from a reference fetched "
                                "for this claim.")
        fields = [output["field"] for output in case["outputs"]]
        if len(set(fields)) != len(fields) or any(not FIELD.fullmatch(field) for field in fields):
            problems.append(label + "output fields need distinct names of letters, digits and underscores, "
                            "starting with a letter.")
        for output in case["outputs"]:
            where = label + "output " + output["field"] + ": "
            kind = output["type"]
            if ("planted" in output) == ("value" in output):
                problems.append(where + "give exactly one of planted and value.")
                continue
            if kind != "number" and ("relative_tolerance" in output or "absolute_tolerance" in output):
                problems.append(where + "only a number takes a tolerance.")
            for key in ("relative_tolerance", "absolute_tolerance"):
                if key in output:
                    try:
                        bound = number(output[key])
                    except ValueError:
                        bound = None
                    if bound is None or bound < 0 or (key == "relative_tolerance" and bound > 1):
                        problems.append(where + key + " must be a decimal string from 0" +
                                        (" to 1." if key == "relative_tolerance" else " up."))
            quoted = "source_quote" in output or "reference_ref" in output
            if quoted:
                problem = quote_problem(references, output.get("reference_ref"), output.get("source_quote"))
                if problem:
                    problems.append(where + "its source_quote " + problem + ".")
                    continue
            if "value" in output:
                if not quoted:
                    problems.append(where + "a quoted value needs reference_ref and source_quote.")
                    continue
                problem = quoted_value_problem(kind, output["value"], output["source_quote"])
                if problem:
                    problems.append(where + problem + ".")
            elif "arguments" not in case:
                problems.append(where + "a planted value needs the task's arguments, which the generator plants it from.")
            elif kind != "number" and not quoted:
                problems.append(where + "a planted " + kind + " is a judgment about what was planted, so it quotes "
                                "the rule it follows in reference_ref and source_quote.")
    unused = [name for name in claim_sections if name not in used]
    if unused:
        problems.append("No task uses the claim's sections " + ", ".join(unused) + "; every section of the claim is "
                        "used by at least one task (\"Tasks\" in local-tasks.md).")


def planted_from(stdout):
    """The planted values a generator printed: its whole output, or else its last line, as one JSON object."""
    if len(stdout.encode("utf-8")) > PLANTED_BYTES:
        return None
    lines = [line for line in stdout.splitlines() if line.strip()]
    for text in (stdout, lines[-1] if lines else ""):
        try:
            value = json.loads(text)
        except (ValueError, RecursionError):
            continue
        if isinstance(value, dict):
            return value
    return None


def build(case, generated, references, raw, problems):
    """The task's input files and resolved outputs, from its generator run and reference files."""
    label = "Task " + case["case_id"] + ": "
    files, planted = {}, {}
    if generated is not None:
        if generated["exit_code"]:
            problems.append(label + "the generator exited with code " + str(generated["exit_code"])
                            + (": " + generated["stderr"] if generated["stderr"] else "") + ".")
            return None
        planted = planted_from(generated["stdout"])
        if planted is None:
            problems.append(label + "the generator must print one JSON object of planted values, at most "
                            + str(PLANTED_BYTES) + " bytes.")
            return None
        nested = [name for name in generated["files"] if "/" in name or not FILE_NAME.fullmatch(name)]
        if nested:
            problems.append(label + "the generator wrote " + ", ".join(sorted(nested)[:5]) + "; write files by plain "
                            "names directly in /work/out.")
            return None
        files.update(generated["files"])
    for item in case.get("reference_files") or []:
        if item["name"] in files:
            problems.append(label + "file " + item["name"] + " is both generated and a reference file.")
            return None
        resource = references.get(item["reference_ref"])
        if resource:
            files[item["name"]] = raw(resource["raw_ref"])
    if len(files) > MAX_FILES:
        problems.append(label + "a task has at most " + str(MAX_FILES) + " input files.")
        return None
    outputs = []
    for output in case["outputs"]:
        if "planted" in output:
            if output["planted"] not in planted or not fits(output["type"], planted[output["planted"]]):
                problems.append(label + "output " + output["field"] + " names planted value " + repr(output["planted"])
                                + ", which the generator did not print as " + FORMATS[output["type"]] + ".")
                return None
            expected, source = as_expected(output["type"], planted[output["planted"]]), "planted"
        else:
            value = output["value"].strip()
            expected = (str(number(value)) if output["type"] == "number"
                        else key_items(value) if output["type"] == "set" else value)
            source = "quoted"
        outputs.append({**output, "expected": expected, "source": source})
    return files, planted, outputs


def qualify(proposal, references, claim_sections, runner, raw):
    """Check a proposed task design and build its tasks. `runner` runs programs (SandboxRunner) or
    replays a saved design (RecordedRunner); `raw(ref)` returns a stored object's bytes.

    Returns the candidate and the input files it made, by object digest, for the caller to store.
    """
    from .common import validate
    from .local import schemas
    from .tools import obj, string
    from .local_candidates import safe_payload
    validate({**proposal, "claim_id": "candidate"}, schemas({}, obj, string)["qualify_local_tasks"])
    safe_payload(proposal)
    problems = []
    check_design(proposal, references, claim_sections, problems)
    cases, made = [], {}
    generator_runs, solver_runs, image = [], [], None
    def run(program, case_id, call):
        """One program run, or None with the design problem named when the program itself was at fault."""
        try:
            return call()
        except Fault as error:
            if error.code not in DESIGN_FAULTS:
                raise
            problems.append("Task " + case_id + ": the " + program + " " + DESIGN_FAULTS[error.code] + ".")
            return None

    if not problems:
        for case in proposal["cases"]:
            generated = None
            if "arguments" in case:
                generated = run("generator", case["case_id"],
                                lambda: runner.generate(proposal["generator"]["code"], case["arguments"]))
                if generated is None:
                    continue
                image = generated["image_id"] or image
                generator_runs.append({"arguments": case["arguments"], "exit_code": generated["exit_code"],
                                       "stdout": generated["stdout"][:PLANTED_BYTES], "stderr": generated["stderr"],
                                       "files": [{"name": name, "object_ref": digest(data), "bytes": len(data)}
                                                 for name, data in sorted(generated["files"].items())]})
            built = build(case, generated, references, raw, problems)
            if built is None:
                continue
            files, planted, outputs = built
            for data in files.values():
                made[digest(data)] = data
            task = {**case, "outputs": outputs, "planted": planted,
                    "files": [{"name": name, "object_ref": digest(data), "bytes": len(data)}
                              for name, data in sorted(files.items())]}
            given = task_input(task)
            solved = run("reference solution", case["case_id"],
                         lambda: runner.solve(proposal["solver"]["code"], given, files))
            if solved is None:
                continue
            image = solved["image_id"] or image
            results = solved["results"]
            solver_runs.append({"key": digest(canonical({"input": given, "files": {name: digest(data) for name, data
                                                                                   in files.items()}})),
                                "case_id": case["case_id"], "exit_code": solved["exit_code"], "stderr": solved["stderr"],
                                "results": results.decode("utf-8", errors="replace") if results is not None else None})
            verdict = score(task, {RESULTS_FILE: results} if results is not None else {})
            task.update(solver_results=read_results({RESULTS_FILE: results} if results is not None else {})[0],
                        solver_checks=verdict["outputs"])
            if verdict["status"] != "pass":
                wrong = [row["field"] + " (expected " + json.dumps(row["expected"]) + ", found "
                         + (json.dumps(row["found"]) if row["present"] else "nothing") + ")"
                         for row in verdict["outputs"] if row["status"] != "pass"]
                problems.append("Task " + case["case_id"] + ": the reference solution does not pass"
                                + (" (" + verdict["results_problem"] + (" Solver exit code " + str(solved["exit_code"])
                                   + ": " + solved["stderr"] if solved["exit_code"] else "") + ")"
                                   if verdict.get("results_problem") else ": " + "; ".join(wrong)) + ".")
            cases.append(task)
    candidate = {"schema_version": 1, "method_version": METHOD_VERSION, "method": "task",
                 **{key: proposal[key] for key in ("name", "scope", "limitations", "generator", "solver")
                    if key in proposal},
                 "cases": cases if not problems else proposal["cases"],
                 "task_receipts": {"generator_sha256": digest(proposal["generator"]["code"].encode("utf-8"))
                                   if proposal.get("generator") else None,
                                   "solver_sha256": digest(proposal["solver"]["code"].encode("utf-8")),
                                   "image_id": image, "generator_runs": generator_runs, "solver_runs": solver_runs},
                 "status": "rejected" if problems else "qualified_local", "scientific_approval": "provisional",
                 "qualification_problems": sorted(set(problems)), "controls": [],
                 "qualification_limitations": QUALIFICATION_LIMITS, "qualified_at": utc_now()}
    return candidate, (made if not problems else {})


def proposal_of(candidate):
    """The planner's proposal inside a saved task design, as qualification received it."""
    keys = ("case_id", "job", "sections", "arguments", "reference_files", "applicability")
    output_keys = ("field", "type", "planted", "value", "relative_tolerance", "absolute_tolerance",
                   "reference_ref", "source_quote")
    return {**{key: candidate[key] for key in ("name", "scope", "limitations", "generator", "solver") if key in candidate},
            "cases": [{**{key: case[key] for key in keys if key in case},
                       "outputs": [{key: output[key] for key in output_keys if key in output}
                                   for output in case["outputs"]]} for case in candidate["cases"]]}


def recheck(candidate, references, raw):
    """A saved design re-checked against its own receipts, with its sections taken as its own."""
    sections = sorted({name for case in candidate["cases"] for name in case["sections"]})
    checked, _ = qualify(proposal_of(candidate), references, sections, RecordedRunner(candidate, raw), raw)
    if checked["status"] != "qualified_local" or canonical(checked["cases"]) != canonical(candidate["cases"]):
        raise Fault("candidate_integrity", "Task design no longer passes qualification against its records.", fatal=True)
    return candidate


def reply_view(candidate, raw, preview=400, shown=3):
    """The candidate as the planner's reply shows it. The programs, which the planner wrote, are named by
    digest rather than repeated, and the start of a task's first text files is shown instead."""
    cases = []
    for case in candidate["cases"]:
        files = []
        for index, item in enumerate(case.get("files") or []):
            entry = dict(item)
            if index < shown:
                try:
                    entry["start"] = raw(item["object_ref"])[:preview].decode("utf-8", errors="replace")
                except (Fault, OSError):
                    entry["start"] = None
            files.append(entry)
        cases.append({**case, "files": files} if case.get("files") else case)
    view = {**candidate, "cases": cases}
    for key in ("generator", "solver"):
        if candidate.get(key):
            view[key] = {**candidate[key], "code": "(" + str(len(candidate[key]["code"])) + " characters, SHA256 "
                         + digest(candidate[key]["code"].encode("utf-8")) + "; not repeated)"}
    return view


def traceable(candidate, case):
    """True when every output's expected value traces to retrieved bytes: planted by the generator from
    its quoted model, a planted judgment also quoting its rule, or a quoted value as a complete token."""
    for output in case["outputs"]:
        if "planted" in output:
            if not candidate.get("generator") or (output["type"] != "number" and not output.get("source_quote")):
                return False
            continue
        kind = {"number": "numeric", "text": "term", "set": "set"}.get(output["type"])
        if kind is None or not in_quote(kind, output["value"], output["source_quote"], tokens=True):
            return False
    return True


def critique_packet(claim, sections, candidate, references, args, ceiling, limits, trials, objections, record, raw):
    """The bounded packet a task design's critique sees ("Selecting and critiquing a task design" in
    local-tasks.md): the claim with its sections' text and the whole design, never the planning."""
    from .documentary import TASK_CRITIQUE_RUBRIC
    from .local_science import PLANNER_JUSTIFICATION
    from .local import JUSTIFICATION_TEXT, NOTE_TEXT

    def clip(text, size=800):
        text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
        return text if len(text) <= size else text[:size] + " [truncated]"

    def start(item, size=1500):
        try:
            return clip(raw(item["object_ref"]).decode("utf-8"), size)
        except (UnicodeError, Fault, OSError):
            return None  # A binary file: its name and size say what it is.

    def url(ref):
        return references.get(ref, {}).get("url")

    sources = {}
    for item in references.values():
        sources[item["url"]] = {"url": item["url"], "version": item["version"], "license": item["license"],
                                "origin": item.get("origin", "unrecorded")}
    tasks = []
    for case in candidate["cases"]:
        tasks.append({"case_id": case["case_id"], "sections": case["sections"], "job": clip(case["job"], 4000),
                      **({"arguments": clip(case["arguments"], 2000)} if "arguments" in case else {}),
                      "files": [{"name": item["name"], "bytes": item["bytes"],
                                 **({"start": start(item)} if index < 4 else {})}
                                for index, item in enumerate(case.get("files") or [])],
                      **({"reference_files": [{"name": item["name"], "url": url(item["reference_ref"])}
                                              for item in case["reference_files"]]} if case.get("reference_files") else {}),
                      "planted": clip(case.get("planted") or {}, 2000),
                      "outputs": [{"field": output["field"], "type": output["type"],
                                   "expected": output["expected"], "source": output["source"],
                                   **{key: output[key] for key in ("relative_tolerance", "absolute_tolerance")
                                      if key in output},
                                   **({"quote": clip(output["source_quote"]), "url": url(output["reference_ref"])}
                                      if output.get("source_quote") else {})}
                                  for output in case["outputs"]],
                      "solver_results": clip(case.get("solver_results"), 2000),
                      "applicability": clip(case["applicability"])})
    generator = candidate.get("generator")
    return {"claim": {**{key: claim[key] for key in ("statement", "scope", "expected_behavior")},
                      "sections": sections},
            "proposed_grade": args["target_grade"], "rubric": TASK_CRITIQUE_RUBRIC,
            "prior_objections": [clip(item, 1000) for item in objections],
            "evidence": {"method": "task", "method_version": candidate["method_version"],
                         "design_scope": clip(candidate["scope"], NOTE_TEXT),
                         "design_limitations": clip(candidate["limitations"], NOTE_TEXT),
                         "task_count": len(candidate["cases"]), "trials_per_task": trials,
                         "references": [sources[key] for key in sorted(sources)],
                         "generator": {"code": generator["code"], "model_quote": clip(generator["model_quote"], 2000),
                                       "model_url": url(generator["reference_ref"])} if generator else None,
                         "solver": {"code": candidate["solver"]["code"]},
                         "tasks": tasks},
            "justification": {key: clip(args[key], JUSTIFICATION_TEXT) for key in PLANNER_JUSTIFICATION},
            "python_checked": {"evidence_ceiling": ceiling, "evidence_limits": limits, "search_record": record,
                               "note": "Python already ran the generator once per task with arguments, stored the files "
                                       "every trial receives, checked every quote exactly against the pinned "
                                       "reference bytes, checked that the tasks use every section of the claim, and "
                                       "ran the reference solution on each task, on whose results every output "
                                       "passed. Judge whether this evidence is fit for this claim at the proposed "
                                       "grade, and give every task a verdict in case_verdicts. Python then "
                                       "recomputes the ceiling over the tasks you count, under "
                                       "rubric.case_requirements."}}
