"""Internal local-profile operations; Claude Code chooses and calls legal steps."""

from html import escape
import base64
import re

from .common import Fault, canonical, digest, utc_now
from .ingest import verified_snapshot
from .storage import atomic_write, no_links
from . import local_candidates as catalog

CLAIM_LEGAL = {
    "local_lookup": ["list_local_candidates", "record_local_limitation"],
    "local_discovery": ["fetch_local_reference", "load_local_resource", "fetch_local_asset", "qualify_local_candidate", "qualify_local_evaluator", "select_local_candidate", "assess_local_documentary", "record_local_unverified", "record_local_limitation"],
    # An audited executable plan is not abandoned by assertion. Every real failure
    # during execution is recorded by Python with the cause it observed.
    "local_ready": ["execute_local_claim"],
    "local_documentary":["fetch_local_reference","load_local_resource","fetch_local_asset","assess_local_documentary","record_local_unverified","record_local_limitation"],
    "terminal_result": [], "terminal_operational": [],
}
OPERATIONS = ("list_local_candidates", "fetch_local_reference", "qualify_local_candidate",
              "select_local_candidate", "execute_local_claim", "record_local_limitation", "load_local_resource", "fetch_local_asset", "qualify_local_evaluator", "assess_local_documentary", "record_local_unverified")
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


def legal(state):
    if state["run_state"] == "active":
        return sorted({tool for claim in state["claim_states"].values() for tool in CLAIM_LEGAL[claim]})
    return {"created": ["load_submitted_skill"], "source_ready": ["read_snapshot_file", "commit_claim_manifest"],
            "reporting": ["write_report_card"], "completed": [], "incomplete": []}[state["run_state"]]


def schemas(base, obj, string):
    from .local_science import PLANNER_JUSTIFICATION
    from .local_candidates import MINIMUM_OPTIONS

    def choice(values, maximum=100):
        return {"type": "string", "minLength": 1, "maxLength": maximum, "enum": list(values)}

    claim = {**base, "claim_id": string(80)}
    # `options` belongs to the choice method: present them in `input`, and `expected` is
    # the 1-based number of one. Optional, so open numeric and token cases are unchanged.
    fields = {"case_id": string(80), "input": string(8000), "expected": string(4000),
              "reference_ref": string(64), "source_quote": string(8000), "applicability": string(4000),
              "options": {"type": "array", "minItems": MINIMUM_OPTIONS, "maxItems": 9, "items": string(4000)},
              # Only in a `mixed` design, where each case names its own installed method.
              "method": choice(("exact", "numeric", "choice"), 20)}
    case = obj(fields, required=[key for key in fields if key not in ("options", "method")])
    return {
        "list_local_candidates": obj(claim),
        "fetch_local_reference": obj({**claim, "url": string(4096), "version": string(200), "license": string(2000)}),
        "load_local_resource":obj({**claim,"resource_name":string(80),"format":string(20)}),
        "fetch_local_asset":obj({**claim,"url":string(4096),"sha256":string(64),"format":string(20),
                                 "version":string(200),"license":string(2000),"units":string(2000)}),
        "qualify_local_evaluator":obj({**claim,"specification_json":string(200000)}),
        "assess_local_documentary":obj({**claim,"evidence":{"type":"array","minItems":1,"maxItems":8,
                "items":obj({"reference_ref":string(64),"quote":string(6000)})},"limitations":string(8000)}),
        "record_local_unverified":obj({**claim,"search_account":string(8000),"missing_evidence":string(8000)}),
        "qualify_local_candidate": obj({**claim, "name": string(200), "scope": string(8000), "method": string(20),
            "limitations": string(8000), "cases": {"type": "array", "minItems": 3, "maxItems": 12, "items": case}}),
        "select_local_candidate": obj({**claim, "candidate_ref": string(64), "applicability": string(8000),
            "target_grade": choice(("A", "B", "C"), 1),
            **{key: string(4000) for key in PLANNER_JUSTIFICATION}}),
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
    from . import local_evaluators
    if candidate.get("status") != "qualified_local" or candidate.get("method_version") not in {catalog.METHOD_VERSION,local_evaluators.METHOD_VERSION}:
        raise Fault("candidate_not_qualified", "Select an installed, mechanically qualified local candidate.")
    refs = {}
    for case in candidate["cases"]:
        ref = case["reference_ref"]
        resource = store.get_json(ref)
        store.get(resource["raw_ref"])
        refs[ref] = resource
        for item in (ref, resource["raw_ref"]):
            if item not in state["objects"]:
                state["objects"].append(item)
    if candidate["method_version"]==local_evaluators.METHOD_VERSION:
        spec=local_evaluators.specification(candidate)
        local_evaluators.validate_spec(spec,refs)
        if candidate["specification_ref"]!=digest(canonical(spec)) or not all(item["passed"] for item in candidate["controls_receipts"]):
            raise Fault("candidate_integrity","Evaluator specification or control receipts changed.",fatal=True)
        check=candidate
    else:
        check = catalog.qualify({name: candidate[name] for name in ("name", "scope", "method", "limitations", "cases")}, refs)
    if check["status"] != "qualified_local":
        raise Fault("candidate_integrity", "Candidate no longer passes qualification.", fatal=True)
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
    if name=="qualify_local_evaluator":
        from .local_evaluators import qualify
        from .mcp import parse_json
        try:
            spec=parse_json(args["specification_json"])
        except (ValueError,UnicodeError,RecursionError):
            raise Fault("evaluator_spec_invalid","Supply a valid bounded JSON specification.") from None
        candidate=qualify(spec,{key:store.get_json(key) for key in work["reference_refs"]},settings_for(store,state),log=getattr(subject,"log",None))
        key=keep(store,state,candidate)
        catalog.save_candidate(store,candidate)
        work["candidate_refs"].append(key)
        return {"outcome":candidate["status"],"candidate_ref":key,"candidate":candidate}
    if name == "qualify_local_candidate":
        proposal = {key: args[key] for key in ("name", "scope", "method", "limitations", "cases")}
        refs = {key: store.get_json(key) for key in work["reference_refs"]}
        candidate = catalog.qualify(proposal, refs)
        key = keep(store, state, candidate)
        catalog.save_candidate(store, candidate)
        work["candidate_refs"].append(key)
        return {"outcome": candidate["status"], "candidate_ref": key, "candidate": candidate}
    if name == "select_local_candidate":
        return select(store, state, claim_id, work, args, subject)
    return execute(store, state, claim_id, subject)


def claim_record(store, state, claim_id):
    return next(item for item in store.get_json(state["manifest_ref"])["claims"]
                if item["claim_id"] == claim_id)


def prior_objections(history):
    """Earlier reviewers' concerns, without their grades, so a revision can be checked.

    Grades are withheld deliberately. A new reviewer told that the last one said C has
    an easy answer available, which is the anchoring the fresh session exists to avoid.
    The concerns themselves are what a revision has to answer, so those carry forward,
    including every case an earlier reviewer did not count: without it, the next reviewer
    cannot tell whether the replacements answer what was wrong with the cases they replaced.
    They come from Python's stored audits, so the planner cannot restate them.
    """
    from .local_science import rejected_cases
    found = []
    for record in history:
        critique = record.get("critique") or {}
        concerns = list(critique.get("objections", []))
        concerns += ["An earlier version's case " + item["case_id"] + " was not counted (" + item["verdict"]
                     + "): " + item["reason"] + " Suggested replacement: " + item["replacement"]
                     for item in rejected_cases(critique)]
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


def critique_packet(claim, candidate, references, args, ceiling, limits, trials, objections=()):
    """The bounded packet a fresh session sees: the design and its facts, no planning."""
    from .documentary import CRITIQUE_RUBRIC
    from .local_science import PLANNER_JUSTIFICATION, answer_form

    def clip(text, size=800):
        return text if len(text) <= size else text[:size] + " [truncated]"

    sources = {}
    for item in references.values():
        sources[item["url"]] = {"url": item["url"], "version": item["version"], "license": item["license"],
                                "origin": item.get("origin", "unrecorded")}
    return {"claim": {key: claim[key] for key in ("statement", "scope", "expected_behavior")},
            "proposed_grade": args["target_grade"], "rubric": CRITIQUE_RUBRIC,
            "prior_objections": [clip(item, 1000) for item in objections],
            "evidence": {"method": candidate["method"], "method_version": candidate["method_version"],
                         "candidate_scope": clip(candidate["scope"]),
                         "candidate_limitations": clip(candidate["limitations"]),
                         "case_count": len(candidate["cases"]), "trials_per_case": trials,
                         "absolute_tolerance": candidate.get("absolute_tolerance"),
                         "references": [sources[key] for key in sorted(sources)],
                         # Every case, because each one gets a verdict. Showing the first six
                         # left cases seven to twelve of a larger design unreviewed.
                         # Inputs get a wider clip and options travel separately: a choice
                         # lists its options at the end of its input and its expected value is
                         # only an index, so a clipped input left the verdict unjudgeable.
                         "cases": [{"case_id": case["case_id"], "answer_form": answer_form(candidate, case),
                                    "input": clip(case["input"], 2000),
                                    **({"options": [clip(option, 400) for option in case["options"]]}
                                       if case.get("options") else {}),
                                    "expected": clip(case["expected"]),
                                    "source_quote": clip(case["source_quote"]),
                                    "applicability": clip(case["applicability"])}
                                   for case in candidate["cases"]]},
            "justification": {key: clip(args[key], 2000) for key in PLANNER_JUSTIFICATION},
            "python_checked": {"evidence_ceiling": ceiling, "evidence_limits": limits,
                               "note": "Python already verified that every expected answer is quoted exactly "
                                       "from the pinned reference bytes. Judge whether that evidence is "
                                       "fit for this claim at the proposed grade. Python counts cases and "
                                       "cannot weigh them: a function name, a scientific value and a fact "
                                       "the claim never states are the same shape once quoted, so whether "
                                       "each case counts is decided here, in case_verdicts. Python then "
                                       "recomputes the ceiling over the cases you count, under "
                                       "rubric.case_requirements, and returns every rejected case with your "
                                       "described replacement to the planner."}}


def select(store, state, claim_id, work, args, subject):
    """Freeze one plan and settle its grade: propose, critique, then fix or ask for a revision."""
    from .local_science import (MAX_ROUNDS, PLANNER_JUSTIFICATION, REPLACEMENT_ROUNDS, audit, case_gap,
                                counted_cases, environment_digest, evidence_ceiling, fingerprint,
                                proposal_problem, rejected_cases)
    key = args["candidate_ref"]
    allowed = {value["candidate_ref"] for value in store.get_json(work["lookup_ref"])["candidates"]}
    if key not in allowed | set(work["candidate_refs"]):
        raise Fault("candidate_not_returned", "Select a candidate returned by this claim's lookup or qualification.")
    candidate = pin_candidate(store, state, key)
    settings = settings_for(store, state)
    references = {case["reference_ref"]: store.get_json(case["reference_ref"]) for case in candidate["cases"]}
    trials = settings["trial_count"]
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
    # the cases the critique counted, and its grade, so it is clamped to the ceiling. A
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
    critique = None
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
                           + ". Change the evidence to justify more, or propose " + accepted + "."}
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
                               "and the cases they did not count. A justification field needs only a new "
                               "proposal; a case's applicability or the design's scope or limitations "
                               "needs a revised candidate."}
        # Measured before the critique and never shown to it: what a subject knowing only the
        # claim answers ("No more" in evidence-rubric.md). A generated evaluator's free output
        # needs the sandbox to be scored, so only installed methods are asked.
        probe = None
        if candidate["method"] != "python":
            from .documentary import claim_probe
            # Earlier rounds' answers travel on their critiques, so an unchanged case is not asked again.
            earlier = {item["case_ref"]: item for record in history
                       for item in ((record.get("critique") or {}).get("claim_probe") or {}).get("cases", [])
                       if item["outcome"] != "unmeasured"}
            probe = claim_probe(subject, claim, candidate, cache=earlier)
        packet = critique_packet(claim, candidate, references, args, ceiling, limits, trials,
                                 prior_objections(history))
        work["critique_packet_ref"] = keep(store, state, packet)
        try:
            from .documentary import critique as run_critique
            critique = run_critique(subject, packet)
        except (Fault, OSError, AttributeError) as error:
            detail = " " + str(error) if isinstance(error, Fault) else ""
            return limitation(store, state, claim_id, getattr(error, "code", "critic_unavailable"),
                              "The independent grade critique did not complete." + detail + " This is an "
                              "operational failure, not an absence of scientific evidence.", asserted_by="runtime")
        if probe is not None:
            # Python's measurement travels with the critique it settles against, beside its verdicts.
            critique = {**critique, "claim_probe": probe}
        work["critique_ref"] = keep(store, state, critique)
    work["candidate_ref"] = key
    selection = {"candidate_ref": key, "applicability": args["applicability"],
                 "target_grade": args["target_grade"],
                 **{name: args[name] for name in PLANNER_JUSTIFICATION},
                 "snapshot_ref": state["source_ref"], "subject_config": state["subject_config"],
                 "source_digest": store.get_json(state["source_ref"])["digest"],
                 "environment_digest": environment_digest(settings, state["subject_config"]),
                 "method_version": candidate["method_version"], "trials_per_case": trials,
                 "claim_id": claim_id}
    work["selection_ref"] = keep(store, state, selection)
    audit_record = audit(candidate, claim, settings, selection, references, critique=critique, rounds=rounds)
    work["audit_ref"] = keep(store, state, audit_record)
    work["negotiation_refs"].append(work["audit_ref"])
    if not audit_record["mechanically_accepted"]:
        return {"outcome": "local_audit_rejected", "audit": audit_record}
    # Two revisions may be spent replacing cases the critique did not count. A third
    # critique that still rejects cases settles the grade the counting cases support.
    rejected = rejected_cases(critique) if critique and not accepting else []
    replacements_used = sum(1 for record in history if rejected_cases(record.get("critique")))
    replacements_spent = bool(rejected) and replacements_used >= REPLACEMENT_ROUNDS
    if (critique and not accepting and audit_record["settled_ceiling"] != args["target_grade"]
            and rounds < MAX_ROUNDS and not replacements_spent):
        # Strengthen the evidence and propose the new ceiling, or accept this grade.
        # On the last round the settled grade is fixed instead of offered.
        return {"outcome": "local_grade_revision_required", "audit": audit_record,
                "supported_grade": critique["supported_grade"],
                "settled_grade": audit_record["settled_ceiling"],
                "objections": critique["objections"],
                "required_revisions": critique["required_revisions"],
                "case_replacements": rejected,
                "rounds_remaining": MAX_ROUNDS - rounds,
                "replacement_rounds_remaining": REPLACEMENT_ROUNDS - replacements_used - bool(rejected),
                "case_gap": case_gap(candidate, counted_cases(critique), args["target_grade"],
                                     critique["supported_grade"])}
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


def compare(candidate,case,text,settings,subject,artifacts=None):
    if candidate["method"]!="python":
        return catalog.compare(catalog.case_method(candidate,case),text,case["expected"])
    from .local_evaluators import score
    return score(candidate,case,text,settings,log=getattr(subject,"log",None),artifacts=artifacts)["status"]


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
            refs.update(case["reference_ref"] for case in store.get_json(work["candidate_ref"])["cases"])
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
    receipts, observations = [], []
    for index, (case,trial) in enumerate(((case,trial) for case in candidate["cases"] for trial in range(1,trials+1)),1):
        request = {"kind": "local-subject-request", "snapshot_ref": state["source_ref"],
                   "selection_ref": work["selection_ref"], "case_id": case["case_id"], "input": case["input"],
                   "subject": state["subject_config"], "trial":trial,"created_at": utc_now()}
        request_ref = keep(store, state, request)
        atomic_write(directory / f"{index:03}-request.json", canonical(request))
        receipts.append(request_ref)
        state["subject_calls_used"] += 1
        try:
            response = subject.observe(source=source, case_input={"input": case["input"]},
                                       config=state["subject_config"], timeout_seconds=settings["subject_timeout_seconds"])
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
                reason = ("Trial " + str(trial) + " of case " + case["case_id"] + " reached this verifier's per-trial limit of "
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
        try:
            evaluation_artifacts=[{"path":item["path"],"base64":base64.b64encode(store.get(item["object_ref"])).decode()} for item in artifacts] if candidate["method"]=="python" else None
            status=compare(candidate,case,response["text"],settings,subject,evaluation_artifacts)
        except Fault as error:
            return limitation(store,state,claim_id,error.code,"The evaluator did not complete. Saved subject observations were not retried.",receipts)
        scored={"case_id":case["case_id"],"trial":trial,"request_ref":request_ref,"response_ref":response_ref,"comparison_status":status,"model_ids":models}
        score_ref=keep(store,state,scored)
        receipts.append(score_ref)
        atomic_write(directory/f"{index:03}-score.json",canonical(scored))
        observations.append(scored)
    # Cases the critique did not count ran and stay in the receipts, but a case measuring
    # something other than the claim cannot pass or fail it. An audit written before case
    # verdicts existed counted every case.
    from .local_science import decide, rejected_cases
    counted = audit_record.get("counted_cases")
    counted = set(counted if counted is not None else (case["case_id"] for case in candidate["cases"]))
    cases = [case for case in candidate["cases"] if case["case_id"] in counted]
    scored = [row for row in observations if row["case_id"] in counted]
    result = {"kind": "local-comparison", "claim_id": claim_id, "candidate_ref": work["candidate_ref"],
              "selection_ref": work["selection_ref"], "observations": observations, "receipts": receipts,
              "comparison_status": "no_counted_cases" if not scored
              else "invalid" if any(row["comparison_status"] == "invalid" for row in scored)
              else "pass" if all(row["comparison_status"] == "pass" for row in scored) else "fail",
              "uncounted_cases": [{key: item[key] for key in ("case_id", "verdict", "reason")}
                                  for item in rejected_cases(audit_record.get("critique"))],
              "scientific_status": None, "evidence_grade": None, "synthetic": subject.identity["synthetic"],
              "limitations": candidate["qualification_limitations"] + [candidate["limitations"]]}
    result.update(decide(audit_record,scored,cases,trials,synthetic=subject.identity["synthetic"]))
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
# One minute per trial is three times the slowest mean of run 3dc02567; five more for the report.
RETRY_SECONDS_PER_TRIAL = 60
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
    """Each distinct reference quote a candidate's cases were keyed to, in case order.

    Qualification already proved every one exact, so a packet built from them needs no planner.
    """
    evidence = []
    for case in store.get_json(candidate_ref)["cases"]:
        if not case.get("reference_ref") or not case.get("source_quote"):
            continue
        reference = store.get_json(case["reference_ref"])
        item = {"reference_ref": case["reference_ref"], "quote": case["source_quote"], "url": reference["url"],
                "version": reference["version"], "license": reference["license"]}
        if item not in evidence and case["source_quote"] in reference["text"]:
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
    from .documentary import ASSESSOR_SHAPE_ATTEMPTS, ASSESSOR_TIMEOUT_SECONDS
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
            reason = "The claim has no qualified candidate whose reference quotes could be assessed."
        elif (deadline and float(deadline) - time.time()
              < ASSESSOR_SHAPE_ATTEMPTS * ASSESSOR_TIMEOUT_SECONDS + RETRY_REPORT_SECONDS):
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
    def cell(value):
        return escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")

    claims = store.get_json(state["manifest_ref"])["claims"]
    rows = []
    lines = ["# Local skill verification", "", "SYNTHETIC FIXTURE RUN" if state["subject_config"]["synthetic"]
             else "Personal/local reference comparisons", "",
             "Scientific status and evidence grade are separate from operational completion. Mechanical qualification alone is ungraded.", ""]
    for claim in claims:
        work = state["local_work"][claim["claim_id"]]
        terminal = store.get_json(work.get("result_ref") or work["outcome_ref"])
        candidate = store.get_json(work["candidate_ref"]) if work.get("candidate_ref") else None
        responses = [store.get_json(key) for key in terminal["receipts"]]
        answers = {(item["case_id"],item.get("trial",1)): item for item in responses if item.get("request_ref") and "text" in item}
        tests, sources = [], {}
        audit_record = store.get_json(work["audit_ref"]) if work.get("audit_ref") else None
        counted = (audit_record or {}).get("counted_cases")
        if candidate:
            trials=store.get_json(work["selection_ref"])["trials_per_case"] if work.get("selection_ref") else 1
            for case,trial in ((case,trial) for case in candidate["cases"] for trial in range(1,trials+1)):
                reference = store.get_json(case["reference_ref"])
                sources[case["reference_ref"]] = {key: reference[key] for key in ("url", "version", "license", "raw_ref", "retrieved_at", "authority", "redistribution")}
                observed = answers.get((case["case_id"],trial))
                tests.append({"case_id": case["case_id"],"trial":trial, "input": case["input"], "expected": case["expected"],
                              "artifacts":observed.get("artifacts",[]) if observed else [],
                              "observed": observed["text"] if observed else None,
                              "comparison_status": next((item["comparison_status"] for item in responses if item.get("case_id")==case["case_id"] and item.get("trial",1)==trial and "comparison_status" in item),"not_obtained"),
                              "reference_ref": case["reference_ref"], "reference_quote": case["source_quote"],
                              "applicability": case["applicability"],
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
                     "retry": retry, "fallback": fallback,
                     "required_grade":required_grade,"meets_required_grade":meets_required,
                     "audit":audit_record,
                     "documentary_assessment":store.get_json(work["assessment_ref"]) if work.get("assessment_ref") else None,
                     "candidate_scope": candidate["scope"] if candidate else None})
        lines.extend(["## " + cell(claim["statement"]), "",
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
                           "judged the claim against the reference quotes its planned cases were keyed to. Its grade D "
                           "is AI judgment only." if fallback["status"] == "assessed"
                           else "No fallback documentary assessment: " + cell(fallback["reason"])), ""])
        if required_grade:
            lines.extend(["Required grade: "+required_grade+"; requirement "+("met" if meets_required else "not met"),""])
        # Every tested case, counted or not; completeness above covers the counted cases only.
        lines.extend(["Trials run, every tested case: "+"; ".join(key+" "+str(value) for key,value in execution_counts.items())+".",""])
        if work.get("audit_ref"):
            # `.get` throughout: a run saved before the grade negotiation existed must stay
            # readable, and reporting an old record as "unrecorded" beats refusing to report.
            settled=store.get_json(work["audit_ref"])
            justification=settled.get("justification",{})
            lines.extend(["Proposed grade: "+cell(settled.get("proposed_grade") or "unrecorded")+"; evidence ceiling: "
                          +cell(settled.get("evidence_ceiling") or "none")+"; settled: "+cell(settled.get("settled_ceiling") or "none")
                          +" after "+str(settled.get("critique_rounds",0))+" critique round(s)"
                          +("; ceiling over counted cases: "+cell(settled.get("case_ceiling") or "none") if "case_ceiling" in settled else "")
                          +".",""])
            # Over the counted cases when a critique judged them, so rejected cases show here.
            limits=settled.get("case_limits",settled.get("evidence_limits"))
            if limits:
                lines.extend(["Grade limited by: "+cell(", ".join(limits))+".",""])
            for label,field in (("Coverage","coverage"),("Uncertainty","uncertainty"),
                                ("Oracle independence","oracle_independence")):
                lines.extend([label+": "+cell(justification.get(field,"unrecorded")),""])
            if settled.get("critique"):
                lines.extend(["Independent critique supported grade "
                              +cell(settled["critique"]["supported_grade"] or "none")+":",""])
                lines.extend("- "+cell(finding) for finding in settled["critique"]["findings"])
                lines.extend("- Objection: "+cell(item) for item in settled["critique"]["objections"])
                from .local_science import rejected_cases
                # In case order: the critique's rejections, and Python's, marked, for cases the
                # claim-only answers missed.
                lines.extend("- Case "+cell(item["case_id"])+" not counted ("+cell(item["verdict"])
                             +(", from the claim-only answers" if item.get("source")=="claim_probe" else "")+"): "
                             +cell(item["reason"])+" Suggested replacement: "+cell(item["replacement"])
                             for item in rejected_cases(settled["critique"]))
                probe=settled["critique"].get("claim_probe")
                if probe:
                    outcomes=[item["outcome"] for item in probe["cases"]]
                    lines.append("- Claim-only answers: "+str(outcomes.count("reached"))+" of "+str(len(outcomes))
                                 +" cases reached their key from the claim alone"
                                 +"".join("; "+str(outcomes.count(name))+" "+name for name in ("missed","unmeasured")
                                          if outcomes.count(name))+".")
                lines.append("")
            else:
                lines.extend(["No independent critique ran for this plan; no grade is assigned.",""])
        if terminal.get("asserted_by")=="planner":
            lines.extend(["This claim was ended by the planner, not by an observed execution failure.",""])
        if tests:
            if terminal.get("fault") and terminal.get("asserted_by") != "planner":
                lines.extend(["A runner fault stopped this claim, so no trial below enters accuracy, status or grade.", ""])
            lines.extend(["| Input | Expected | Observed | Comparison | Case | Trial | Counted |", "| --- | --- | --- | --- | --- | --- | --- |"])
            for case in tests:
                lines.append("| " + " | ".join(cell(case[key]) for key in ("input", "expected", "observed", "comparison_status","case_id","trial"))
                             + " | " + ("yes" if case["counted"] else "no") + " |")
            if any(case["artifacts"] for case in tests):
                from urllib.parse import quote
                from pathlib import Path
                lines.extend(["","Generated files:",""])
                for case in tests:
                    for artifact in case["artifacts"]:
                        lines.append("- Case "+cell(case["case_id"])+", trial "+str(case["trial"])+": ["+cell(artifact["path"]).replace("[","&#91;").replace("]","&#93;")+"]("+quote(Path(artifact["saved_path"]).as_posix(),safe="/:")+"); SHA256 "+artifact["object_ref"])
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
    document = {"schema_version": 1, "profile": "local", "run_id": state["run_id"],
                "snapshot_ref": state["source_ref"], "manifest_ref": state["manifest_ref"],
                "claims": rows, "verification_complete": True, "overall_scientific_grade": None,
                "synthetic": state["subject_config"]["synthetic"], "subject": state["subject_config"],
                "host_limitations": state["host_limitations"], "generated_at": utc_now()}
    if state.get("local_settings_ref"):
        document["configuration_ref"]=state["local_settings_ref"]
    if state.get("local_catalog_ref"):
        document["catalog_inventory_ref"]=state["local_catalog_ref"]
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
