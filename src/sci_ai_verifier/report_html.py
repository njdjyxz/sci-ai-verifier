"""A finished run as one HTML page for people to read ("HTML report" in LOCAL-INSTALL.md).

Numbers and tables come from the run's own records: the report card, the run journal, the
workflow log, the subject replies and the content-addressed store. Plain-language text (what the
skill does, what each claim says and each test asks, summaries and review notes) comes from a
notes file written after the run, by the agent that asked for the verification, and the page
marks it as such. The page is one file with no scripts and no outside styles, and every recorded
string is escaped. Nothing here changes a run: the page and its notes live in `.verifier/reports/`.
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "report_html.py"
TYPES = {"numeric": "number", "exact": "exact token", "term": "word or phrase", "choice": "multiple choice",
         "expression": "formula", "list": "list, in order", "set": "list, any order"}
NOT_COUNTED = {"leaked": "it gives away the answer or the rule", "duplicate": "it repeats another test",
               "beyond_scope": "the claim alone does not settle it", "naming": "it only asks what something is called",
               "unsound": "its expected value or tolerance is not right"}
# The verdict table's questions, as the page names them ("Cases each grade requires" in evidence-rubric.md).
QUESTIONS = {"outside_claim": "Outside the claim?", "gives_away": "Gives the answer or the rule away?",
             "job_decides": "Says how to compute it, so the skill can be skipped?",
             "repeats": "Repeats an earlier task?", "key_wrong": "Key or tolerance wrong?",
             "wrong_passes": "Would a wrong method pass?"}
OUTCOMES = {"local_plan_fixed": "plan fixed", "local_grade_revision_required": "sent back to revise",
            "local_grade_proposal_refused": "refused before review"}
REFUSALS = {"prior_review_in_packet": "its notes mentioned an earlier review",
            "local_design_unchanged": "the same design again",
            "sections_unused": "its tasks did not use this claim's sections",
            "critique_packet_too_large": "its review packet was over the size limit"}
HOST = {"managed_host_configuration_is_trusted": "The verifier trusts the computer and the settings it runs on.",
        "local_container_execution": "The tests ran in a container on one local computer.",
        "container_image_not_configured": "No container image was set, so no task could run.",
        "evidence_grade_is_an_evidence_strength_indicator_not_an_endorsement":
            "A grade shows how strong the evidence is. It is not an approval of the skill.",
        "live_cli_acceptance_required": "The verifier itself is still being tested with live runs.",
        "external_app_adapters_are_operator_trusted": "Outside tools added by the operator are trusted as they are."}
GUIDE = ("Fill in the empty fields below in plain words and short sentences, for a reader who has not seen the "
         "skill. Do not quote the skill. skill.name: a short plain name. skill.summary: 3 to 5 sentences on what "
         "the skill does. For each claim: title, 2 to 5 words; says, 2 to 4 sentences on what the claim says; "
         "summary, 2 to 4 sentences on how it did, naming any test that failed, did not count or passed on "
         "tolerance only, and any fact left untested. For each test: asks, the question or task in one short plain sentence; review, only if you checked a "
         "failed or odd test, saying whether the question, the key or the skill was at fault. cautions: short "
         "sentences the reader should know. by: your name; author: who wrote this text, and when. Leave every "
         "other field as it is, then run the render command to update the page.")


class ReportUnavailable(Exception):
    """The run has no report card to draw a page from."""


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_text(path, text):
    """Bytes, so the page and notes keep LF endings on every platform."""
    Path(path).write_bytes(text.encode("utf-8"))


def when(stamp):
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def first_line(text):
    lines = [line.strip() for line in str(text or "").strip().splitlines() if line.strip()]
    return lines[0] if lines else ""


def gist(question):
    """The sentence that asks, without the setting before it or the options after it."""
    text = " ".join(str(question or "").split())
    mark = text.find("?")
    if mark < 0:
        core = re.split(r"(?<=[.!])\s+", text.rstrip(". "))[-1]
    else:
        start = max(text.rfind(". ", 0, mark), text.rfind("! ", 0, mark))
        core = text[start + 2 if start >= 0 else 0:mark + 1]
    return core if len(core) <= 200 else core[:197].rstrip() + "…"


def money(value):
    return "–" if value is None else f"${value:,.2f}"


def minutes(seconds):
    return "–" if seconds is None else f"{seconds / 60:.0f} min"


# ---------------------------------------------------------------- reading the records

class Run:
    """Everything one run recorded, read once. Missing parts (a moved log, a store without an
    object) leave their figures blank rather than stopping the page."""

    def __init__(self, workspace, run):
        self.workspace = Path(workspace).resolve()
        self.verifier = self.workspace / ".verifier"
        self.directory = self.find(run)
        self.report = read_json(self.directory / "report-card.json")
        self.state = read_json(self.directory / "run.json")
        self.id = self.report["run_id"]
        self.journal = [read_json(p) for p in sorted((self.directory / "events").glob("*.json"))]
        log = self.report.get("workflow_log") or {}
        candidates = [Path(log["directory"])] if log.get("directory") else []
        candidates.append(self.directory.parents[1] / "attempts" / str(log.get("attempt_id")))
        self.attempt = next((path for path in candidates if (path / "events").is_dir()), None)
        self.costs, self.planner, self.span, self.deadline = {}, None, None, None
        if self.attempt:
            self.read_attempt()
        for path in (self.directory.parents[1] / "subject-runs" / self.id).glob("claim-*/*-response.json"):
            reply = read_json(path)
            self.costs.setdefault(reply.get("session_id"), reply.get("total_cost_usd"))

    def find(self, run):
        path = Path(run)
        if not path.is_dir():
            runs = self.verifier / "runs"
            matches = [p for p in runs.iterdir() if p.is_dir() and p.name.startswith(str(run))] if runs.is_dir() else []
            if len(matches) != 1:
                raise ReportUnavailable(f"No single run matches {run!r} under {runs}.")
            path = matches[0]
        if not (path / "report-card.json").is_file():
            stopped = " It stopped early: see partial-report.md." if (path / "partial-report.json").is_file() else ""
            raise ReportUnavailable(f"{path} has no report card.{stopped}")
        return path

    def read_attempt(self):
        first = last = None
        for path in sorted((self.attempt / "events").glob("[0-9]*.json")):
            item = read_json(path)
            first, last = first or item.get("created_at"), item.get("created_at")
            data = item.get("data") or {}
            if item.get("event") == "process_started" and data.get("role") == "planner":
                self.deadline = data.get("timeout_seconds")
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
            if item.get("event") == "claude_event" and payload.get("type") == "result":
                cost = payload.get("total_cost_usd")
                if data.get("role") == "planner":
                    self.planner = {"cost": cost, "turns": payload.get("num_turns")}
                self.costs[data.get("session_id") or payload.get("session_id")] = cost
        if first and last:
            self.span = (when(last) - when(first)).total_seconds()

    def get(self, ref):
        """A stored object by its digest, or None."""
        if not ref:
            return None
        for path in (self.verifier / "store" / ref, self.verifier / "candidates" / f"{ref}.json",
                     self.directory.parents[1] / "candidates" / f"{ref}.json"):
            if path.is_file():
                return read_json(path)
        return None

    def calls(self, claim_id, tool=None):
        """Journal events for one claim, in order, optionally for one tool."""
        return [event for event in self.journal
                if (event.get("request") or {}).get("arguments", {}).get("claim_id") == claim_id
                and (tool is None or (event.get("request") or {}).get("tool") == tool)]


def claim_view(run, number, claim, notes):
    """Everything one claim's chapter and summary row show."""
    from .local import search_record
    record, audit = claim.get("record") or {}, claim.get("audit") or {}
    critique = audit.get("critique") or {}
    candidate = run.get(record.get("candidate_ref")) or {}
    designed = {case["case_id"]: case for case in candidate.get("cases", [])}
    note = (notes.get("claims") or {}).get(str(number)) or {}
    claim_id = claim["claim"]["claim_id"]
    sessions = set()

    trials = defaultdict(list)
    for test in claim.get("tests") or []:
        trials[test["case_id"]].append(test)
        sessions.add(test.get("session_id"))
        if isinstance(test.get("reading"), dict):
            sessions.add(test["reading"].get("session_id"))
    verdicts = {item["case_id"]: {**item, "answers": (critique.get("task_checks") or {}).get(item["case_id"])}
                for item in critique.get("case_verdicts") or []}
    dropped = {item["case_id"]: item for item in record.get("uncounted_cases") or []}
    probes = {item["case_id"]: item for item in (critique.get("claim_probe") or {}).get("cases", [])}

    rounds = []
    for event in run.calls(claim_id, "select_local_candidate"):
        data = (event.get("result") or {}).get("data") or {}
        judged = (data.get("audit") or {}).get("critique") or {}
        sessions.add(judged.get("session_id"))
        run.costs.setdefault(judged.get("session_id"), judged.get("total_cost_usd"))
        for case in (judged.get("claim_probe") or {}).get("cases", []):
            for sample in case.get("samples", []):
                sessions.add(sample.get("session_id"))
                run.costs.setdefault(sample.get("session_id"), sample.get("total_cost_usd"))
                if isinstance(sample.get("reading"), dict):
                    sessions.add(sample["reading"].get("session_id"))
        outcome = OUTCOMES.get(data.get("outcome"), str(data.get("outcome")))
        if data.get("reason"):
            outcome += ": " + REFUSALS.get(data["reason"], data["reason"])
        rounds.append({"proposed": event["request"]["arguments"].get("target_grade"),
                       "reviewer": judged.get("supported_grade"), "outcome": outcome,
                       "not_counted": sum(v.get("verdict") != "counts" for v in judged.get("case_verdicts") or []),
                       # A critique from before coverage gaps were listed has no count to show.
                       "untested": len(judged["coverage_gaps"]) if "coverage_gaps" in judged else None})
    for part in (claim.get("documentary_assessment"), (claim.get("fallback") or {}).get("assessment")):
        if isinstance(part, dict):
            sessions.add(part.get("session_id"))
            run.costs.setdefault(part.get("session_id"), part.get("total_cost_usd"))
    sessions.discard(None)

    stamps = [when(event["created_at"]) for event in run.calls(claim_id)]
    looked = search_record(SimpleNamespace(directory=run.attempt), claim_id)["this_claim"] if run.attempt else None

    tests = []
    for index, (case_id, rows) in enumerate(trials.items(), 1):
        case = designed.get(case_id, {})
        if candidate.get("method") == "task":
            tests.append(task_view(index, case_id, rows, case, verdicts.get(case_id, {}), dropped.get(case_id),
                                   (note.get("tests") or {}).get(case_id) or {}, claim.get("references") or {}))
            continue
        method = case.get("method") if candidate.get("method") == "mixed" else candidate.get("method")
        verdict = verdicts.get(case_id, {})
        counted = any(row.get("counted") for row in rows)
        reason = dropped.get(case_id) or (verdict if verdict.get("verdict") not in (None, "counts") else {})
        probe = probes.get(case_id, {})
        written = (note.get("tests") or {}).get(case_id) or {}
        tests.append({
            "number": index, "case_id": case_id, "method": method, "options": case.get("options") or [],
            "asks": written.get("asks"), "review": written.get("review"),
            "question": rows[0].get("input", ""), "expected": rows[0].get("expected", ""),
            "unit": case.get("unit"), "why": rows[0].get("applicability") or case.get("applicability"),
            "quote": rows[0].get("reference_quote"),
            "reference": (claim.get("references") or {}).get(rows[0].get("reference_ref")) or {},
            "calculated": rows[0].get("calculated"), "trials": rows, "counted": counted,
            "not_counted": NOT_COUNTED.get(reason.get("verdict"), reason.get("verdict")) if not counted else None,
            "verdict": verdict, "dropped": dropped.get(case_id),
            "probe": [sample.get("answer") for sample in probe.get("samples", [])],
            "probe_reached": probe.get("outcome") == "reached" if probe else None,
            "passed": sum(row.get("comparison_status") == "pass" for row in rows),
            "by_reader": sum(row.get("comparison_status") == "pass" and row.get("python_status") != "pass"
                             for row in rows)})

    accuracy, consistency = record.get("accuracy"), record.get("consistency")
    counted_trials = [row for test in tests if test["counted"] for row in test["trials"]]
    generator = candidate.get("generator") if candidate.get("method") == "task" else None
    return {
        "tasks": candidate.get("method") == "task",
        "design": {"generator": generator, "solver": candidate.get("solver"),
                   "model_url": ((claim.get("references") or {}).get((generator or {}).get("reference_ref")) or {}).get("url")}
        if candidate.get("method") == "task" else None,
        "run_problems": sorted({item for test in tests for row in test["trials"] for item in row.get("run_problems") or []}),
        "number": number, "id": claim_id, "claim": claim["claim"], "note": note, "record": record,
        "title": note.get("title") or (claim.get("sections") or [f"Claim {number}"])[0],
        "sections": claim.get("sections") or [], "grade": record.get("evidence_grade"),
        "status": record.get("scientific_status"), "withheld": record.get("status_withheld_reason"),
        "accuracy": accuracy if isinstance(accuracy, dict) else None,
        "consistency": consistency if isinstance(consistency, dict) else None,
        "tests": tests, "tests_counted": sum(test["counted"] for test in tests),
        "trials_run": sum(len(test["trials"]) for test in tests), "trials_counted": len(counted_trials),
        "by_reader": sum(row.get("comparison_status") == "pass" and row.get("python_status") != "pass"
                         for row in counted_trials),
        "rounds": rounds, "looked": looked,
        "untested": critique.get("coverage_gaps"), "findings": critique.get("findings") or [],
        "departures": critique.get("departures") or [],
        "seconds": (max(stamps) - min(stamps)).total_seconds() if len(stamps) > 1 else None,
        "cost": sum(run.costs.get(s) or 0 for s in sessions) if sessions else None,
        "references": claim.get("references") or {}, "limitations": record.get("limitations") or [],
        "documentary": claim.get("documentary_assessment"), "fault": record.get("fault")}


def task_view(index, case_id, rows, case, verdict, dropped, written, references):
    """One task of a task design, as its table row and fold show it ("Tasks" in local-tasks.md)."""
    counted = any(row.get("counted") for row in rows)
    reason = dropped or (verdict if verdict.get("verdict") not in (None, "counts") else {})
    outputs = []
    for output in case.get("outputs") or []:
        source = references.get(output.get("reference_ref")) or {}
        outputs.append({**output, "url": source.get("url"), "version": source.get("version")})
    gaps = [float(item["off_reference"]) for row in rows for item in row.get("outputs") or []
            if item.get("off_reference") is not None]
    return {"kind": "task", "number": index, "case_id": case_id, "method": "task", "options": [],
            "criterion_given": verdict.get("criterion_given") or "", "off_reference": max(gaps) if gaps else None,
            "asks": written.get("asks"), "review": written.get("review"), "question": rows[0].get("input", ""),
            "expected": rows[0].get("expected") or {}, "outputs": outputs, "files": rows[0].get("files") or [],
            "sections": rows[0].get("sections") or [], "planted": case.get("planted"),
            "solver_results": case.get("solver_results"), "why": rows[0].get("applicability"),
            "trials": rows, "counted": counted,
            "not_counted": NOT_COUNTED.get(reason.get("verdict"), reason.get("verdict")) if not counted else None,
            "verdict": verdict, "dropped": dropped, "probe": [], "probe_reached": None, "unit": None,
            "quote": None, "reference": {}, "calculated": None,
            "passed": sum(row.get("comparison_status") == "pass" for row in rows), "by_reader": 0}


def shown(output, value):
    """An expected or found value as a reader reads it: a number bare, anything else as JSON."""
    if output.get("type") == "number" and isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def tolerance_text(output):
    parts = []
    if output.get("relative_tolerance"):
        parts.append("±" + str(round(float(output["relative_tolerance"]) * 100, 4)).rstrip("0").rstrip(".") + "%")
    if output.get("absolute_tolerance"):
        parts.append("±" + output["absolute_tolerance"])
    return " or ".join(parts) if parts else ("exact" if output.get("type") == "number" else "")


def misses(row):
    """What one try got wrong: each output that did not pass, or why no results were read."""
    wrong = [item["field"] + (": " + json.dumps(item["found"], ensure_ascii=False) if item.get("present") else ": missing")
             for item in row.get("outputs") or [] if item.get("status") != "pass"]
    return "; ".join(wrong) or row.get("results_problem") or ""


def views(run, notes):
    return [claim_view(run, i, claim, notes) for i, claim in enumerate(run.report["claims"], 1)]


# ---------------------------------------------------------------- drawing the page

CSS = """
:root{--navy:#14243d;--navy2:#1e3556;--ink:#22303f;--muted:#4a6280;--soft:#64748b;--line:#d3dce6;
--card:#edf1f6;--card2:#f6f8fb;--teal:#0f8a7e;--teal-dark:#0b6f65;--teal-tint:#e6f4f1;--blue:#2f6da3;
--amber:#b77410;--amber-tint:#fdf3e1;--red:#a32c21;--red-tint:#fbecea;--gray:#7a8699}
*{box-sizing:border-box}
body{margin:0;background:#eef2f6;color:var(--ink);font:16px/1.55 "Segoe UI",Calibri,Arial,sans-serif}
.page{max-width:1320px;margin:0 auto;padding:28px 22px 64px}
h1,h2,h3{font-family:Cambria,Georgia,serif;color:var(--navy);line-height:1.2;margin:0 0 .5em}
h1{font-size:34px;color:#fff}h2{font-size:27px}h3{font-size:19px;margin-top:1.2em}
a{color:var(--teal-dark)}
.hero{background:var(--navy);color:#cadcfc;border-radius:16px;padding:30px 32px}
.kicker{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#7ed6cb}
.hero p{margin:.3em 0 0;font-size:17px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin-top:22px}
.tile{background:var(--navy2);border-radius:12px;padding:14px 16px}
.tile b{display:block;font:700 24px Cambria,Georgia,serif;color:#fff;margin-bottom:2px}
.tile .badge{width:24px;height:24px;font-size:15px;margin:0 3px 3px 0}
.tile span{font-size:14px}
nav{margin-top:20px;display:flex;flex-wrap:wrap;gap:8px}
nav a{background:#24406a;color:#fff;text-decoration:none;border-radius:999px;padding:5px 13px;font-size:14px}
section{background:#fff;border-radius:14px;padding:26px 28px;margin-top:22px;box-shadow:0 1px 3px rgba(20,36,61,.08)}
.lead{font-size:17px;max-width:62em}
.written{background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin:12px 0}
.written p{margin:.25em 0}
.by{font-size:12.5px;color:var(--soft);font-weight:600;letter-spacing:.02em}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.stats{display:flex;flex-wrap:wrap;gap:8px 18px;margin:10px 0 4px;color:var(--muted);font-size:15px}
.stats b{color:var(--ink)}
.wrap{overflow-x:auto;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14.5px}
table.glance{font-size:14px}
table.glance td,table.glance th{padding:8px 8px}table.glance td{white-space:nowrap}
table.glance td:first-child{white-space:normal;min-width:11em}
th{background:var(--navy);color:#fff;text-align:left;font-weight:600;padding:9px 10px;vertical-align:bottom}
td{padding:9px 10px;border-bottom:1px solid #e3e9f0;vertical-align:top}
tbody tr:nth-child(even) td{background:var(--card2)}
td.n,th.n{text-align:right;white-space:nowrap}
tr.total td{font-weight:700;background:var(--card)!important}
.badge{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:7px;
color:#fff;font:700 18px Cambria,Georgia,serif;vertical-align:middle}
.g-A{background:var(--teal)}.g-B{background:var(--blue)}.g-C{background:var(--amber)}.g-D,.g-none{background:var(--gray)}.g-U{background:var(--red)}
.chip{display:inline-block;border-radius:999px;padding:1px 10px;font-size:13.5px;font-weight:700;white-space:nowrap}
.s-pass{background:var(--teal-tint);color:var(--teal-dark)}.s-fail{background:var(--red-tint);color:var(--red)}
.s-inconclusive,.s-none{background:var(--amber-tint);color:var(--amber)}
.ans{display:inline-block;max-width:15em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
border-radius:6px;padding:0 7px;margin:1px 2px 1px 0;font-size:13.5px;vertical-align:middle}
.ok{background:var(--teal-tint);color:var(--teal-dark)}.bad{background:var(--red-tint);color:var(--red)}
.dim{color:var(--soft);font-size:13px}
.id{font-family:Consolas,"Courier New",monospace;font-size:12.5px;color:var(--soft)}
tr.review td{background:var(--amber-tint)!important;border-bottom:1px solid #f0dcb6}
.flag{font-weight:700;color:var(--amber)}
.pending{background:var(--amber-tint);border-radius:12px;padding:12px 16px;margin:12px 0}
details{border:1px solid var(--line);border-radius:12px;margin:14px 0;background:#fff}
details>summary{cursor:pointer;padding:12px 16px;font-weight:700;color:var(--navy);list-style-position:inside}
details[open]>summary{border-bottom:1px solid var(--line)}
details .inner{padding:6px 18px 16px}
details details{margin:10px 0;border-radius:10px}
details details>summary{font-weight:600;font-size:15px;padding:9px 14px}
dl{display:grid;grid-template-columns:11em 1fr;gap:6px 14px;margin:10px 0}
dt{color:var(--muted);font-weight:600}dd{margin:0}
pre{white-space:pre-wrap;word-wrap:break-word;background:var(--card2);border:1px solid #e3e9f0;border-radius:8px;
padding:10px 12px;font:13px/1.45 Consolas,"Courier New",monospace;max-height:22em;overflow:auto;margin:6px 0}
.question{white-space:pre-wrap;background:var(--card2);border:1px solid #e3e9f0;border-radius:8px;padding:10px 12px}
blockquote{margin:6px 0;padding:8px 14px;background:var(--teal-tint);border-radius:8px;color:var(--ink)}
.try{border-top:1px dashed var(--line);padding-top:8px;margin-top:8px}
ul.plain{margin:.4em 0;padding-left:1.2em}ul.plain li{margin:.3em 0}
.legend dt{color:var(--navy)}
footer{color:var(--soft);font-size:13px;margin-top:26px;text-align:center}
@media (max-width:760px){.two{grid-template-columns:1fr}dl{grid-template-columns:1fr}}
"""


def e(value):
    return escape(str(value if value is not None else ""), quote=True)


def badge(grade):
    return f'<span class="badge g-{e(grade or "none")}" title="Evidence grade">{e(grade or "–")}</span>'


def chip(status, withheld=None):
    title = f' title="{e(withheld)}"' if withheld else ""
    return f'<span class="chip s-{e(status or "none")}"{title}>{e(status or "not decided")}</span>'


def link(url, text=None):
    url = str(url or "")
    if url.startswith(("https://", "http://")):
        return f'<a href="{e(url)}" rel="noreferrer">{e(text or url)}</a>'
    return e(text or url)


def paragraphs(value):
    items = value if isinstance(value, list) else [value] if value else []
    return "".join(f"<p>{e(item)}</p>" for item in items)


def written(heading, body, author):
    return f'<div class="written"><div class="by">{e(heading)} · ✎ written by {e(author)}</div>{body}</div>'


def answer_text(test, text):
    """A reply's answer line, with the option it names for a multiple-choice question."""
    line = first_line(text).strip("*` ")
    if test["method"] == "choice" and line.split(" ")[0].rstrip(".").isdigit():
        index = int(line.split(" ")[0].rstrip("."))
        if 1 <= index <= len(test["options"]):
            return f"{index} · {test['options'][index - 1]}"
    return line


def chips(test, answers, passed):
    """One chip per distinct answer, in order, with its count: '2 ×3' rather than three copies.
    A multiple-choice answer shows only its number when that is the key's."""
    groups = []
    for text, ok in zip(answers, passed):
        line = answer_text(test, text)
        if test["method"] == "choice" and line.split(" · ")[0] == str(test["expected"]).strip():
            line = line.split(" · ")[0]
        for group in groups:
            if group[0] == line and group[1] == ok:
                group[2] += 1
                break
        else:
            groups.append([line, ok, 1])
    return "".join(f'<span class="ans {"ok" if ok else "bad"}" title="{e(line)}">{e(line)}'
                   f'{" ×" + str(count) if count > 1 else ""}</span>' for line, ok, count in groups)


def expected_text(test):
    if test["method"] == "choice" and str(test["expected"]).strip().isdigit():
        index = int(test["expected"])
        if 1 <= index <= len(test["options"]):
            return f"{index} · {test['options'][index - 1]}"
    return str(test["expected"]) + (f" {test['unit']}" if test.get("unit") else "")


def counted_text(test):
    return "yes" if test["counted"] else f'no — {test["not_counted"] or "not counted"}'


def summary_table(claims, run):
    head = [("Claim", ""), ("Grade", "How strong the tests were, A to D"), ("Status", "Did the claim hold?"),
            ("Right", "Counted answers that were right"), ("Agreement", "Did the tries of each test agree?"),
            ("Tests", "Tests that counted, of all tests run"), ("Trials", "Tries that counted, of all tries"),
            ("AI reader", "Answers passed only because the AI reader accepted them"),
            ("Rounds", "Each grading round: the planner's grade, then the reviewer's"),
            ("Search · fetch", "Web searches and pages fetched for this claim"),
            ("Untested", "Parts of the claim the reviewer says no test covered"),
            ("Time", "Time spent on this claim"), ("Cost", "Cost of this claim's AI sessions, planner not included")]
    numeric = {3, 5, 6, 7, 9, 10, 11, 12}
    rows = []
    for v in claims:
        acc = v["accuracy"]
        rows.append([
            f'<a href="#claim-{v["number"]}">{v["number"]} · {e(v["title"])}</a>', badge(v["grade"]),
            chip(v["status"], v["withheld"]),
            f'{acc["matched"]} of {acc["evaluated"]}' if acc else "–",
            e(v["consistency"]["label"]) if v["consistency"] else "–",
            f'{v["tests_counted"]} of {len(v["tests"])}' if v["tests"] else "no tests",
            f'{v["trials_counted"]} of {v["trials_run"]}' if v["tests"] else "–",
            str(v["by_reader"]) if v["tests"] else "–",
            e(", ".join(f'{r["proposed"]}→{r["reviewer"] or "–"}' for r in v["rounds"] if r["reviewer"]) or "–"),
            f'{v["looked"]["searches"]} · {v["looked"]["fetches"]}' if v["looked"] else "–",
            str(len(v["untested"])) if v["tests"] and v["untested"] is not None else "–", minutes(v["seconds"]),
            money(v["cost"])])
    matched = sum(v["accuracy"]["matched"] for v in claims if v["accuracy"])
    evaluated = sum(v["accuracy"]["evaluated"] for v in claims if v["accuracy"])
    rows.append(["All claims", "", "", f"{matched} of {evaluated}", "",
                 f'{sum(v["tests_counted"] for v in claims)} of {sum(len(v["tests"]) for v in claims)}',
                 f'{sum(v["trials_counted"] for v in claims)} of {sum(v["trials_run"] for v in claims)}',
                 str(sum(v["by_reader"] for v in claims)), "", "", "",
                 minutes(run.span), money(sum(c or 0 for c in run.costs.values()) if run.costs else None)])
    out = ['<div class="wrap"><table class="glance"><thead><tr>']
    out += [f'<th class="{"n" if i in numeric else ""}" title="{e(tip)}">{e(h)}</th>' for i, (h, tip) in enumerate(head)]
    out.append("</tr></thead><tbody>")
    for r, row in enumerate(rows):
        out.append('<tr class="total">' if r == len(rows) - 1 else "<tr>")
        out += [f'<td class="{"n" if i in numeric else ""}">{cell}</td>' for i, cell in enumerate(row)]
        out.append("</tr>")
    out.append("</tbody></table></div><p class='dim'>Right: counted answers that were right. Tests and trials: "
               "counted, of all run. AI reader: passes that rested on the AI reader. Rounds: the planner's grade → the "
               "reviewer's, for each round. Search · fetch: web searches and pages fetched. Untested: parts of the "
               "claim no test covered. Cost: the claim's own AI sessions; the planner is counted only in the total.</p>")
    return "".join(out)


def task_table(v):
    """One row per task: what it asks, what Python checks, and each try's result."""
    head = ["#", "What the task asks", "Sections", "Checked outputs", "Tries", "Right", "Counted?"]
    out = ['<div class="wrap"><table><thead><tr>'] + [f"<th>{e(h)}</th>" for h in head] + ["</tr></thead><tbody>"]
    for t in v["tests"]:
        checked = "<br>".join(f'{e(o["field"])} = {e(shown(o, o.get("expected")))}'
                              + (f' <span class="dim">{e(tolerance_text(o))}</span>' if tolerance_text(o) else "")
                              for o in t["outputs"])
        tries = "".join(f'<span class="ans {"ok" if row.get("comparison_status") == "pass" else "bad"}" '
                        f'title="{e(misses(row))}">{e(row.get("comparison_status"))}'
                        f'{(": " + e(misses(row))) if misses(row) else ""}</span>' for row in t["trials"])
        given = (f'<div class="dim">The job gives a rule the skill does not: {e(t["criterion_given"])}</div>'
                 if t["criterion_given"] else "")
        near = (f'<div class="dim">On tolerance only: up to {t["off_reference"]:.1%} from the reference '
                f'solution</div>' if t["off_reference"] is not None else "")
        out.append(f'<tr><td class="n">{t["number"]}</td><td>{e(t["asks"] or gist(t["question"]))}'
                   f'<div class="id">{e(t["case_id"])}</div>{given}</td><td>{e(", ".join(t["sections"]))}</td>'
                   f'<td>{checked}</td><td>{tries}</td><td class="n">{t["passed"]} of {len(t["trials"])}{near}</td>'
                   f'<td>{e(counted_text(t)[:1].upper() + counted_text(t)[1:])}</td></tr>')
        if t["review"]:
            out.append(f'<tr class="review"><td></td><td colspan="6"><span class="flag">⚑ Our check:</span> '
                       f'{e(t["review"])}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def task_details(t):
    rows = [("The job", f'<div class="question">{e(t["question"])}</div>')]
    if t["files"]:
        rows.append(("Input files", e(", ".join(f'{item["name"]} ({item["bytes"]:,} bytes)' for item in t["files"]))
                     + '<div class="dim">The same bytes went to every try, read-only.</div>'))
    checked = []
    for o in t["outputs"]:
        where = ("planted by Python's run of the generator" if o.get("source") == "planted"
                 else "quoted from " + link(o.get("url"), o.get("version") or o.get("url")))
        quote = f'<blockquote>{e(o.get("source_quote"))}</blockquote>' if o.get("source_quote") else ""
        if o.get("source") == "planted" and o.get("source_quote"):
            where += ", following the rule quoted from " + link(o.get("url"), o.get("version") or o.get("url"))
        checked.append(f'<li><b>{e(o["field"])}</b> = {e(shown(o, o.get("expected")))} '
                       f'<span class="dim">{e(tolerance_text(o))}</span><div class="dim">{where}</div>{quote}</li>')
    rows.append(("What Python checks", "<ul class='plain'>" + "".join(checked) + "</ul>"))
    if t["solver_results"] is not None:
        rows.append(("Reference solution's results", f'<pre>{e(json.dumps(t["solver_results"], ensure_ascii=False, indent=1))}</pre>'))
    if t["why"]:
        rows.append(("Why this task", e(t["why"])))
    if t["verdict"]:
        rows.append(("Reviewer AI said", f'<b>{e(t["verdict"].get("verdict"))}</b> — {e(t["verdict"].get("reason"))}'))
    answers = t["verdict"].get("answers") if t["verdict"] else None
    if answers:
        rows.append(("Its answers", "<ul class='plain'>" + "".join(
            f'<li>{e(QUESTIONS.get(key, key))} <b>{e(item["answer"])}</b> — {e(item["reason"])}</li>'
            for key, item in answers.items() if isinstance(item, dict)) + "</ul>"))
    if t["criterion_given"]:
        rows.append(("Rule the job gives", e(t["criterion_given"]) + '<div class="dim">The skill\'s sections do not '
                     "give this rule, so the task tests applying it as given.</div>"))
    if t["off_reference"] is not None:
        rows.append(("Passed on tolerance only", f'Up to {t["off_reference"]:.1%} from the reference solution\'s '
                     "result, inside a tolerance meant for honest variation. The skill computed something else."))
    tries = []
    for row in t["trials"]:
        found = "".join(f'<tr><td>{e(item["field"])}</td><td>{e(shown(item, item.get("expected")))}</td>'
                        f'<td>{e(json.dumps(item.get("found"), ensure_ascii=False)) if item.get("present") else "missing"}'
                        + (f'<div class="dim">{float(item["off_reference"]):.1%} from the reference\'s '
                           f'{e(item["reference_result"])}</div>' if item.get("off_reference") is not None else "")
                        + f'</td><td>{chip(item.get("status"))}</td></tr>' for item in row.get("outputs") or [])
        problems = row.get("run_problems") or []
        tries.append(f'<div class="try"><b>Try {e(row.get("trial"))}</b> · {chip(row.get("comparison_status"))}'
                     + (f'<div class="dim">{e(row["results_problem"])}</div>' if row.get("results_problem") else "")
                     + (f'<div class="dim">Run problems: {e("; ".join(problems))}</div>' if problems else "")
                     + (f"<div class='wrap'><table><thead><tr><th>Output</th><th>Expected</th><th>Found</th>"
                        f"<th>Verdict</th></tr></thead><tbody>{found}</tbody></table></div>" if found else "")
                     + f'<pre>{e(row.get("observed"))}</pre></div>')
    body = "".join(f"<dt>{e(k)}</dt><dd>{val}</dd>" for k, val in rows)
    state = "counted" if t["counted"] else "not counted"
    return (f'<details><summary>Task {t["number"]} · {e(t["case_id"])} · right {t["passed"]} of {len(t["trials"])}'
            f' · {state}</summary><div class="inner"><dl>{body}</dl>{"".join(tries)}</div></details>')


def tests_table(v):
    if v["tasks"]:
        return task_table(v)
    head = ["#", "What the test asks", "Answer type", "Expected answer", "Answers (each try)", "Right",
            "Counted?", "Claim-only check"]
    out = ['<div class="wrap"><table><thead><tr>'] + [f"<th>{e(h)}</th>" for h in head] + ["</tr></thead><tbody>"]
    for t in v["tests"]:
        asks = e(t["asks"] or gist(t["question"]))
        answers = chips(t, [row.get("observed") for row in t["trials"]],
                        [row.get("comparison_status") == "pass" for row in t["trials"]])
        right = f'{t["passed"]} of {len(t["trials"])}'
        if t["by_reader"]:
            right += f'<div class="dim">{t["by_reader"]} by AI reader</div>'
        probe = (chips(t, t["probe"], [bool(t["probe_reached"])] * len(t["probe"])) if t["probe"]
                 else '<span class="dim">–</span>')
        out.append(f'<tr><td class="n">{t["number"]}</td><td>{asks}<div class="id">{e(t["case_id"])}</div></td>'
                   f'<td>{e(TYPES.get(t["method"], t["method"] or "–"))}</td><td>{e(expected_text(t))}</td>'
                   f'<td>{answers}</td><td class="n">{right}</td><td>{e(counted_text(t)[:1].upper() + counted_text(t)[1:])}</td>'
                   f'<td>{probe}</td></tr>')
        if t["review"]:
            out.append(f'<tr class="review"><td></td><td colspan="7"><span class="flag">⚑ Our check:</span> '
                       f'{e(t["review"])}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def test_details(t):
    if t.get("kind") == "task":
        return task_details(t)
    rows = [("Full question", f'<div class="question">{e(t["question"])}</div>')]
    rows.append(("Expected answer", e(expected_text(t))))
    if t["calculated"]:
        rows.append(("How the key was made", "Python calculated it with the planner's program, inputs "
                     + e(t["calculated"].get("arguments"))))
    if t["quote"]:
        source = t["reference"]
        rows.append(("Source quote", f'<blockquote>{e(t["quote"])}</blockquote>'
                     + (f'<div class="dim">From {link(source.get("url"), source.get("version") or source.get("url"))}</div>'
                        if source else "")))
    if t["why"]:
        rows.append(("Why this test", e(t["why"])))
    verdict = t["verdict"]
    if verdict:
        rows.append(("Reviewer AI said", f'<b>{e(verdict.get("verdict"))}</b> — {e(verdict.get("reason"))}'))
    if t["dropped"] and t["dropped"].get("reason") and t["dropped"].get("reason") != verdict.get("reason"):
        rows.append(("Why not counted", e(t["dropped"].get("reason"))))
    if t["probe"]:
        rows.append(("Claim-only answers", e(" · ".join(answer_text(t, a) for a in t["probe"]))
                     + (" (reached the key)" if t["probe_reached"] else " (missed the key)")))
    tries = []
    for row in t["trials"]:
        reading = row.get("reading") if isinstance(row.get("reading"), dict) else {}
        by = "AI reader" if row.get("read_by") == "ai_reader" else "Python"
        line = f'<div class="try"><b>Try {e(row.get("trial"))}</b> · {chip(row.get("comparison_status"))} · read by {by}'
        if reading.get("reason"):
            line += f'<div class="dim">AI reader: {e(reading.get("reading"))} — {e(reading.get("reason"))}</div>'
        tries.append(line + f'<pre>{e(row.get("observed"))}</pre></div>')
    body = "".join(f"<dt>{e(k)}</dt><dd>{val}</dd>" for k, val in rows)
    state = "counted" if t["counted"] else "not counted"
    return (f'<details><summary>Test {t["number"]} · {e(t["case_id"])} · right {t["passed"]} of {len(t["trials"])}'
            f' · {state}</summary><div class="inner"><dl>{body}</dl>{"".join(tries)}</div></details>')


def chapter(v, author):
    note, claim = v["note"], v["claim"]
    out = [f'<section id="claim-{v["number"]}"><div class="kicker">Claim {v["number"]} of the skill</div>',
           f'<h2>{badge(v["grade"])} &nbsp;{e(v["title"])} &nbsp;{chip(v["status"], v["withheld"])}</h2>',
           f'<div class="dim">From the skill\'s section: {e(", ".join(v["sections"]) or "–")}</div>']
    says = paragraphs(note.get("says")) if note.get("says") else ""
    summary = paragraphs(note.get("summary")) if note.get("summary") else ""
    if says or summary:
        out.append('<div class="two">' + (written("What the claim says", says, author) if says else "")
                   + (written("Our summary", summary, author) if summary else "") + "</div>")
    else:
        # The planner's statement lists every fact the claim states and is written to be tested,
        # not read; until a plain summary is written, its scope line stands in and the rest folds away.
        scope = re.split(r"(?<=\.)\s", str(claim.get("scope") or "").strip())[0]
        out.append('<div class="pending"><b>No plain summary yet.</b> The agent that ran this verification writes one '
                   "into the notes file and updates this page." + (f" The planner's scope: {e(scope)}" if scope else "")
                   + "</div>")
    acc = v["accuracy"]
    stats = [f'<span>Answers right: <b>{acc["matched"]} of {acc["evaluated"]}</b></span>' if acc else "",
             f'<span>Tests counted: <b>{v["tests_counted"]} of {len(v["tests"])}</b></span>' if v["tests"] else "",
             f'<span>Grading rounds: <b>{len([r for r in v["rounds"] if r["reviewer"]])}</b></span>',
             f'<span>Time: <b>{minutes(v["seconds"])}</b></span>', f'<span>Cost: <b>{money(v["cost"])}</b></span>']
    out.append('<div class="stats">' + "".join(stats) + "</div>")
    if v["fault"]:
        out.append(f'<p><span class="flag">⚑ Stopped by a fault:</span> {e(v["fault"])}</p>')
    if v["departures"]:
        out.append('<p><span class="flag">⚑ Held below the proposed grade:</span> the reviewer found where the '
                   "skill's own procedure gives a different result from the reference solution, and no task tests "
                   "it. Its list is under the test details.</p>")
    near = [t["case_id"] for t in v["tests"] if t.get("off_reference") is not None]
    if near:
        out.append('<p><span class="flag">⚑ Passed on tolerance only:</span> ' + e(", ".join(near))
                   + ". The skill's answers were more than 0.5% from the reference solution's, inside a tolerance "
                   "meant for honest variation.</p>")
    if v["run_problems"]:
        out.append('<p><span class="flag">⚑ While running the skill</span>, the test AI met: '
                   + e("; ".join(v["run_problems"])) + ". The skill may not run as shipped on this computer.</p>")
    if v["tests"]:
        out.append(("<h3>The tasks</h3><p class='dim'>Each task gives fresh AI sessions input files and a job. They "
                    "follow the skill and write their results, and Python checks every output.</p>" if v["tasks"]
                    else "<h3>The tests</h3>") + tests_table(v))
    elif v["documentary"]:
        assessment = v["documentary"].get("assessment") or {}
        out.append("<h3>No tests ran</h3><p>An AI assessor read the cited sources instead. Its result: "
                   f'{chip(assessment.get("status"))}</p>')
    more = [f"<details><summary>The full claim, as the planner wrote it</summary><div class='inner'>"
            f"<p>{e(claim.get('statement'))}</p></div></details>"]
    if v["tests"]:
        more.append(("<h3>Each task</h3>" if v["tasks"] else "<h3>Each test</h3>")
                    + "".join(test_details(t) for t in v["tests"]))
    if v["design"]:
        design = v["design"]
        if design["generator"]:
            more.append("<h3>How the input files were made</h3><p>Python ran the planner's generator, which "
                        "implements this model, quoted from " + link(design["model_url"]) + ":</p><blockquote>"
                        + e(design["generator"].get("model_quote")) + "</blockquote>"
                        "<details><summary>The generator's code</summary><div class='inner'><pre>"
                        + e(design["generator"].get("code")) + "</pre></div></details>")
        if design["solver"]:
            more.append("<details><summary>The reference solution's code</summary><div class='inner'><p class='dim'>"
                        "Python ran it on every task before any try; every output passed on its results.</p><pre>"
                        + e(design["solver"].get("code")) + "</pre></div></details>")
    if v["documentary"]:
        assessment = v["documentary"].get("assessment") or {}
        cited = []
        for item in assessment.get("citations") or []:
            source = v["references"].get(item.get("reference_ref")) or {}
            cited.append(f'<li><blockquote>{e(item.get("quote"))}</blockquote>'
                         + (f'<div class="dim">From {link(source.get("url"), source.get("version") or source.get("url"))}'
                            f'</div>' if source else "") + "</li>")
        more.append("<h3>What the assessor cited</h3><ul class='plain'>" + "".join(cited) + "</ul>")
        more.append("<h3>What the assessor found</h3>" + "".join(f"<p>{e(f)}</p>" for f in assessment.get("findings") or []))
    if v["references"]:
        items = "".join(f'<li>{link(ref.get("url"), ref.get("version") or ref.get("url"))}'
                        f'<div class="dim">{e(ref.get("url"))} · licence: {e(ref.get("license"))} · '
                        f'fetched {e(str(ref.get("retrieved_at"))[:10])}</div></li>' for ref in v["references"].values())
        more.append(f"<h3>Where the answer keys came from ({len(v['references'])})</h3><ul class='plain'>{items}</ul>")
    if v["rounds"]:
        rows = "".join(f'<tr><td class="n">{i}</td><td>{e(r["proposed"])}</td><td>{e(r["reviewer"] or "–")}</td>'
                       f'<td>{e(r["outcome"])}</td><td class="n">{r["not_counted"] if r["reviewer"] else "–"}</td>'
                       f'<td class="n">{r["untested"] if r["untested"] is not None else "–"}</td></tr>'
                       for i, r in enumerate(v["rounds"], 1))
        more.append("<h3>Grading rounds</h3><p class='dim'>The planner proposes a grade. A reviewer AI that never saw the "
                    "planning may lower it, and the planner can revise.</p><div class='wrap'><table><thead><tr>"
                    "<th class='n'>Round</th><th>Planner proposed</th><th>Reviewer said</th><th>Outcome</th>"
                    "<th class='n'>Tests not counted</th><th class='n'>Left untested</th></tr></thead>"
                    f"<tbody>{rows}</tbody></table></div>")
    if v["untested"]:
        more.append("<h3>What the reviewer says is still untested</h3><ul class='plain'>"
                    + "".join(f"<li>{e(gap)}</li>" for gap in v["untested"]) + "</ul>")
    if v["departures"]:
        more.append("<h3>Where the skill departs from the reference, untested</h3><ul class='plain'>"
                    + "".join(f"<li>{e(item)}</li>" for item in v["departures"]) + "</ul>")
    if v["limitations"]:
        more.append("<details><summary>Limits the planner recorded (technical)</summary><div class='inner'>"
                    "<ul class='plain'>" + "".join(f"<li>{e(item)}</li>" for item in v["limitations"])
                    + "</ul></div></details>")
    if v["findings"]:
        more.append("<details><summary>The reviewer AI's full report</summary><div class='inner'>"
                    + "".join(f"<p>{e(f)}</p>" for f in v["findings"]) + "</div></details>")
    out.append('<details class="more"><summary>Test details and sources</summary><div class="inner">'
               + "".join(more) + "</div></details></section>")
    return "".join(out)


def sections_block(sections, rows):
    """The skill's sections and the claim that tested each; folded when the list is long."""
    if not sections:
        return ""
    tested = sum(bool(s.get("claims")) for s in sections)
    table = (f"<div class='wrap'><table><thead><tr><th>Section of the skill</th><th>Tested by</th></tr></thead>"
             f"<tbody>{rows}</tbody></table></div>")
    if len(sections) <= 10:
        return f"<h3>Its sections, and which claim tested each</h3>{table}"
    return (f"<details><summary>Its {len(sections)} sections, and which claim tested each ({tested} tested)"
            f"</summary><div class='inner'>{table}</div></details>")


def page(run, notes):
    report, state = run.report, run.state
    author = notes.get("by") or "Claude"
    claims = views(run, notes)
    skill = notes.get("skill") or {}
    name = Path(str(state.get("source_path") or "")).name or "skill"
    statuses = {}
    for word in ("pass", "fail", "inconclusive", None):
        count = sum(v["status"] == word for v in claims)
        if count:
            statuses[word or "not decided"] = count
    matched = sum(v["accuracy"]["matched"] for v in claims if v["accuracy"])
    evaluated = sum(v["accuracy"]["evaluated"] for v in claims if v["accuracy"])
    settings = run.get(state.get("local_settings_ref")) or {}
    total = sum(c or 0 for c in run.costs.values()) if run.costs else None
    tiles = [(" ".join(badge(v["grade"]) for v in claims), f"{len(claims)} claims"),
             (" · ".join(f"{n} {s}" for s, n in statuses.items()), "status of the claims"),
             (f"{matched} of {evaluated}", "counted answers right"),
             (minutes(run.span), f"run time, of {minutes(run.deadline)} allowed" if run.deadline else "run time"),
             (f'{state.get("subject_calls_used", "–")} of {settings.get("max_subject_calls", "–")}', "AI test sessions"),
             (money(total), "cost at API prices" + (f", planner {money(run.planner['cost'])}" if run.planner else ""))]
    nav = ['<a href="#skill">The skill</a>', '<a href="#glance">Results at a glance</a>']
    nav += [f'<a href="#claim-{v["number"]}">Claim {v["number"]}</a>' for v in claims]
    nav += ['<a href="#cautions">Cautions</a>', '<a href="#how">How to read this</a>']
    created = str(state.get("created_at") or report.get("generated_at") or "")[:10]
    out = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
           "<meta name='viewport' content='width=device-width,initial-scale=1'>",
           f"<title>{e(name)} · verification report {e(run.id[:8])}</title><style>{CSS}</style></head><body>"
           "<div class='page'>",
           f'<div class="hero"><div class="kicker">Skill verification report · run {e(run.id[:8])} · {e(created)}</div>'
           f'<h1>{e(skill.get("name") or name)}</h1>'
           f'<p>Skill folder: {e(name)} · tested with {e((report.get("subject") or {}).get("model_id"))} · '
           f'verifier code {e(str(state.get("local_method_ref") or "")[:8])}</p>'
           '<div class="tiles">' + "".join(f"<div class='tile'><b>{big}</b><span>{e(small)}</span></div>"
                                           for big, small in tiles) + "</div>"
           "<nav>" + "".join(nav) + "</nav></div>"]

    sections = ((report.get("coverage") or {}).get("sections")) or []
    numbers = {v["id"]: v["number"] for v in claims}
    section_rows = "".join(
        f'<tr><td>{"&nbsp;" * 4 * max(0, (s.get("level") or 1) - 1)}{e(s.get("heading"))}</td><td>'
        + (", ".join(f'<a href="#claim-{numbers[c]}">Claim {numbers[c]}</a>' for c in s.get("claims") or [] if c in numbers)
           or (f'<span class="dim">set aside: {e(s["set_aside"])}</span>' if s.get("set_aside")
               else '<span class="dim">not tested</span>')) + "</td></tr>" for s in sections)
    body = paragraphs(skill.get("summary")) if skill.get("summary") else ""
    out.append('<section id="skill"><h2>The skill in plain words</h2>'
               + (written("About the skill", body, author) if body else
                  '<div class="pending"><b>No plain summary yet.</b> The agent that ran this verification writes one '
                  "into the notes file and updates this page.</div>")
               + sections_block(sections, section_rows) + "</section>")

    out.append('<section id="glance"><h2>Results at a glance</h2><p class="lead">One row per claim. A claim passes only if '
               'every counted answer is right. The grade says how strong the tests were, not whether the skill passed.'
               '</p>' + summary_table(claims, run) + "</section>")
    out += [chapter(v, author) for v in claims]

    cautions = notes.get("cautions") or []
    recorded = []
    untested = [s.get("heading") for s in sections if not s.get("claims") and not s.get("set_aside")]
    if untested:
        recorded.append(f"{len(untested)} of {len(sections)} sections of the skill had no claim: " + "; ".join(untested) + ".")
    aside = [s for s in sections if s.get("set_aside")]
    if aside:
        recorded.append(f"{len(aside)} of {len(sections)} sections were set aside as having nothing to test: "
                        + "; ".join(f'{s.get("heading")} ({s["set_aside"]})' for s in aside) + ".")
    problems = sorted({item for v in claims for item in v["run_problems"]})
    if problems:
        recorded.append("While running the skill, the test AI met: " + "; ".join(problems)
                        + ". A skill that cannot run as shipped is a finding about the skill.")
    environment = report.get("environment") or {}
    if environment.get("imports_unavailable_reported_by_image"):
        recorded.append("The test computer did not have these Python packages: "
                        + ", ".join(environment["imports_unavailable_reported_by_image"]) + ".")
    readers = sum(v["by_reader"] for v in claims)
    recorded.append("A reviewer AI checked every test plan, so every grade includes AI judgment."
                    + (f" {readers} counted answer{'s' if readers > 1 else ''} passed only because the AI reader "
                       f"accepted {'them' if readers > 1 else 'it'}." if readers else ""))
    recorded += [HOST.get(item, item) for item in report.get("host_limitations") or []]
    out.append('<section id="cautions"><h2>Cautions and limitations</h2>'
               + (written("Cautions from our review", "<ul class='plain'>" + "".join(f"<li>{e(c)}</li>" for c in cautions)
                          + "</ul>", author) if cautions else "")
               + "<h3>From the run's records</h3><ul class='plain'>" + "".join(f"<li>{e(r)}</li>" for r in recorded)
               + "</ul></section>")

    tasks = any(v["tasks"] for v in claims)
    out.append('<section id="how"><h2>How to read this report</h2><dl class="legend">'
               + ("<dt>Claim</dt><dd>A part of the skill that serves one purpose: a group of its sections. Together the "
                  "claims hold every section, except those set aside as having nothing to test.</dd>"
                  "<dt>Task</dt><dd>Input files and a job, as a user of the skill would give. Fresh AI sessions do it 3 "
                  "times while using the skill and write their results. Python checks each output against a value it "
                  "built into the files, or one taken from an outside source, never from the skill.</dd>"
                  if tasks else
                  "<dt>Claim</dt><dd>One thing the skill says it does. Each claim comes from one section of the skill.</dd>"
                  "<dt>Test</dt><dd>A question with an answer key taken from an outside source, not from the skill. "
                  "Fresh AI sessions answer it 3 times while using the skill.</dd>") +
               "<dt>Grade A–D</dt><dd>How strong the tests and their answer keys are. A is the strongest. It is set "
               "before the tests run, and it is not an approval of the skill.</dd>"
               "<dt>Status</dt><dd>pass: every counted answer was right. fail: at least one was wrong. "
               "inconclusive: the evidence could not decide.</dd>"
               "<dt>Counted</dt><dd>Only tests the reviewer AI accepted count toward the status. The others still "
               "ran and are shown.</dd>"
               + ("" if tasks else
                  "<dt>Claim-only check</dt><dd>Two fresh AI sessions answer each test from the claim alone, without the "
                  "skill. If they miss the key, the claim does not settle the test, so it cannot count.</dd>"
                  "<dt>AI reader</dt><dd>When Python's strict check marks an answer wrong, a second AI reads it again and "
                  "can accept a right answer written another way.</dd>") +
               "<dt>✎ text</dt><dd>" + e(notes.get("author") or "Written after the run") + ", to explain the "
               "results. It is not part of the scored record.</dd></dl></section>")
    out.append(f"<footer>Made from the records of run {e(run.id)}. Report card: "
               f"{e(run.directory / 'report-card.json')}</footer></div></body></html>")
    return "".join(out)


# ---------------------------------------------------------------- notes and publishing

def skeleton(run):
    """The notes file the agent fills in: empty plain-language fields beside what they describe."""
    claims = {}
    for v in views(run, {}):
        acc = v["accuracy"]
        result = [v["grade"] or "no grade", v["status"] or "not decided"]
        if acc:
            result.append(f'{acc["matched"]} of {acc["evaluated"]} counted answers right')
        claims[str(v["number"])] = {
            "section": ", ".join(v["sections"]), "claim_as_written": v["claim"].get("statement"),
            "result": " · ".join(result), "left_untested": v["untested"],
            "title": "", "says": [], "summary": [],
            "tests": {t["case_id"]: {
                "question": t["question"],
                "expected": ({o["field"]: shown(o, o.get("expected")) for o in t["outputs"]} if t.get("kind") == "task"
                             else expected_text(t)),
                "answers": [(row.get("comparison_status") or "") + (": " + misses(row) if misses(row) else "")
                            if t.get("kind") == "task" else answer_text(t, row.get("observed")) for row in t["trials"]],
                "right": f'{t["passed"]} of {len(t["trials"])}', "counted": counted_text(t),
                "asks": "", "review": ""} for t in v["tests"]}}
    sections = [s.get("heading") for s in ((run.report.get("coverage") or {}).get("sections")) or []]
    return {"guide": GUIDE, "by": "", "author": "",
            "skill": {"folder": Path(str(run.state.get("source_path") or "")).name, "sections": sections,
                      "name": "", "summary": []},
            "claims": claims, "cautions": []}


def render(workspace, run_id, notes_path=None, out=None):
    """Write the page from the run's records and its notes, if any; return the page's path."""
    run = Run(workspace, run_id)
    reports = run.verifier / "reports"
    notes_path = Path(notes_path) if notes_path else reports / f"{run.id}.notes.json"
    notes = read_json(notes_path) if notes_path.is_file() else {}
    out = Path(out) if out else reports / f"{run.id}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_text(out, page(run, notes))
    return out


def publish(workspace, run_id):
    """After a run: the page, an unfilled notes file beside it, and how to finish both.

    Existing notes are kept, so publishing again never erases a written summary.
    """
    run = Run(workspace, run_id)
    reports = run.verifier / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    notes = reports / f"{run.id}.notes.json"
    if not notes.is_file():
        write_text(notes, json.dumps(skeleton(run), ensure_ascii=False, indent=2) + "\n")
    page_path = render(workspace, run.id)
    command = f'"{sys.executable}" "{SCRIPT}" {run.id} --workspace "{Path(workspace).resolve()}"'
    return {"path": str(page_path), "notes_path": str(notes), "render_command": command,
            "next_step": "Unless the user asked for no HTML report: open notes_path, fill its empty fields as its "
                         "guide says, in plain short sentences that do not quote the skill, then run "
                         "render_command and give the user the page at path."}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Write a finished run's HTML page from its records and notes.")
    parser.add_argument("run", help="run ID, a unique prefix of one, or a run directory")
    parser.add_argument("--workspace", default=str(SCRIPT.parents[1]))
    parser.add_argument("--notes", help="notes file; default .verifier/reports/<run ID>.notes.json")
    parser.add_argument("--out", help="page to write; default .verifier/reports/<run ID>.html")
    args = parser.parse_args(argv)
    try:
        print(render(args.workspace, args.run, args.notes, args.out))
    except ReportUnavailable as error:
        raise SystemExit(str(error)) from None
