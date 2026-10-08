"""Internal local-profile operations; Claude Code chooses and calls legal steps."""

from html import escape
import base64
import json
import re

from .common import Fault, canonical, digest, normalize, utc_now
from .ingest import verified_snapshot
from .storage import atomic_write, no_links
from . import local_candidates as catalog

CLAIM_LEGAL = {
    "local_lookup": ["list_local_candidates", "record_local_limitation"],
    "local_discovery": ["fetch_local_reference", "load_local_resource", "fetch_local_asset", "qualify_local_tasks", "select_local_candidate", "assess_local_documentary", "record_local_unverified", "record_local_limitation"],
    # An audited executable plan is not abandoned by assertion. Every real failure
    # during execution is recorded by Python with the cause it observed.
    "local_ready": ["execute_local_claim"],
    "local_documentary":["fetch_local_reference","load_local_resource","fetch_local_asset","assess_local_documentary","record_local_unverified","record_local_limitation"],
    "terminal_result": [], "terminal_operational": [],
}
# "Claims" in local-tasks.md owns the claim limit and the grouping rule the planner's manifest
# tool states; the earlier profiles keep their atomic claims and their own limit. Twelve claims of
# three tasks and three trials use 108 of the default 128 subject calls.
MAX_CLAIMS = 12
CLAIM_MANIFEST_DESCRIPTION = (
    "In source_ready only: commit claims quoted from delivered snapshot ranges. Each claim is a group of whole "
    "sections of the skill file that serve one purpose, named by the IDs load_submitted_skill returned; every "
    "section goes in exactly one claim or in set_aside with a reason, and a longer skill gets more claims, at most "
    + str(MAX_CLAIMS) + ", as \"Claims\" in local-tasks.md says. Use Not specified for absent scope/behavior; add "
    "no background definitions. An empty list, with every section set aside, is valid. No grading.")
CLAIM_LIMIT_MESSAGE = ("A local manifest holds at most " + str(MAX_CLAIMS) + " claims (\"Claims\" in "
                       "local-tasks.md). Group sections that serve one purpose into one claim.")
OPERATIONS = ("list_local_candidates", "fetch_local_reference", "qualify_local_tasks", "select_local_candidate",
              "execute_local_claim", "record_local_limitation", "load_local_resource", "fetch_local_asset",
              "assess_local_documentary", "record_local_unverified")
# The planner may end a claim operationally only for one of these named causes. Codes
# raised by Python for an observed failure are passed internally and are not in this set,
# so a report can tell an abandoned claim from an execution that actually broke.
PLANNER_LIMITATIONS = (
    "no_independent_reference_available",
    "reference_retrieval_failed",
    "claim_not_mechanically_testable",
    "required_resource_unavailable",
    "required_environment_unavailable",
    "scope_outside_local_support",
)
# The planner's own notes reach the critique whole, so these are also what a critique reads:
# a design's scope and limitations, and each justification of a proposal. Run 26312681's
# critiques read the limitations cut at 800 characters and the coverage note at 2,000.
NOTE_TEXT = 8000
JUSTIFICATION_TEXT = 4000


def legal(state):
    if state["run_state"] == "active":
        return sorted({tool for claim in state["claim_states"].values() for tool in CLAIM_LEGAL[claim]})
    return {"created": ["load_submitted_skill"], "source_ready": ["read_snapshot_file", "commit_claim_manifest"],
            "reporting": ["write_report_card"], "completed": [], "incomplete": []}[state["run_state"]]


def schemas(base, obj, string):
    from .local_science import PLANNER_JUSTIFICATION
    from .local_tasks import MAX_OUTPUTS, MAX_TASKS, TYPES as TASK_TYPES

    def choice(values, maximum=100):
        return {"type": "string", "minLength": 1, "maxLength": maximum, "enum": list(values)}

    claim = {**base, "claim_id": string(80)}
    # A task design ("Tasks" in local-tasks.md). Each case is a task; an output gives `planted` or `value`.
    output = obj({"field": string(60), "type": choice(TASK_TYPES, 10), "planted": string(60), "value": string(2000),
                  "relative_tolerance": string(20), "absolute_tolerance": string(20),
                  "reference_ref": string(64), "source_quote": string(8000)}, required=["field", "type"])
    task = obj({"case_id": string(80), "job": string(8000),
                "sections": {"type": "array", "minItems": 1, "maxItems": 40, "items": string(10)},
                "arguments": string(8000),
                "reference_files": {"type": "array", "maxItems": 10,
                                    "items": obj({"name": string(100), "reference_ref": string(64)})},
                "outputs": {"type": "array", "minItems": 1, "maxItems": MAX_OUTPUTS, "items": output},
                "applicability": string(4000)}, required=["case_id", "job", "sections", "outputs", "applicability"])
    return {
        "list_local_candidates": obj(claim),
        "fetch_local_reference": obj({**claim, "url": string(4096), "version": string(200), "license": string(2000)}),
        "load_local_resource":obj({**claim,"resource_name":string(80),"format":string(20)}),
        "fetch_local_asset":obj({**claim,"url":string(4096),"sha256":string(64),"format":string(20),
                                 "version":string(200),"license":string(2000),"units":string(2000)}),
        "assess_local_documentary":obj({**claim,"evidence":{"type":"array","minItems":1,"maxItems":8,
                "items":obj({"reference_ref":string(64),"quote":string(6000)})},"limitations":string(8000)}),
        "record_local_unverified":obj({**claim,"search_account":string(8000),"missing_evidence":string(8000)}),
        "qualify_local_tasks": obj({**claim, "name": string(200), "scope": string(NOTE_TEXT),
            "limitations": string(NOTE_TEXT),
            "generator": obj({"code": string(32000), "reference_ref": string(64), "model_quote": string(8000)}),
            "solver": obj({"code": string(32000)}),
            "cases": {"type": "array", "minItems": 1, "maxItems": MAX_TASKS, "items": task}},
            required=[*claim, "name", "scope", "limitations", "solver", "cases"]),
        "select_local_candidate": obj({**claim, "candidate_ref": string(64), "applicability": string(8000),
            "target_grade": choice(("A", "B", "C"), 1),
            **{key: string(JUSTIFICATION_TEXT) for key in PLANNER_JUSTIFICATION}}),
        "execute_local_claim": obj(claim),
        "record_local_limitation": obj({**claim, "code": choice(PLANNER_LIMITATIONS), "reason": string(8000)}),
    }


def keep(store, state, value):
    catalog.safe_payload(value)
    key = store.put_json(value)
    if key not in state["objects"]:
        state["objects"].append(key)
    return key


def retired_candidates(store,state):
    receipts=store.get_json(state["local_catalog_ref"]) if state.get("local_catalog_ref") else []
    return {key for receipt in receipts for key in receipt.get("retired_candidate_refs",[])}


def pin_candidate(store, state, key):
    if key in retired_candidates(store,state):
        raise Fault("candidate_retired","This run's pinned catalog retires the requested candidate; select another method.")
    candidate = store.get_json(key)
    from . import local_tasks
    if candidate.get("status") != "qualified_local" or candidate.get("method_version") != local_tasks.METHOD_VERSION:
        raise Fault("candidate_not_qualified", "Select a mechanically qualified task design.")
    refs = {}
    for ref in catalog.reference_refs(candidate):
        resource = store.get_json(ref)
        store.get(resource["raw_ref"])
        refs[ref] = resource
        for item in (ref, resource["raw_ref"]):
            if item not in state["objects"]:
                state["objects"].append(item)
    # Every trial gets these exact bytes, so they are pinned with the run like its references.
    for case in candidate["cases"]:
        for item in case.get("files") or []:
            store.get(item["object_ref"])
            if item["object_ref"] not in state["objects"]:
                state["objects"].append(item["object_ref"])
    local_tasks.recheck(candidate, refs, store.get)
    if key not in state["objects"]:
        state["objects"].append(key)
    return candidate


# Why the verdict is withheld, per fault. Most faults mean nothing usable came back at
# all; a changed subject model is different, because observations did arrive and are
# simply not attributable to one subject.
#
# A truncated trial set reports no measurement: the observations that completed before
# the fault are discarded rather than salvaged into a partial accuracy. Decided
# 2026-09-21, not pending. A prefix of a plan is not the plan the critique reviewed, and
# the surviving cases are whichever ones happened to run before the failure, so a figure
# computed from them describes an arbitrary subset while looking like a measurement. The
# raw observations stay in the receipts for anyone who wants them; they are simply not
# promoted to an axis. Do not add partial-accuracy reporting here without revisiting that.
WITHHELD_FOR_FAULT = {"subject_model_changed": "unattributable_observations"}


def limitation(store, state, claim_id, code, reason, receipts=None, *, asserted_by="runtime"):
    work = state["local_work"].setdefault(claim_id, {})
    previous=[]
    if work.get("result_ref"):
        work["comparison_ref"]=work.pop("result_ref")
        previous=store.get_json(work["comparison_ref"]).get("receipts",[])
    # A fault is the runner's, never the skill's, so it is named in its own field and
    # never becomes a grade or a verdict. The behavioural axes read `not_obtained`
    # rather than `not_applicable`: execution was attempted and returned nothing usable,
    # which is a different statement from a path that never measures behaviour at all.
    record = {"kind": "local-limitation", "claim_id": claim_id, "code": code, "reason": reason,
              "asserted_by": asserted_by, "scientific_status": None, "evidence_grade": None,
              "status_withheld_reason": WITHHELD_FOR_FAULT.get(code, "not_executed"), "fault": code,
              "accuracy": "not_obtained", "consistency": "not_obtained",
              "receipts":list(dict.fromkeys([*previous,*(receipts or [])]))}
    work["outcome_ref"] = keep(store, state, record)
    state["claim_states"][claim_id] = "terminal_operational"
    return {"outcome": code, "limitation": record}


def reply_reference(reference):
    """A pinned reference as the planner may receive it: text past the reply limit is cut.

    Quotes are checked against the pinned record, never against this copy.
    """
    shown, total = catalog.reply_text(reference.get("text") or "")
    if total is None:
        return reference
    return {**reference, "text": shown, "text_truncated": True, "text_bytes_total": total}


def operate(store, state, name, args, subject):
    if name == "write_report_card":
        if subject is not None:
            retry_stopped_claims(store, state, subject)
            fallback_documentary(store, state, subject)
        return report(store, state)
    claim_id = args["claim_id"]
    if name not in CLAIM_LEGAL.get(state["claim_states"].get(claim_id), []):
        raise Fault("illegal_claim_transition", "This operation is not legal for this local claim.")
    work = state["local_work"].setdefault(claim_id, {"reference_refs": [], "candidate_refs": []})
    if name == "record_local_limitation":
        return limitation(store, state, claim_id, args["code"], args["reason"], asserted_by="planner")
    if name in {"assess_local_documentary","record_local_unverified"}:
        return documentary_step(store,state,claim_id,name,args,subject)
    if name == "list_local_candidates":
        retired=retired_candidates(store,state)
        found = [item for item in catalog.candidates(store) if item["candidate_ref"] not in retired]
        work["lookup_ref"] = keep(store, state, {"candidates": found, "created_at": utc_now()})
        state["claim_states"][claim_id] = "local_discovery"
        return {"outcome": "local_candidates_returned" if found else "discovery_required", "candidates": found}
    if name == "fetch_local_reference":
        check_reference_host(settings_for(store,state),args["url"])
        raw, text = catalog.fetch_public(args["url"])
        raw_ref = store.put(raw)
        state["objects"].append(raw_ref)
        reference = {"kind": "local-reference", "url": args["url"], "raw_ref": raw_ref, "text": text,
                     "version": args["version"], "license": args["license"], "retrieved_at": utc_now(),
                     "origin": "retrieved_public_https",
                     "authority": "not_independently_attested", "redistribution": "not_authorized"}
        key = keep(store, state, reference)
        work["reference_refs"].append(key)
        return {"outcome": "reference_fetched", "reference_ref": key, "untrusted_reference": reply_reference(reference)}
    if name in {"load_local_resource","fetch_local_asset"}:
        from .local_resources import inspect_resource,import_configured
        settings=settings_for(store,state)
        if name=="load_local_resource":
            raw,metadata=import_configured(settings,args["resource_name"])
            # An operator-selected local dataset is pinned but was not retrieved by Python,
            # so it supports external validation rather than direct validation.
            metadata={**{key:value for key,value in metadata.items() if key!="path"},
                      "url":"operator-resource:"+args["resource_name"],"origin":"operator_local_resource"}
        else:
            check_reference_host(settings,args["url"])
            raw,_=catalog.fetch_bytes(args["url"],max_bytes=settings["max_file_bytes"])
            if digest(raw)!=args["sha256"]:
                raise Fault("resource_changed","Downloaded asset differs from the requested digest.")
            metadata={**{key:args[key] for key in ("url","version","license","units")},
                      "origin":"retrieved_public_https"}
        inspection=inspect_resource(raw,args["format"],settings)
        raw_ref=store.put(raw)
        if raw_ref not in state["objects"]:
            state["objects"].append(raw_ref)
        reference={"kind":"local-reference",**metadata,**inspection,"text":inspection.get("text",""),
                   "raw_ref":raw_ref,"retrieved_at":utc_now(),"authority":"not_independently_attested","redistribution":"not_authorized"}
        key=keep(store,state,reference)
        work["reference_refs"].append(key)
        return {"outcome":"reference_fetched","reference_ref":key,"untrusted_reference":reply_reference(reference)}
    if name == "qualify_local_tasks":
        from . import local_tasks
        settings = settings_for(store, state)
        runner = local_tasks.SandboxRunner(settings, log=getattr(subject, "log", None),
                                           solver_image=getattr(subject, "subject_image", None))
        refs = {key: store.get_json(key) for key in work["reference_refs"]}
        proposal = {key: args[key] for key in ("name", "scope", "limitations", "generator", "solver", "cases")
                    if key in args}
        candidate, made = local_tasks.qualify(proposal, refs, claim_sections(store, state, claim_id), runner, store.get)
        for data in made.values():
            object_ref = store.put(data)
            if object_ref not in state["objects"]:
                state["objects"].append(object_ref)
        key = keep(store, state, candidate)
        catalog.save_candidate(store, candidate)
        work["candidate_refs"].append(key)
        return {"outcome": candidate["status"], "candidate_ref": key,
                "candidate": local_tasks.reply_view(candidate, store.get)}
    if name == "select_local_candidate":
        return select(store, state, claim_id, work, args, subject)
    return execute(store, state, claim_id, subject)


def claim_record(store, state, claim_id):
    return next(item for item in store.get_json(state["manifest_ref"])["claims"]
                if item["claim_id"] == claim_id)


def claim_sections(store, state, claim_id):
    """The section IDs a claim holds ("Claims" in local-tasks.md); none for a manifest without them."""
    return list(claim_record(store, state, claim_id).get("sections") or [])


def prior_objections(history):
    """Earlier reviewers' concerns, without their grades, so a revision can be checked.

    Grades are withheld deliberately. A new reviewer told that the last one said C has
    an easy answer available, which is the anchoring the fresh session exists to avoid.
    The concerns themselves are what a revision has to answer, so those carry forward,
    including every task an earlier reviewer did not count: without it, the next reviewer
    cannot tell whether the replacements answer what was wrong with the tasks they replaced.
    They come from Python's stored audits, so the planner cannot restate them.
    """
    from .local_science import rejected_cases
    found = []
    for record in history:
        critique = record.get("critique") or {}
        concerns = list(critique.get("objections", []))
        concerns += ["An earlier version's task " + item["case_id"] + " was not counted (" + item["verdict"]
                     + "): " + item["reason"] + " Suggested replacement: " + item["replacement"]
                     for item in rejected_cases(critique)]
        # What an earlier review required is what the revision has to answer. Run 3303fd93's second
        # critique of its fourth claim was never shown the five revisions the first had required.
        concerns += ["An earlier review required: " + item for item in critique.get("required_revisions") or []]
        concerns += ["An earlier version left untested: " + item for item in critique.get("coverage_gaps") or []]
        concerns += ["An earlier review found the skill departs from the reference solution, with no task exposing "
                     "it: " + item for item in critique.get("departures") or []]
        for concern in concerns:
            if concern not in found:
                found.append(concern)
    # Keep the most recent: the latest round's concerns are what the new design must answer.
    return found[-16:]


# The planner's notes travel to the critique, so they must not carry what Python withholds.
# Run b0955d2f's planner told one reviewer "The previous round settled at C" and another
# that "Two independent critiques have given this case the verdict counts". `review` alone
# is allowed: a source may be a review article. Bare `settled` refused run 3dc02567's "No
# two cases are settled by the same discriminating fact", so only `settled at` is caught.
PRIOR_REVIEW = re.compile(r"\b(?:critiqu\w*|reviewers?|verdicts?|settled at|no[- ]grade)\b"
                          r"|\b(?:previous|earlier|prior|last) rounds?\b", re.IGNORECASE)


def prior_review_note(candidate, args):
    """The first planner note bound for the critique that mentions an earlier review."""
    from .local_science import PLANNER_JUSTIFICATION
    notes = [("scope", candidate["scope"]), ("limitations", candidate["limitations"])]
    notes += [("applicability of " + case["case_id"], case["applicability"]) for case in candidate["cases"]]
    notes += [(key, args[key]) for key in PLANNER_JUSTIFICATION]
    for field, text in notes:
        found = PRIOR_REVIEW.search(text)
        if found:
            return field, found.group(0)
    return None


RECORD_ITEMS = 100
FETCH_TOOLS = ("fetch_local_reference", "fetch_local_asset", "load_local_resource")


def search_record(log, claim_id):
    """How the planner looked for sources, read from this attempt's workflow log.

    The planner's notes say what it searched; this is what it ran ("the search record" in
    local-contract.md). A WebSearch, read from the planner's own stream, belongs to the claim its
    last verifier tool call named. A fetch is read from Python's own record of the call, because
    the log cuts the planner's copy of a long reply short, and belongs to the claim it names.
    Event files are written once and never replaced, so they are read without the log's lock.
    """
    if log is None:
        return {"recorded": False, "note": "No workflow log was attached, so Python recorded no search."}

    def whose(named):
        return "this claim" if named == claim_id else "another claim" if named else "no claim yet"

    # A selection must never fail on what the log holds, so every shape is checked, not assumed.
    def outcome(event, data):
        if event == "tool_failed":
            return "failed: " + str(data.get("code"))
        if data.get("status") != "ok":
            error = data.get("error")
            return "refused: " + str(error.get("code") if isinstance(error, dict) else data.get("status"))
        return str(data.get("outcome"))

    searches, fetches, pending, active = [], [], {}, None
    for path in sorted(no_links(log.directory / "events").glob("[0-9]*.json")):
        try:
            item = json.loads(path.read_bytes())
        except (OSError, ValueError, UnicodeError, RecursionError):
            continue
        event = item.get("event") if isinstance(item, dict) else None
        data = item.get("data") if isinstance(item, dict) else None
        if not isinstance(data, dict):
            continue
        call = data.get("invocation_id") if isinstance(data.get("invocation_id"), str) else None
        if event == "tool_started" and data.get("tool") in FETCH_TOOLS:
            given = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
            target = given.get("url") or "operator-resource:" + str(given.get("resource_name", ""))
            entry = {"tool": data["tool"], "url": str(target)[:200], "for": whose(given.get("claim_id")),
                     "outcome": "no result recorded"}
            fetches.append(entry)
            if call:
                pending[call] = entry
            continue
        if event in ("tool_finished", "tool_failed") and call in pending:
            pending.pop(call)["outcome"] = outcome(event, data)[:80]
            continue
        if event != "claude_event" or data.get("role") != "planner":
            continue
        payload = data.get("payload")
        message = payload.get("message") if isinstance(payload, dict) else None
        blocks = message.get("content") if isinstance(message, dict) else None
        for block in blocks if isinstance(blocks, list) else []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            given = block.get("input") if isinstance(block.get("input"), dict) else {}
            if str(block.get("name", "")).rsplit("__", 1)[-1] == "WebSearch":
                searches.append({"query": str(given.get("query", ""))[:200], "for": whose(active)})
            elif isinstance(given.get("claim_id"), str):
                active = given["claim_id"]
    return {"recorded": True, "searches_total": len(searches), "fetches_total": len(fetches),
            "this_claim": {"searches": sum(item["for"] == "this claim" for item in searches),
                           "fetches": sum(item["for"] == "this claim" for item in fetches)},
            "searches": searches[:RECORD_ITEMS], "fetches": fetches[:RECORD_ITEMS],
            "note": "Python read the searches from the planner's own stream in this attempt's workflow log, "
                    "and the fetches from its own record of each call. The justification describes the "
                    "planner's searches; this records them. A search shown here for another claim can "
                    "still bear on this one."}


def select(store, state, claim_id, work, args, subject):
    """Freeze one plan and settle its grade: propose, critique, then fix or ask for a revision."""
    from .claims import section_texts
    from .local_science import (MAX_ROUNDS, PLANNER_JUSTIFICATION, REPLACEMENT_ROUNDS, audit, case_gap,
                                counted_cases, environment_digest, evidence_ceiling, fingerprint,
                                proposal_problem, rejected_cases)
    from .local_tasks import critique_packet
    key = args["candidate_ref"]
    allowed = {value["candidate_ref"] for value in store.get_json(work["lookup_ref"])["candidates"]}
    if key not in allowed | set(work["candidate_refs"]):
        raise Fault("candidate_not_returned", "Select a candidate returned by this claim's lookup or qualification.")
    candidate = pin_candidate(store, state, key)
    settings = settings_for(store, state)
    references = {ref: store.get_json(ref) for ref in catalog.reference_refs(candidate)}
    trials = settings["trial_count"]
    # A design found by lookup was built for another claim's sections ("Tasks" in local-tasks.md).
    wanted = claim_sections(store, state, claim_id)
    used = {name for case in candidate["cases"] for name in case["sections"]}
    unused, outside = [name for name in wanted if name not in used], sorted(used - set(wanted)) if wanted else []
    if unused or outside:
        return {"outcome": "local_grade_proposal_refused", "reason": "sections_unused", "candidate_ref": key,
                "unused_sections": unused, "sections_outside_claim": outside,
                "message": "Every section of this claim must be used by a task of the design, and no task may "
                           "use another claim's sections. Qualify a task design for this claim's sections."}
    ceiling, limits = evidence_ceiling(candidate, references, trials)
    history = [store.get_json(item) for item in work.setdefault("negotiation_refs", [])]
    identity = fingerprint(candidate)
    # The grade the last critique of *this exact design* settled at is the only grade below
    # the ceiling the planner may accept. A critique of a design since revised says nothing
    # about this one.
    previous = next((record for record in reversed(history)
                     if record["candidate_fingerprint"] == identity and record.get("critique")), None)
    settled = previous["critique"] if previous else None
    # The audit's settled ceiling is already the weakest of the proposal, the ceiling over
    # the tasks the critique counted, and its grade, so it is clamped to the ceiling. A
    # critique supporting D or none leaves it `None`: the design supports no *execution*
    # grade, and acceptance reads it that way. Only A, B and C can be proposed, so an
    # accepted "D" left a no-grade design unselectable: the planner of run b43780be could
    # neither accept the verdict nor run the plan, only abandon it.
    accepted = previous["settled_ceiling"] if previous else None
    problem = proposal_problem(args["target_grade"], ceiling, accepted)
    if problem:
        # Refuse before spending a critique session, and leave the claim in discovery so
        # strengthening the design or proposing the ceiling is the next ordinary step.
        if accepted:
            tail = ", or accept " + accepted + " as its last critique settled."
        elif settled and ceiling:
            tail = (". Its last critique supported no execution grade; proposing " + ceiling + " accepts "
                    "that, and the plan still runs to produce ungraded comparison evidence before the "
                    "documentary path.")
        else:
            tail = ". Strengthen the design to reach a stronger one."
        return {"outcome": "local_grade_proposal_refused", "reason": problem,
                "evidence_ceiling": ceiling, "evidence_limits": limits, "candidate_ref": key,
                "acceptable_grades": sorted({item for item in (ceiling, accepted) if item}),
                "message": "Propose the grade this design supports, " + (ceiling or "which is none") + tail}
    claim = claim_record(store, state, claim_id)
    rounds = len(history) + 1
    critique = record = None
    # Accepting this exact design's own critique ends the negotiation, including when it
    # concluded that the design supports no grade: executing it still produces ungraded
    # comparison evidence and the documentary path.
    accepting = bool(settled) and (args["target_grade"] == accepted or accepted is None)
    if accepting:
        critique = settled  # Re-running that judgment on the same evidence buys nothing.
    elif state["subject_config"]["synthetic"]:
        pass  # Fixture observations are never graded, so no session is spent.
    elif settled:
        # Re-proposing a grade this exact design was already critiqued below cannot
        # loop: no session and no round are spent on an unchanged design.
        return {"outcome": "local_design_unchanged", "candidate_ref": key,
                "objections": prior_objections(history),
                "message": "This design was already critiqued and settled at " + accepted
                           + ". Change the evidence to justify more, answering every revision the critique "
                           "required; propose " + accepted + " only when step 4 of \"Negotiating the grade\" "
                           "allows it."}
    elif rounds > MAX_ROUNDS:
        return {"outcome": "local_grade_rounds_exhausted", "candidate_ref": key,
                "rounds_used": len(history), "objections": prior_objections(history),
                "message": "The negotiation budget for this claim is spent. Reselect a design that "
                           "was already critiqued and accept the grade it settled at."}
    else:
        note = prior_review_note(candidate, args)
        if note:
            # Like an out-of-range proposal, refused before a session or a round is spent.
            field, phrase = note
            return {"outcome": "local_grade_proposal_refused", "reason": "prior_review_in_packet",
                    "field": field, "phrase": phrase, "evidence_ceiling": ceiling,
                    "evidence_limits": limits, "candidate_ref": key,
                    "acceptable_grades": sorted({item for item in (ceiling, accepted) if item}),
                    "message": "The critique never learns what an earlier review decided, and " + field
                               + " mentions one (" + repr(phrase) + "). Describe this design and its "
                               "evidence only: Python already gives the critique the earlier objections "
                               "and the tasks they did not count. A justification field needs only a new "
                               "proposal; a task's applicability or the design's scope or limitations "
                               "needs a revised design."}
        record = search_record(getattr(subject, "log", None), claim_id)
        sections = section_texts(store, verified_snapshot(store, state), set(claim.get("sections") or []))
        packet = critique_packet(claim, sections, candidate, references, args, ceiling, limits, trials,
                                 prior_objections(history), record, store.get)
        from .documentary import CRITIC_PACKET_LIMIT, critique_tasks
        size = len(canonical(packet))
        if size > CRITIC_PACKET_LIMIT:
            # Refused before a session or a round is spent; the critique never sees a shortened design.
            return {"outcome": "local_grade_proposal_refused", "reason": "critique_packet_too_large",
                    "packet_bytes": size, "limit_bytes": CRITIC_PACKET_LIMIT, "evidence_ceiling": ceiling,
                    "evidence_limits": limits, "candidate_ref": key,
                    "acceptable_grades": sorted({item for item in (ceiling, accepted) if item}),
                    "message": "The critique's packet for this design is " + str(size) + " bytes, over its "
                               + str(CRITIC_PACKET_LIMIT) + "-byte limit. Shorten the design: fewer or shorter "
                               "tasks, outputs, quotes, programs or notes."}
        work["critique_packet_ref"] = keep(store, state, packet)
        try:
            critique = critique_tasks(subject, packet)
        except (Fault, OSError, AttributeError) as error:
            detail = " " + str(error) if isinstance(error, Fault) else ""
            return limitation(store, state, claim_id, getattr(error, "code", "critic_unavailable"),
                              "The independent grade critique did not complete." + detail + " This is an "
                              "operational failure, not an absence of scientific evidence.", asserted_by="runtime")
        work["critique_ref"] = keep(store, state, critique)
    work["candidate_ref"] = key
    selection = {"candidate_ref": key, "applicability": args["applicability"],
                 "target_grade": args["target_grade"],
                 **{name: args[name] for name in PLANNER_JUSTIFICATION},
                 "snapshot_ref": state["source_ref"], "subject_config": state["subject_config"],
                 "source_digest": store.get_json(state["source_ref"])["digest"],
                 "environment_digest": environment_digest(settings, state["subject_config"],
                                                          state.get("local_environment_ref")),
                 "method_version": candidate["method_version"], "trials_per_case": trials,
                 "claim_id": claim_id}
    work["selection_ref"] = keep(store, state, selection)
    audit_record = audit(candidate, claim, settings, selection, references, critique=critique, rounds=rounds,
                         judged=not accepting)
    work["audit_ref"] = keep(store, state, audit_record)
    work["negotiation_refs"].append(work["audit_ref"])
    if not audit_record["mechanically_accepted"]:
        return {"outcome": "local_audit_rejected", "audit": audit_record}
    # Two revisions may be spent replacing tasks the critique did not count. A third
    # critique that still rejects tasks settles the grade the counting tasks support.
    rejected = rejected_cases(critique) if critique and not accepting else []
    replacements_used = sum(1 for earlier in history if rejected_cases(earlier.get("critique")))
    replacements_spent = bool(rejected) and replacements_used >= REPLACEMENT_ROUNDS
    gaps = list(critique.get("coverage_gaps") or []) if critique and not accepting else []
    # The coverage return (tool-contracts.md): a critique agreeing with the proposal, at any grade, sends
    # the claim back once when it lists what no task tests. Run f84c131c's four critiques agreed with A
    # while naming untested parts of every claim, and nothing asked the planner to answer them. Ending it
    # needs no search: run 2bef9e0d's planner met that rule with web searches it never read.
    gap_return = (bool(gaps) and not work.get("gap_return_ref") and audit_record["settled_ceiling"] == args["target_grade"]
                  and rounds < MAX_ROUNDS and not replacements_spent)
    if gap_return:
        work["gap_return_ref"] = keep(store, state, {"kind": "local-gap-return", "candidate_fingerprint": identity,
                                                     "round": rounds})
    if (critique and not accepting and (audit_record["settled_ceiling"] != args["target_grade"] or gap_return)
            and rounds < MAX_ROUNDS and not replacements_spent):
        # Strengthen the evidence and propose the new ceiling, or accept this grade.
        # On the last round the settled grade is fixed instead of offered.
        held, settled_grade = audit_record["held_by_departures"], audit_record["settled_ceiling"]
        return {"outcome": "local_grade_revision_required", "audit": audit_record,
                "supported_grade": critique["supported_grade"],
                "settled_grade": audit_record["settled_ceiling"],
                "objections": critique["objections"],
                "required_revisions": critique["required_revisions"],
                "coverage_gaps": gaps,
                "departures": list(critique.get("departures") or []),
                "case_replacements": rejected,
                "rounds_remaining": MAX_ROUNDS - rounds,
                "replacement_rounds_remaining": REPLACEMENT_ROUNDS - replacements_used - bool(rejected),
                "case_gap": case_gap(candidate, counted_cases(critique), args["target_grade"],
                                     critique["supported_grade"], held),
                **({"message": "The critique agreed with " + args["target_grade"] + " but named parts of the claim "
                              "no task tests, in coverage_gaps; this return comes once per claim. Test the gaps "
                              "with tasks in a revised design and propose its ceiling, or accept "
                              + args["target_grade"] + " and leave them open, which the report says."}
                   if gap_return else
                   {"message": "The critique found where the skill's own procedure departs from the reference "
                               "solution with no task exposing it, in departures, so the grade stays below "
                               + args["target_grade"] + ". Expose each in a revised design whose input puts the "
                               "difference outside its tolerance, and propose its ceiling, or accept "
                               + (settled_grade or "that this design supports no execution grade") + "."}
                   if held else {})}
    state["claim_states"][claim_id] = "local_ready"
    return {"outcome": "local_plan_fixed", "candidate": candidate,
            "selection_ref": work["selection_ref"], "audit": audit_record}


def settings_for(store,state):
    from .local_config import load_configuration
    return store.get_json(state["local_settings_ref"]) if state.get("local_settings_ref") else {**load_configuration(),"trial_count":1,"max_subject_calls":64,"documentary_assessment":False}


def check_reference_host(settings,url):
    from urllib.parse import urlsplit
    if settings["allowed_reference_hosts"] and urlsplit(url).hostname not in settings["allowed_reference_hosts"]:
        raise Fault("resource_not_authorized","Reference host is outside the operator's configured list.")


def stronger_evidence_available(store,state,claim_id,work):
    """True when this claim qualified a candidate of its own and never ran it.

    Scoped to candidates qualified for this claim. A catalog candidate returned by
    lookup may belong to another claim's scope, and whether it applies here is a
    semantic judgment Python cannot make; blocking on it would refuse the
    documentary path for every claim as soon as any candidate exists.

    "Never ran" is the claim still being in local_discovery, since no path returns there
    after execution. It used to be "never selected", which let a selected but unexecuted
    plan skip to documentary; run b43780be did exactly that and discarded 18 planned trials
    that workflow.md and the rubric both say a no-grade design must still run.
    """
    if state["claim_states"][claim_id]!="local_discovery":
        return False
    return any(store.get_json(key).get("status")=="qualified_local"
               for key in work.get("candidate_refs",[]))


def assessor_changed(state, subject):
    """True when the runtime or the assessor's settings differ from those pinned at bootstrap."""
    from .storage import implementation_bytes
    return digest(implementation_bytes()) != state["local_method_ref"] or subject.identity != state["subject_config"]


def documentary_record(store, state, claim_id, evidence, limitations, subject, retained, fallback_for=None):
    """Assess one pinned packet in a fresh session and return its record; a Fault says why not.

    The planner's documentary step and the fallback after a runner fault share this, so the
    packet, the replay marker and the grade-D rule have one owner. `fallback_for` names the
    fault a fallback stands in for.
    """
    from .documentary import assess, RUBRIC, RUBRIC_REF
    work = state["local_work"][claim_id]
    claim = claim_record(store, state, claim_id)
    packet = {"claim": {key: claim[key] for key in ("statement", "scope", "expected_behavior")},
              "evidence": evidence, "rubric": RUBRIC, "limitations": limitations}
    packet_ref = keep(store, state, packet)
    work["documentary_packet_ref"] = packet_ref
    marker = no_links(store.run_dir(state["run_id"]) / ("assessor-" + str(sorted(state["claim_states"]).index(claim_id)) + ".json"))
    if marker.exists():
        raise Fault("interrupted_assessment", "A prior assessment request exists and was not automatically replayed.")
    atomic_write(marker, canonical({"packet_ref": packet_ref, "created_at": utc_now()}))
    try:
        response = assess(subject, packet)
    except (Fault, OSError, AttributeError) as error:
        raise Fault(getattr(error, "code", "assessor_unavailable"),
                    "The independent assessment did not complete; this is not missing scientific evidence.") from error
    assessment_ref = keep(store, state, response)
    work["assessment_ref"] = assessment_ref
    # A completed independent assessment against the installed rubric is grade D.
    # Synthetic fixture observations never receive a grade.
    graded = not state["subject_config"]["synthetic"]
    # The planner's path compares documents and never runs the skill, so there is no
    # behaviour to measure: `not_applicable`. A fallback stands in for an execution that was
    # attempted and lost, which is what `not_obtained` says.
    unmeasured = "not_obtained" if fallback_for else "not_applicable"
    notes = ["Documentary consistency only; scientific performance remains unverified.",
             response["assessment"]["limitations"],
             "Assessed by a fresh independent session against the installed rubric; AI judgment is primary and disclosed."
             if graded else "Synthetic fixture run; no grade is assigned."]
    if fallback_for:
        notes.insert(0, "Fallback documentary assessment after " + fallback_for["fault"] + ": " + fallback_for["reason"]
                     + " No execution evidence was obtained, so this grade is AI judgment of the reference quotes the"
                     " claim's planned cases were keyed to, not of the skill's behaviour.")
    record = {**retained, "kind": "local-documentary", "assessment_ref": assessment_ref, "packet_ref": packet_ref,
              "rubric_ref": RUBRIC_REF,
              "scientific_status": response["assessment"]["status"] if graded else None,
              "evidence_grade": "D" if graded else None,
              "status_withheld_reason": None if graded else "synthetic_observations",
              "accuracy": unmeasured, "consistency": unmeasured, "completeness": unmeasured,
              # A fallback keeps the runner fault on its own axis, beside the grade.
              "fault": fallback_for["fault"] if fallback_for else None,
              "documentary_status": response["assessment"]["status"],
              "ai_involvement": {"orchestration": True, "evidence_generation": True, "verdict": True},
              "limitations": notes}
    if fallback_for:
        record["fallback_for"] = fallback_for
    return record


def documentary_step(store,state,claim_id,name,args,subject):
    work=state["local_work"][claim_id]
    if not work.get("lookup_ref"):
        raise Fault("catalog_lookup_required","Check available evaluators before concluding this claim.")
    if not (work.get("reference_refs") or work.get("candidate_refs")):
        # Neither path may conclude on a free-text account of a search Python never saw.
        raise Fault("evidence_search_required",
                    "Retrieve at least one reference, or record a rejected qualification attempt, "
                    "before concluding that no stronger evidence exists.")
    if stronger_evidence_available(store,state,claim_id,work):
        raise Fault("stronger_evidence_available",
                    "A qualified candidate for this claim has not been executed. Select and run it, "
                    "or record why it does not apply, before taking a documentary or unverified outcome.")
    if name=="assess_local_documentary" and assessor_changed(state,subject):
        return limitation(store,state,claim_id,"assessment_identity_changed","Runtime or assessor settings changed after bootstrap.")
    previous=store.get_json(work["result_ref"]) if work.get("result_ref") else None
    retained={"claim_id":claim_id,"receipts":previous["receipts"] if previous else [],
              "comparison_ref":work.get("result_ref"),"synthetic":state["subject_config"]["synthetic"]}
    if name=="record_local_unverified":
        record={**retained,"kind":"local-unverified","scientific_status":"inconclusive","evidence_grade":"U",
                "search_account":args["search_account"],"missing_evidence":args["missing_evidence"],
                "limitations":["No acceptable scientific evidence established; operational failures do not authorize this result."]}
    else:
        refs=set(work["reference_refs"])
        if work.get("candidate_ref"):
            refs.update(catalog.reference_refs(store.get_json(work["candidate_ref"])))
        evidence=[]
        for item in args["evidence"]:
            if item["reference_ref"] not in refs:
                raise Fault("documentary_reference_invalid","Use references retrieved for this claim.")
            resource=store.get_json(item["reference_ref"])
            if item["quote"] not in resource["text"]:
                raise Fault("documentary_reference_invalid","Every excerpt must be an exact reference quote.")
            evidence.append({**item,"url":resource["url"],"version":resource["version"],"license":resource["license"]})
        try:
            record=documentary_record(store,state,claim_id,evidence,args["limitations"],subject,retained)
        except Fault as error:
            return limitation(store,state,claim_id,error.code,str(error),retained["receipts"])
    work["result_ref"]=keep(store,state,record)
    state["claim_states"][claim_id]="terminal_result"
    return {"outcome":"local_documentary_complete" if name=="assess_local_documentary" else "local_unverified_recorded","result":record}


def execute(store, state, claim_id, subject, retry=False):
    """Run the settled plan's full trial set; `retry` is the end-of-run re-run, kept apart."""
    from .claude_runner import SYNTHETIC_MODEL
    from .storage import implementation_bytes
    if digest(implementation_bytes()) != state["local_method_ref"]:
        return limitation(store, state, claim_id, "method_changed", "Runtime code changed after bootstrap; start a new verification.")
    work = state["local_work"][claim_id]
    if not work.get("audit_ref"):
        raise Fault("audit_required", "No settled plan audit exists for this claim.", fatal=True)
    candidate = pin_candidate(store, state, work["candidate_ref"])
    if subject.identity != state["subject_config"]:
        return limitation(store, state, claim_id, "subject_identity_changed", "Restart with the originally pinned subject settings.")
    # Stable ordinal avoids repeating the 70-character claim hash in Windows
    # paths; the full claim/selection identity remains inside every receipt.
    claim_directory = f"claim-{sorted(state['claim_states']).index(claim_id) + 1:03}" + ("-retry" if retry else "")
    directory = no_links(store.root / "subject-runs" / state["run_id"] / claim_directory)
    if directory.exists() and list(directory.glob("*-request.json")):
        receipts = []
        for path in sorted(directory.glob("*.json")):
            raw = no_links(path).read_bytes()
            key = store.put(raw)
            if key not in state["objects"]:
                state["objects"].append(key)
            receipts.append(key)
        state["subject_calls_used"] += len(list(directory.glob("*-request.json")))
        return limitation(store, state, claim_id, "interrupted_subject_execution",
                          "Earlier trial requests are retained. No trial was replayed.", receipts)
    settings=settings_for(store,state)
    trials=store.get_json(work["selection_ref"])["trials_per_case"]
    audit_record=store.get_json(work["audit_ref"])
    if audit_record["selection_digest"]!=digest(canonical(store.get_json(work["selection_ref"]))) or not audit_record["mechanically_accepted"]:
        return limitation(store,state,claim_id,"audit_invalidated","The plan differs from its accepted audit.")
    if state["subject_calls_used"] + len(candidate["cases"])*trials > settings["max_subject_calls"]:
        return limitation(store, state, claim_id, "subject_budget_exhausted", "The configured subject call limit would be exceeded.")
    snapshot = verified_snapshot(store, state)
    source=[]
    for entry in snapshot["files"]:
        raw=store.get(entry["digest"])
        source.append({"path":entry["path"],**({"content":raw.decode("utf-8")} if entry["encoding"]=="utf-8" else {"base64":base64.b64encode(raw).decode()})})
    from .local_tasks import score as score_task, task_input
    receipts, observations, scored_trials = [], [], []
    for index, (case,trial) in enumerate(((case,trial) for case in candidate["cases"] for trial in range(1,trials+1)),1):
        # A task gives its job, its files' paths and its output fields ("Tasks" in local-tasks.md).
        case_input = task_input(case)
        task_files = {item["name"]: store.get(item["object_ref"]) for item in case.get("files") or []}
        request = {"kind": "local-subject-request", "snapshot_ref": state["source_ref"],
                   "selection_ref": work["selection_ref"], "case_id": case["case_id"], **case_input,
                   "subject": state["subject_config"], "trial":trial,"created_at": utc_now()}
        request_ref = keep(store, state, request)
        atomic_write(directory / f"{index:03}-request.json", canonical(request))
        receipts.append(request_ref)
        state["subject_calls_used"] += 1
        try:
            response = subject.observe(source=source, case_input=case_input,
                                       config=state["subject_config"], timeout_seconds=settings["subject_timeout_seconds"],
                                       task_files=task_files)
            catalog.safe_payload(response)
            if (not isinstance(response, dict) or not isinstance(response.get("text"), str) or len(response["text"].encode("utf-8")) > 16384
                    or response.get("invocation_verified") is not True or not response.get("response_id")):
                raise Fault("subject_response_invalid", "Subject response or explicit skill invocation is incomplete.")
        except (Fault, OSError) as error:
            code = error.code if isinstance(error, Fault) else "subject_unavailable"
            # A safety refusal is reported as itself. It says the provider would not answer,
            # not that the skill was wrong. Execution never retries a trial; the one
            # disclosed re-run of a stopped claim is write_report_card's, and its record says
            # what happened, so this reason does not predict it.
            if code == "subject_refused":
                reason = str(error)
            elif code == "claude_timeout":
                # The limit is ours. Saying "did not return an observation" hid that run
                # 84e90683's subject was still working when the verifier's 120 s ran out.
                reason = ("Trial " + str(trial) + " of task " + case["case_id"] + " reached this verifier's per-trial limit of "
                          + str(settings["subject_timeout_seconds"]) + " s (subject_timeout_seconds) before the subject answered. "
                          "The limit is the verifier's setting, not a property of the skill; a longer limit may let this case finish.")
            else:
                reason = "Subject execution did not return a complete verified observation."
            return limitation(store, state, claim_id, code, reason, receipts)
        artifacts=[]
        for item in response.pop("artifacts",[]):
            from .ingest import valid_relative
            if not valid_relative(item["path"]):
                raise Fault("artifact_invalid","Artifact paths must stay within the trial output directory.",fatal=True)
            raw=base64.b64decode(item["base64"],validate=True)
            if digest(raw)!=item["sha256"]:
                raise Fault("artifact_integrity","A generated artifact digest did not match.",fatal=True)
            key=store.put(raw)
            if key not in state["objects"]:
                state["objects"].append(key)
            artifact_path=no_links(directory/"artifacts"/f"{index:03}"/item["path"])
            atomic_write(artifact_path,raw)
            artifacts.append({"path":item["path"],"object_ref":key,"bytes":len(raw),"saved_path":str(artifact_path)})
        response = {**response, "artifacts":artifacts,"trial":trial,"case_id": case["case_id"], "request_ref": request_ref}
        response_ref = keep(store, state, response)
        atomic_write(directory / f"{index:03}-response.json", canonical(response))
        receipts.append(response_ref)
        models=response.get("observed_model_ids",[])
        if models:
            # Exactly one model answers every trial. Pinning whatever the first trial reported
            # let run 3dc02567's first two trials, each answered partly by Opus 4.8, pass as a
            # stable identity until the third differed.
            answered=sorted(set(models)-{SYNTHETIC_MODEL})
            pinned="retry_observed_models_ref" if retry else "observed_models_ref"
            if len(answered)!=1:
                return limitation(store,state,claim_id,"subject_model_changed","A trial was answered by "+(", ".join(answered) or "no model")+", not by exactly one model.",receipts)
            if pinned not in work:
                work[pinned]=keep(store,state,answered)
            elif store.get_json(work[pinned])!=answered:
                return limitation(store,state,claim_id,"subject_model_changed","Observed model identity changed within the frozen trial set.",receipts)
        # Python reads the trial's results file itself ("Reading a trial's results", local-tasks.md).
        scored_trials.append({"index":index,"case":case,"trial":trial,"request_ref":request_ref,
                              "response_ref":response_ref,"models":models,"run_problems":response.get("run_problems",[]),
                              "files_not_kept":response.get("files_not_kept",[]),
                              "score":score_task(case,{item["path"]:store.get(item["object_ref"]) for item in artifacts})})
    # Tasks the critique did not count ran and stay in the receipts, but a task measuring
    # something other than the claim cannot pass or fail it.
    from .local_science import decide, rejected_cases
    counted = set(audit_record["counted_cases"])
    cases = [case for case in candidate["cases"] if case["case_id"] in counted]
    for item in scored_trials:
        scored = {"case_id": item["case"]["case_id"], "trial": item["trial"], "request_ref": item["request_ref"],
                  "response_ref": item["response_ref"], "comparison_status": item["score"]["status"],
                  "model_ids": item["models"], "outputs": item["score"]["outputs"],
                  "results_found": item["score"]["results_found"], "run_problems": item["run_problems"],
                  "files_not_kept": item["files_not_kept"],
                  **({"results_problem": item["score"]["results_problem"]} if "results_problem" in item["score"] else {})}
        score_ref = keep(store, state, scored)
        receipts.append(score_ref)
        atomic_write(directory / f"{item['index']:03}-score.json", canonical(scored))
        observations.append(scored)
    scored = [row for row in observations if row["case_id"] in counted]
    statuses = {row["comparison_status"] for row in scored}
    result = {"kind": "local-comparison", "claim_id": claim_id, "candidate_ref": work["candidate_ref"],
              "selection_ref": work["selection_ref"], "observations": observations, "receipts": receipts,
              # A wrong result decides the claim whatever an unreadable trial said ("Status" in local-contract.md).
              "comparison_status": "no_counted_cases" if not scored else "fail" if "fail" in statuses
              else "invalid" if "invalid" in statuses else "pass",
              "uncounted_cases": [{key: item[key] for key in ("case_id", "verdict", "reason")}
                                  for item in rejected_cases(audit_record.get("critique"))],
              "scientific_status": None, "evidence_grade": None, "synthetic": subject.identity["synthetic"],
              "limitations": candidate["qualification_limitations"] + [candidate["limitations"]]}
    result.update(decide(audit_record, scored, cases, trials, synthetic=subject.identity["synthetic"]))
    work["result_ref"] = keep(store, state, result)
    needs_documentary=not result["evidence_grade"] and settings["documentary_assessment"]
    state["claim_states"][claim_id] = "local_documentary" if needs_documentary else "terminal_result"
    return {"outcome": "local_documentary_required" if needs_documentary else "local_comparison_complete", "result": result}


# Trial faults the one end-of-run re-run may clear ("Subject boundary" in local-contract.md).
# A security fault is never re-run, nor is a failure of Python's own checks.
RETRY_FAULTS = {"subject_refused", "subject_model_changed", "subject_unavailable", "subject_response_invalid",
                "skill_invocation_unverified", "claude_incomplete", "claude_protocol_error",
                "claude_identity_error", "claude_timeout", "claude_output_limit", "claude_unavailable",
                "sandbox_unavailable", "sandbox_image_unavailable", "sandbox_start_failed",
                "sandbox_not_started", "sandbox_timeout", "sandbox_source_unavailable"}
# A trial runs the skill on its task's files, so the re-run budgets five minutes for each, half the
# default per-trial limit, and five more for the report.
RETRY_SECONDS_PER_TRIAL = 300
RETRY_REPORT_SECONDS = 300
# Set by the runner for its planner's tool server; absent when nothing bounds the attempt.
DEADLINE_ENV = "SCI_VERIFIER_ATTEMPT_DEADLINE"


def retry_stopped_claims(store, state, subject):
    """Re-run once, in full, each claim a subject-trial fault stopped, and record why not otherwise."""
    import os
    import time
    settings = settings_for(store, state)
    deadline = os.environ.get(DEADLINE_ENV)
    for claim_id in sorted(state["claim_states"]):
        work = state["local_work"].get(claim_id) or {}
        if (state["claim_states"][claim_id] != "terminal_operational" or "retry_ref" in work
                or not work.get("outcome_ref") or not work.get("audit_ref") or not work.get("selection_ref")):
            continue
        first = store.get_json(work["outcome_ref"])
        if first.get("fault") not in RETRY_FAULTS:
            continue
        trials = len(store.get_json(work["candidate_ref"])["cases"]) * store.get_json(work["selection_ref"])["trials_per_case"]
        record = {"kind": "local-retry", "claim_id": claim_id, "fault": first["fault"], "first_attempt_ref": work["outcome_ref"]}
        skip = None
        if not store.get_json(work["audit_ref"]).get("settled_ceiling") and settings["documentary_assessment"]:
            skip = "Its plan settled no execution grade, and the documentary step after a re-run needs the planner."
        elif state["subject_calls_used"] + trials > settings["max_subject_calls"]:
            skip = "The subject-call budget cannot cover a re-run of " + str(trials) + " trials."
        elif deadline and float(deadline) - time.time() < trials * RETRY_SECONDS_PER_TRIAL + RETRY_REPORT_SECONDS:
            skip = "Too little time remains before the attempt deadline to re-run " + str(trials) + " trials and write the report."
        if skip:
            work["retry_ref"] = keep(store, state, {**record, "status": "skipped", "reason": skip})
            continue
        del work["outcome_ref"]
        outcome = execute(store, state, claim_id, subject, retry=True)["outcome"]
        if state["claim_states"][claim_id] == "local_documentary":
            # Nothing may wait on the planner once the report is being written.
            state["claim_states"][claim_id] = "terminal_result"
        work["retry_ref"] = keep(store, state, {**record, "status": "retried", "outcome": outcome})


def case_quotes(store, candidate_ref, limit=8):
    """Each distinct quote a task design rests on: its generator's model and each output's quoted value
    or rule, in order. Qualification already proved every one exact, so a packet built from them needs
    no planner."""
    evidence = []
    candidate = store.get_json(candidate_ref)
    generator = candidate.get("generator") or {}
    pairs = [(generator.get("reference_ref"), generator.get("model_quote")),
             *((output.get("reference_ref"), output.get("source_quote"))
               for case in candidate["cases"] for output in case["outputs"])]
    for ref, quote in pairs:
        if not ref or not quote:
            continue
        reference = store.get_json(ref)
        item = {"reference_ref": ref, "quote": quote, "url": reference["url"],
                "version": reference["version"], "license": reference["license"]}
        if item not in evidence and quote in reference["text"]:
            evidence.append(item)
    return evidence[:limit]


def fallback_documentary(store, state, subject):
    """Give each claim a runner fault still stops a documentary assessment Python assembles.

    Run 84e90683's ring-option claim timed out twice and reported nothing. The planner has
    finished by now, so the evidence is the reference quote each planned case was keyed to,
    and no subject answer enters the packet ("Independent documentary path",
    local-contract.md). Whenever the assessment does not run, the fault stays the outcome.
    """
    import os
    import time
    from .documentary import ASSESSOR_TIMEOUT_SECONDS
    settings = settings_for(store, state)
    deadline = os.environ.get(DEADLINE_ENV)
    for claim_id in sorted(state["claim_states"]):
        work = state["local_work"].get(claim_id) or {}
        if (state["claim_states"][claim_id] != "terminal_operational" or "fallback_ref" in work
                or not work.get("outcome_ref")):
            continue
        stopped = store.get_json(work["outcome_ref"])
        if stopped.get("fault") not in RETRY_FAULTS:
            continue
        fallback_for = {"fault": stopped["fault"], "limitation_ref": work["outcome_ref"], "reason": stopped["reason"]}
        record = {"kind": "local-fallback", "claim_id": claim_id, **fallback_for}
        evidence = case_quotes(store, work["candidate_ref"]) if work.get("candidate_ref") else []
        reason = None
        if not settings["documentary_assessment"]:
            reason = "Documentary assessment is disabled in the local settings."
        elif not evidence:
            reason = "The claim has no qualified task design whose reference quotes could be assessed."
        elif (deadline and float(deadline) - time.time()
              < ASSESSOR_TIMEOUT_SECONDS + RETRY_REPORT_SECONDS):
            reason = "Too little time remains before the attempt deadline for an assessment and the report."
        elif assessor_changed(state, subject):
            reason = "Runtime or assessor settings changed after bootstrap."
        if reason is None:
            retained = {"claim_id": claim_id, "receipts": stopped["receipts"], "comparison_ref": None,
                        "synthetic": state["subject_config"]["synthetic"]}
            limitations = ("Assembled by the verifier after the planner finished: execution of this claim stopped on "
                           + stopped["fault"] + " and was not recovered. Each excerpt is the reference passage one of "
                           "the claim's planned test cases was keyed to. No subject answer is included.")
            try:
                result = documentary_record(store, state, claim_id, evidence, limitations, subject, retained, fallback_for)
            except Fault as error:
                reason = "The fallback assessment did not complete (" + error.code + ")."
            else:
                work["result_ref"] = keep(store, state, result)
                state["claim_states"][claim_id] = "terminal_result"
                work["fallback_ref"] = keep(store, state, {**record, "status": "assessed"})
                continue
        work["fallback_ref"] = keep(store, state, {**record, "status": "not_assessed", "reason": reason})


def axis_lines(terminal, cell):
    """Render the independent axes so a reader can localise the fault at a glance.

    Grade reports the reference, accuracy and consistency report the skill, completeness
    and fault report the run. Printing them together is the point: a weak reference and a
    wobbling skill produce very different cards that a single verdict line would flatten.
    """
    def measured(value, render):
        """Sentinels arrive as bare strings; only a dict carries an actual measurement."""
        return render(value) if isinstance(value, dict) else cell(value or "unassigned")

    lines = []
    if terminal.get("scientific_status") is None and terminal.get("status_withheld_reason"):
        lines.append("Status withheld: " + cell(terminal["status_withheld_reason"]) + ".")
    if terminal.get("accuracy") is not None or terminal.get("consistency") is not None:
        # `not_applicable` and `not_obtained` arrive as bare strings, not measurements:
        # the documentary path never measures behaviour, which is a different statement
        # from an execution that was attempted and returned nothing.
        def spread(value):
            label = cell(value.get("label", "unassigned"))
            if value.get("label") == "split":
                label += (f" ({value['split_cases']} split of "
                          f"{value['split_cases'] + value['unanimous_cases']} cases)")
            return label

        lines.append("Accuracy: "
                     + measured(terminal.get("accuracy"), lambda v: cell(f"{v['matched']} of {v['evaluated']}"))
                     + "; consistency: " + measured(terminal.get("consistency"), spread)
                     + "; completeness: "
                     + measured(terminal.get("completeness"),
                                lambda v: cell(f"{v['obtained']} of {v['planned']} trials")) + ".")
    if terminal.get("aggregation_rule"):
        lines.append("Aggregation rule: " + cell(terminal["aggregation_rule"]) + ".")
    if terminal.get("execution_limit_reasons"):
        lines.append("Execution limited by: " + cell(", ".join(terminal["execution_limit_reasons"]))
                     + ". These describe the run and the skill, not the reference.")
    if terminal.get("fault"):
        lines.append("Runner fault: " + cell(terminal["fault"]) + ". This is ours, not the skill's.")
    return lines + [""] if lines else []


def report(store, state):
    from .local_science import rejected_cases, size_limit

    def cell(value):
        return escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")

    manifest = store.get_json(state["manifest_ref"])
    claims = manifest["claims"]
    rows = []
    lines = ["# Local skill verification", "", "SYNTHETIC FIXTURE RUN" if state["subject_config"]["synthetic"]
             else "Personal/local reference comparisons", "",
             "Scientific status and evidence grade are separate from operational completion. Mechanical qualification alone is ungraded.", ""]
    environment = None
    if state.get("local_environment_ref"):
        from .environment import report_line, report_summary
        environment = report_summary(store.get_json(state["local_environment_ref"]))
        lines.extend([cell(report_line(environment)), ""])
    # Which of the skill's sections the claims hold, and why the rest were set aside ("Claims" in
    # local-tasks.md).
    from .claims import manifest_coverage
    snapshot = verified_snapshot(store, state)
    coverage = manifest_coverage(manifest, {entry["path"]: normalize(store.get(entry["digest"]).decode("utf-8"))
                                            for entry in snapshot["files"] if entry["encoding"] == "utf-8"})
    covering = {}
    if coverage:
        for section in coverage["sections"]:
            for claim_id in section["claims"]:
                covering.setdefault(claim_id, []).append(section["heading"])
        covered = sum(bool(section["claims"]) for section in coverage["sections"])
        aside = coverage["set_aside"]
        lines.extend([cell("Skill sections: the claims hold " + str(covered) + " of the " + str(len(coverage["sections"]))
                           + " sections of SKILL.md" + ("; no claim holds " + "; ".join(coverage["uncovered"])
                                                        if coverage["uncovered"] else "")
                           + ("; set aside: " + "; ".join(item["section"] + " " + item["heading"] + " (" + item["reason"]
                                                          + ")" for item in aside) if aside else "") + "."), ""])
    for claim in claims:
        work = state["local_work"][claim["claim_id"]]
        terminal = store.get_json(work.get("result_ref") or work["outcome_ref"])
        candidate = store.get_json(work["candidate_ref"]) if work.get("candidate_ref") else None
        responses = [store.get_json(key) for key in terminal["receipts"]]
        answers = {(item["case_id"],item.get("trial",1)): item for item in responses if item.get("request_ref") and "text" in item}
        scores = {(item["case_id"],item.get("trial",1)): item for item in responses if "comparison_status" in item}
        tests, sources = [], {}
        audit_record = store.get_json(work["audit_ref"]) if work.get("audit_ref") else None
        counted = (audit_record or {}).get("counted_cases")
        if candidate:
            trials=store.get_json(work["selection_ref"])["trials_per_case"] if work.get("selection_ref") else 1
            for ref in catalog.reference_refs(candidate):
                reference = store.get_json(ref)
                sources[ref] = {key: reference[key] for key in ("url", "version", "license", "raw_ref", "retrieved_at", "authority", "redistribution")}
            for case,trial in ((case,trial) for case in candidate["cases"] for trial in range(1,trials+1)):
                observed = answers.get((case["case_id"],trial))
                score = scores.get((case["case_id"],trial)) or {}
                # Each output's expected value, the value found and its verdict.
                tests.append({"case_id": case["case_id"], "trial": trial, "input": case["job"],
                              "expected": {output["field"]: output["expected"] for output in case["outputs"]},
                              "artifacts": observed.get("artifacts", []) if observed else [],
                              "observed": observed["text"] if observed else None,
                              "comparison_status": score.get("comparison_status", "not_obtained"),
                              "outputs": score.get("outputs"), "results_found": score.get("results_found"),
                              "results_problem": score.get("results_problem"),
                              "run_problems": score.get("run_problems", []),
                              "files_not_kept": score.get("files_not_kept", []), "sections": case["sections"],
                              "files": case.get("files") or [], "applicability": case["applicability"],
                              "counted": counted is None or case["case_id"] in counted,
                              "session_id": observed.get("session_id") if observed else None,
                              "observed_model_ids": observed.get("observed_model_ids", []) if observed else [],
                              "refusals": observed.get("refusals", []) if observed else []})
        execution_counts={"planned":len(tests),"attempted":sum(item.get("kind")=="local-subject-request" for item in responses),
                          "obtained":len(answers),"evaluated":sum("comparison_status" in item for item in responses),
                          "invalid":sum(item.get("comparison_status")=="invalid" for item in responses),"missing":len(tests)-len(answers)}
        required_grade=settings_for(store,state).get("minimum_grade")
        achieved=terminal.get("evidence_grade")
        meets_required=None if required_grade is None else bool(achieved in {"A","B","C","D"} and "ABCD".index(achieved)<= "ABCD".index(required_grade))
        retry = store.get_json(work["retry_ref"]) if work.get("retry_ref") else None
        if retry:
            retry = {**retry, "first_attempt": store.get_json(retry["first_attempt_ref"])}
        fallback = store.get_json(work["fallback_ref"]) if work.get("fallback_ref") else None
        rows.append({"claim": claim, "record": terminal, "tests": tests, "references": sources,"execution_counts":execution_counts,
                     "method": candidate["method"] if candidate else None,
                     "retry": retry, "fallback": fallback,
                     "required_grade":required_grade,"meets_required_grade":meets_required,
                     "audit":audit_record,
                     "sections":covering.get(claim["claim_id"],[]),
                     "size_limited":size_limit(audit_record,candidate) if audit_record and candidate else None,
                     "documentary_assessment":store.get_json(work["assessment_ref"]) if work.get("assessment_ref") else None,
                     "candidate_scope": candidate["scope"] if candidate else None})
        lines.extend(["## " + cell(claim["statement"]), ""])
        lines.extend(["Skill sections: " + cell("; ".join(covering.get(claim["claim_id"], [])) or "none"), ""])
        lines.extend([
                      "Outcome: " + terminal.get("comparison_status", terminal.get("documentary_status",terminal.get("code",terminal.get("scientific_status") or "unavailable"))), "",
                      "Scientific status: "+cell(terminal.get("scientific_status") or "unassigned")+"; evidence grade: "+cell(terminal.get("evidence_grade") or "unassigned"),""])
        lines.extend(axis_lines(terminal, cell))
        if retry:
            first_attempt = "First attempt stopped by " + cell(retry["fault"]) + ": " + cell(retry["first_attempt"].get("reason", "")) + " "
            lines.extend([first_attempt + ("Re-run once at the end of the run, with the same plan, model and inputs: "
                                           + cell(retry["outcome"]) + "." if retry["status"] == "retried"
                                           else "Not re-run: " + cell(retry["reason"])), ""])
        if fallback:
            lines.extend([("Fallback documentary assessment: no execution evidence was obtained, so a fresh AI session "
                           "judged the claim against the quotes its task design rests on. Its grade D is AI judgment "
                           "only." if fallback["status"] == "assessed"
                           else "No fallback documentary assessment: " + cell(fallback["reason"])), ""])
        if required_grade:
            lines.extend(["Required grade: "+required_grade+"; requirement "+("met" if meets_required else "not met"),""])
        # Every task, counted or not; completeness above covers the counted tasks only.
        lines.extend(["Trials run, every task: "+"; ".join(key+" "+str(value) for key,value in execution_counts.items())+".",""])
        if audit_record:
            justification=audit_record.get("justification",{})
            lines.extend(["Proposed grade: "+cell(audit_record.get("proposed_grade") or "unrecorded")+"; evidence ceiling: "
                          +cell(audit_record.get("evidence_ceiling") or "none")+"; settled: "+cell(audit_record.get("settled_ceiling") or "none")
                          +" after "+str(audit_record.get("critique_rounds",0))+" critique round(s)"
                          +"; ceiling over counted tasks: "+cell(audit_record.get("case_ceiling") or "none")+".",""])
            # Over the counted tasks when a critique judged them, so rejected tasks show here.
            limits=audit_record.get("case_limits",audit_record.get("evidence_limits"))
            if limits:
                lines.extend(["Grade limited by: "+cell(", ".join(limits))+".",""])
            size=rows[-1]["size_limited"]
            if size:
                lines.extend(["Limited by its number of independent tasks, not its source: the source supports "
                              +size["source_supports"]+", but "+str(size["counting"])+" tasks counted, where "
                              +size["source_supports"]+" needs "+str(size["counting_needed"])+".",""])
            for label,field in (("Coverage","coverage"),("Uncertainty","uncertainty"),
                                ("Oracle independence","oracle_independence")):
                lines.extend([label+": "+cell(justification.get(field,"unrecorded")),""])
            if candidate and candidate.get("generator"):
                lines.extend(["Generated input: Python ran the planner's generator (SHA256 "
                              +str(candidate["task_receipts"]["generator_sha256"])+") on each task's arguments; it "
                              "implements the model quoted from "
                              +cell(sources[candidate["generator"]["reference_ref"]]["url"])+": "
                              +cell(candidate["generator"]["model_quote"])+". The reference solution (SHA256 "
                              +str(candidate["task_receipts"]["solver_sha256"])+") passed every output before any trial.",""])
            if audit_record.get("critique"):
                critique=audit_record["critique"]
                lines.extend(["Independent critique supported grade "+cell(critique["supported_grade"] or "none")+":",""])
                lines.extend("- "+cell(finding) for finding in critique["findings"])
                lines.extend("- Objection: "+cell(item) for item in critique["objections"])
                lines.extend("- Task "+cell(item["case_id"])+" not counted ("+cell(item["verdict"])+"): "
                             +cell(item["reason"])+" Suggested replacement: "+cell(item["replacement"])
                             for item in rejected_cases(critique))
                lines.extend("- Coverage gap: "+cell(item) for item in critique.get("coverage_gaps") or [])
                lines.extend("- Departure no task exposes: "+cell(item) for item in critique.get("departures") or [])
                lines.extend("- Task "+cell(item["case_id"])+" gives a rule the claim's sections do not: "
                             +cell(item["criterion_given"])
                             for item in critique.get("case_verdicts") or [] if item.get("criterion_given"))
                lines.append("")
                if critique.get("departures"):
                    lines.extend(["Held below the grade proposed to this critique while it lists a departure no task "
                                  "exposes.",""])
                if work.get("gap_return_ref"):
                    returned=store.get_json(work["gap_return_ref"])
                    kept=returned["candidate_fingerprint"]==audit_record.get("candidate_fingerprint")
                    left=len(critique.get("coverage_gaps") or [])
                    lines.extend(["Returned once for coverage gaps: the critique in round "+str(returned["round"])
                                  +" agreed with the proposed grade but named parts of the claim no task tests. "
                                  +("The planner kept the design, leaving "+str(left)+" open." if kept
                                    else "The planner revised the design."),""])
            else:
                lines.extend(["No independent critique ran for this plan; no grade is assigned.",""])
        if terminal.get("asserted_by")=="planner":
            lines.extend(["This claim was ended by the planner, not by an observed execution failure.",""])
        if tests:
            if terminal.get("fault") and terminal.get("asserted_by") != "planner":
                lines.extend(["A runner fault stopped this claim, so no trial below enters accuracy, status or grade.", ""])
            # A pass inside the tolerance but away from the reference result ("Reading a trial's results").
            off={}
            for case in tests:
                for row in case["outputs"] or []:
                    if row.get("off_reference") is not None:
                        off[case["case_id"]]=max(off.get(case["case_id"],0.0),float(row["off_reference"]))
            if off:
                lines.extend(["Passed on tolerance only, more than 0.5% from the reference solution's result: "
                              +"; ".join(cell(case_id)+" (up to "+format(value,".1%")+")" for case_id,value in off.items())
                              +".",""])
            # One row per trial: the task, its status, and every output that did not pass.
            lines.extend(["| Task | Trial | Status | Outputs not passing (expected; found) | Run problems | Counted |",
                          "| --- | --- | --- | --- | --- | --- |"])
            for case in tests:
                misses = "; ".join(row["field"] + " " + row["status"] + " ("
                                   + (row["expected"] if row["type"] == "number" else json.dumps(row["expected"]))
                                   + "; " + (json.dumps(row["found"]) if row["present"] else "missing") + ")"
                                   for row in case["outputs"] or [] if row["status"] != "pass")
                lines.append("| " + cell(case["case_id"]) + " | " + cell(case["trial"]) + " | "
                             + cell(case["comparison_status"]) + " | "
                             + cell(misses or case.get("results_problem") or "none") + " | "
                             + cell("; ".join(case["run_problems"]) or "none") + " | "
                             + ("yes" if case["counted"] else "no") + " |")
            if any(case["artifacts"] for case in tests):
                from urllib.parse import quote
                from pathlib import Path
                lines.extend(["","Generated files:",""])
                for case in tests:
                    for artifact in case["artifacts"]:
                        lines.append("- Task "+cell(case["case_id"])+", trial "+str(case["trial"])+": ["+cell(artifact["path"]).replace("[","&#91;").replace("]","&#93;")+"]("+quote(Path(artifact["saved_path"]).as_posix(),safe="/:")+"); SHA256 "+artifact["object_ref"])
            if any(case.get("files_not_kept") for case in tests):
                # "Files not kept" in local-tasks.md: past a size or count limit, left in the container.
                lines.extend(["","Files not kept, past the size or count limits:",""])
                for case in tests:
                    for item in case.get("files_not_kept") or []:
                        lines.append("- Task "+cell(case["case_id"])+", trial "+str(case["trial"])+": "+cell(item["path"])+", "+str(item["bytes"])+" bytes")
            lines.extend(["", "Reference provenance:", ""])
            for source in sources.values():
                lines.append("- " + cell(source["url"]) + "; version: " + cell(source["version"]) + "; license: " + cell(source["license"]))
            lines.append("")
        lines.append(cell(terminal["reason"]) if "reason" in terminal else "\n".join("- " + cell(item) for item in terminal.get("limitations", [])))
        if work.get("assessment_ref"):
            assessment=store.get_json(work["assessment_ref"])
            lines.extend(["","Independent documentary assessment (AI judgment):",""])
            lines.extend("- "+cell(finding) for finding in assessment["assessment"]["findings"])
            for citation in assessment["assessment"]["citations"]:
                reference=store.get_json(citation["reference_ref"])
                lines.append("- Source: "+cell(reference["url"])+"; quote: "+cell(citation["quote"]))
        lines.append("")
    if not rows:
        lines.append("No scientific claims were extracted. No subject was executed.")
    document = {"schema_version": 1, "profile": "local", "run_id": state["run_id"], "coverage": coverage,
                "snapshot_ref": state["source_ref"], "manifest_ref": state["manifest_ref"],
                "claims": rows, "verification_complete": True, "overall_scientific_grade": None,
                "synthetic": state["subject_config"]["synthetic"], "subject": state["subject_config"],
                "host_limitations": state["host_limitations"], "generated_at": utc_now()}
    if state.get("local_settings_ref"):
        document["configuration_ref"]=state["local_settings_ref"]
    if state.get("local_catalog_ref"):
        document["catalog_inventory_ref"]=state["local_catalog_ref"]
    if environment:
        document["environment_ref"]=state["local_environment_ref"]
        document["environment"]=environment
    pointer=store.run_dir(state["run_id"])/"workflow-log.json"
    if pointer.exists():
        from .mcp import parse_json
        document["workflow_log"]=parse_json(no_links(pointer).read_bytes())
    state["report_ref"] = keep(store, state, document)
    state["report_markdown_ref"] = store.put(("\n".join(lines) + "\n").encode("utf-8"))
    state["objects"].append(state["report_markdown_ref"])
    state["run_state"] = "completed"
    state["verification_complete"] = True
    state["finished_at"] = utc_now()
    state["completion_reason"] = "local_report_complete"
    state["finalization"] = store.finalize(state)
    return {"outcome": "local_report_written", "report": document,
            "report_json_path": str(store.run_dir(state["run_id"]) / "report-card.json"),
            "report_markdown_path": str(store.run_dir(state["run_id"]) / "report-card.md")}
