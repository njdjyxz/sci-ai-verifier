"""Internal local-profile operations; Claude Code chooses and calls legal steps."""

from html import escape

from .common import Fault, canonical, digest, utc_now
from .ingest import verified_snapshot
from .storage import atomic_write, no_links
from . import local_candidates as catalog

CLAIM_LEGAL = {
    "local_lookup": ["list_local_candidates", "record_local_limitation"],
    "local_discovery": ["fetch_local_reference", "qualify_local_candidate", "select_local_candidate", "record_local_limitation"],
    "local_ready": ["execute_local_claim", "record_local_limitation"],
    "terminal_result": [], "terminal_operational": [],
}
OPERATIONS = ("list_local_candidates", "fetch_local_reference", "qualify_local_candidate",
              "select_local_candidate", "execute_local_claim", "record_local_limitation")


def legal(state):
    if state["run_state"] == "active":
        return sorted({tool for claim in state["claim_states"].values() for tool in CLAIM_LEGAL[claim]})
    return {"created": ["load_submitted_skill"], "source_ready": ["read_snapshot_file", "commit_claim_manifest"],
            "reporting": ["write_report_card"], "completed": [], "incomplete": []}[state["run_state"]]


def schemas(base, obj, string):
    claim = {**base, "claim_id": string(80)}
    case = obj({"case_id": string(80), "input": string(8000), "expected": string(4000),
                "reference_ref": string(64), "source_quote": string(8000), "applicability": string(4000)})
    return {
        "list_local_candidates": obj(claim),
        "fetch_local_reference": obj({**claim, "url": string(4096), "version": string(200), "license": string(2000)}),
        "qualify_local_candidate": obj({**claim, "name": string(200), "scope": string(8000), "method": string(20),
            "limitations": string(8000), "cases": {"type": "array", "minItems": 3, "maxItems": 12, "items": case}}),
        "select_local_candidate": obj({**claim, "candidate_ref": string(64), "applicability": string(8000)}),
        "execute_local_claim": obj(claim),
        "record_local_limitation": obj({**claim, "code": string(100), "reason": string(8000)}),
    }


def keep(store, state, value):
    catalog.safe_payload(value)
    key = store.put_json(value)
    if key not in state["objects"]:
        state["objects"].append(key)
    return key


def pin_candidate(store, state, key):
    candidate = store.get_json(key)
    if candidate.get("status") != "qualified_local" or candidate.get("method_version") != catalog.METHOD_VERSION:
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
    check = catalog.qualify({name: candidate[name] for name in ("name", "scope", "method", "limitations", "cases")}, refs)
    if check["status"] != "qualified_local":
        raise Fault("candidate_integrity", "Candidate no longer passes qualification.", fatal=True)
    if key not in state["objects"]:
        state["objects"].append(key)
    return candidate


def limitation(store, state, claim_id, code, reason, receipts=None):
    work = state["local_work"].setdefault(claim_id, {})
    record = {"kind": "local-limitation", "claim_id": claim_id, "code": code, "reason": reason,
              "scientific_status": None, "evidence_grade": None, "receipts": receipts or []}
    work["outcome_ref"] = keep(store, state, record)
    state["claim_states"][claim_id] = "terminal_operational"
    return {"outcome": code, "limitation": record}


def operate(store, state, name, args, subject):
    if name == "write_report_card":
        return report(store, state)
    claim_id = args["claim_id"]
    if name not in CLAIM_LEGAL.get(state["claim_states"].get(claim_id), []):
        raise Fault("illegal_claim_transition", "This operation is not legal for this local claim.")
    work = state["local_work"].setdefault(claim_id, {"reference_refs": [], "candidate_refs": []})
    if name == "record_local_limitation":
        return limitation(store, state, claim_id, args["code"], args["reason"])
    if name == "list_local_candidates":
        found = catalog.candidates(store)
        work["lookup_ref"] = keep(store, state, {"candidates": found, "created_at": utc_now()})
        state["claim_states"][claim_id] = "local_discovery"
        return {"outcome": "local_candidates_returned" if found else "discovery_required", "candidates": found}
    if name == "fetch_local_reference":
        raw, text = catalog.fetch_public(args["url"])
        raw_ref = store.put(raw)
        state["objects"].append(raw_ref)
        reference = {"kind": "local-reference", "url": args["url"], "raw_ref": raw_ref, "text": text,
                     "version": args["version"], "license": args["license"], "retrieved_at": utc_now(),
                     "authority": "not_independently_attested", "redistribution": "not_authorized"}
        key = keep(store, state, reference)
        work["reference_refs"].append(key)
        return {"outcome": "reference_fetched", "reference_ref": key, "untrusted_reference": reference}
    if name == "qualify_local_candidate":
        proposal = {key: args[key] for key in ("name", "scope", "method", "limitations", "cases")}
        refs = {key: store.get_json(key) for key in work["reference_refs"]}
        candidate = catalog.qualify(proposal, refs)
        key = keep(store, state, candidate)
        catalog.save_candidate(store, candidate)
        work["candidate_refs"].append(key)
        return {"outcome": candidate["status"], "candidate_ref": key, "candidate": candidate}
    if name == "select_local_candidate":
        key = args["candidate_ref"]
        allowed = {value["candidate_ref"] for value in store.get_json(work["lookup_ref"])["candidates"]}
        if key not in allowed | set(work["candidate_refs"]):
            raise Fault("candidate_not_returned", "Select a candidate returned by this claim's lookup or qualification.")
        candidate = pin_candidate(store, state, key)
        work["candidate_ref"] = key
        work["selection_ref"] = keep(store, state, {"candidate_ref": key, "applicability": args["applicability"],
             "snapshot_ref": state["source_ref"], "subject_config": state["subject_config"],
             "method_version": catalog.METHOD_VERSION, "trials_per_case": 1, "claim_id": claim_id})
        state["claim_states"][claim_id] = "local_ready"
        return {"outcome": "local_plan_fixed", "candidate": candidate, "selection_ref": work["selection_ref"]}
    return execute(store, state, claim_id, subject)


def execute(store, state, claim_id, subject):
    from .scientific import implementation_bytes
    if digest(implementation_bytes()) != state["local_method_ref"]:
        return limitation(store, state, claim_id, "method_changed", "Runtime code changed after bootstrap; start a new verification.")
    work = state["local_work"][claim_id]
    candidate = pin_candidate(store, state, work["candidate_ref"])
    if subject.identity != state["subject_config"]:
        return limitation(store, state, claim_id, "subject_identity_changed", "Restart with the originally pinned subject settings.")
    # Stable ordinal avoids repeating the 70-character claim hash in Windows
    # paths; the full claim/selection identity remains inside every receipt.
    claim_directory = f"claim-{sorted(state['claim_states']).index(claim_id) + 1:03}"
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
    if state["subject_calls_used"] + len(candidate["cases"]) > 64:
        return limitation(store, state, claim_id, "subject_budget_exhausted", "The 64-call run limit would be exceeded.")
    snapshot = verified_snapshot(store, state)
    source = [{"path": entry["path"], "content": store.get(entry["digest"]).decode("utf-8")}
              for entry in snapshot["files"] if entry["encoding"] == "utf-8"]
    if len(source) != len(snapshot["files"]) or sum(len(item["content"].encode("utf-8")) for item in source) > 128*1024:
        return limitation(store, state, claim_id, "unsupported_subject", "Local v1 requires at most 128 KiB of text-only skill files.")
    receipts, observations = [], []
    for index, case in enumerate(candidate["cases"], 1):
        request = {"kind": "local-subject-request", "snapshot_ref": state["source_ref"],
                   "selection_ref": work["selection_ref"], "case_id": case["case_id"], "input": case["input"],
                   "subject": state["subject_config"], "created_at": utc_now()}
        request_ref = keep(store, state, request)
        atomic_write(directory / f"{index:03}-request.json", canonical(request))
        receipts.append(request_ref)
        state["subject_calls_used"] += 1
        try:
            response = subject.observe(source=source, case_input={"input": case["input"]},
                                       config=state["subject_config"], timeout_seconds=120)
            catalog.safe_payload(response)
            if (not isinstance(response, dict) or not isinstance(response.get("text"), str) or len(response["text"].encode("utf-8")) > 16384
                    or response.get("invocation_verified") is not True or not response.get("response_id")):
                raise Fault("subject_response_invalid", "Subject response or explicit skill invocation is incomplete.")
        except (Fault, OSError) as error:
            code = error.code if isinstance(error, Fault) else "subject_unavailable"
            return limitation(store, state, claim_id, code, "Subject execution did not return a complete verified observation. No retry was made.", receipts)
        response = {**response, "case_id": case["case_id"], "request_ref": request_ref}
        response_ref = keep(store, state, response)
        atomic_write(directory / f"{index:03}-response.json", canonical(response))
        receipts.append(response_ref)
        observations.append({"case_id": case["case_id"], "request_ref": request_ref, "response_ref": response_ref,
                             "comparison_status": catalog.compare(candidate["method"], response["text"], case["expected"])})
    result = {"kind": "local-comparison", "claim_id": claim_id, "candidate_ref": work["candidate_ref"],
              "selection_ref": work["selection_ref"], "observations": observations, "receipts": receipts,
              "comparison_status": "invalid" if any(row["comparison_status"] == "invalid" for row in observations)
              else "pass" if all(row["comparison_status"] == "pass" for row in observations) else "fail",
              "scientific_status": None, "evidence_grade": None, "synthetic": subject.identity["synthetic"],
              "limitations": candidate["qualification_limitations"] + [candidate["limitations"]]}
    work["result_ref"] = keep(store, state, result)
    state["claim_states"][claim_id] = "terminal_result"
    return {"outcome": "local_comparison_complete", "result": result}


def report(store, state):
    def cell(value):
        return escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")

    claims = store.get_json(state["manifest_ref"])["claims"]
    rows = []
    lines = ["# Local skill verification", "", "SYNTHETIC FIXTURE RUN" if state["subject_config"]["synthetic"]
             else "Personal/local reference comparisons", "",
             "Scientific status and evidence grade are unassigned. Local candidate qualification is mechanical.", ""]
    for claim in claims:
        work = state["local_work"][claim["claim_id"]]
        terminal = store.get_json(work.get("result_ref") or work["outcome_ref"])
        candidate = store.get_json(work["candidate_ref"]) if work.get("candidate_ref") else None
        responses = [store.get_json(key) for key in terminal["receipts"]]
        answers = {item["case_id"]: item for item in responses if item.get("request_ref") and "text" in item}
        tests, sources = [], {}
        if candidate:
            for case in candidate["cases"]:
                reference = store.get_json(case["reference_ref"])
                sources[case["reference_ref"]] = {key: reference[key] for key in ("url", "version", "license", "raw_ref", "retrieved_at", "authority", "redistribution")}
                observed = answers.get(case["case_id"])
                tests.append({"case_id": case["case_id"], "input": case["input"], "expected": case["expected"],
                              "observed": observed["text"] if observed else None,
                              "comparison_status": catalog.compare(candidate["method"], observed["text"], case["expected"]) if observed else "not_obtained",
                              "reference_ref": case["reference_ref"], "reference_quote": case["source_quote"],
                              "applicability": case["applicability"],
                              "session_id": observed.get("session_id") if observed else None,
                              "observed_model_ids": observed.get("observed_model_ids", []) if observed else []})
        rows.append({"claim": claim, "record": terminal, "tests": tests, "references": sources,
                     "candidate_scope": candidate["scope"] if candidate else None})
        lines.extend(["## " + cell(claim["statement"]), "",
                      "Outcome: " + terminal.get("comparison_status", terminal.get("code", "unavailable")), ""])
        if tests:
            lines.extend(["| Input | Expected | Observed | Comparison |", "| --- | --- | --- | --- |"])
            for case in tests:
                lines.append("| " + " | ".join(cell(case[key]) for key in ("input", "expected", "observed", "comparison_status")) + " |")
            lines.extend(["", "Reference provenance:", ""])
            for source in sources.values():
                lines.append("- " + cell(source["url"]) + "; version: " + cell(source["version"]) + "; license: " + cell(source["license"]))
            lines.append("")
        lines.append(cell(terminal["reason"]) if "reason" in terminal else "\n".join("- " + cell(item) for item in terminal.get("limitations", [])))
        lines.append("")
    if not rows:
        lines.append("No scientific claims were extracted. No subject was executed.")
    document = {"schema_version": 1, "profile": "local", "run_id": state["run_id"],
                "snapshot_ref": state["source_ref"], "manifest_ref": state["manifest_ref"],
                "claims": rows, "verification_complete": True, "overall_scientific_grade": None,
                "synthetic": state["subject_config"]["synthetic"], "subject": state["subject_config"],
                "host_limitations": state["host_limitations"], "generated_at": utc_now()}
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
