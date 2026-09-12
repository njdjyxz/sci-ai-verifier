"""Internal local-profile operations; Claude Code chooses and calls legal steps."""

from html import escape
import base64

from .common import Fault, canonical, digest, utc_now
from .ingest import verified_snapshot
from .storage import atomic_write, no_links
from . import local_candidates as catalog

CLAIM_LEGAL = {
    "local_lookup": ["list_local_candidates", "record_local_limitation"],
    "local_discovery": ["fetch_local_reference", "load_local_resource", "fetch_local_asset", "qualify_local_candidate", "qualify_local_evaluator", "select_local_candidate", "assess_local_documentary", "record_local_unverified", "record_local_limitation"],
    "local_ready": ["execute_local_claim", "record_local_limitation"],
    "local_documentary":["fetch_local_reference","load_local_resource","fetch_local_asset","assess_local_documentary","record_local_unverified","record_local_limitation"],
    "terminal_result": [], "terminal_operational": [],
}
OPERATIONS = ("list_local_candidates", "fetch_local_reference", "qualify_local_candidate",
              "select_local_candidate", "execute_local_claim", "record_local_limitation", "load_local_resource", "fetch_local_asset", "qualify_local_evaluator", "assess_local_documentary", "record_local_unverified")


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
        "load_local_resource":obj({**claim,"resource_name":string(80),"format":string(20)}),
        "fetch_local_asset":obj({**claim,"url":string(4096),"sha256":string(64),"format":string(20),
                                 "version":string(200),"license":string(2000),"units":string(2000)}),
        "qualify_local_evaluator":obj({**claim,"specification_json":string(200000)}),
        "assess_local_documentary":obj({**claim,"evidence":{"type":"array","minItems":1,"maxItems":8,
                "items":obj({"reference_ref":string(64),"quote":string(6000)})},"limitations":string(8000)}),
        "record_local_unverified":obj({**claim,"search_account":string(8000),"missing_evidence":string(8000)}),
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


def limitation(store, state, claim_id, code, reason, receipts=None):
    work = state["local_work"].setdefault(claim_id, {})
    previous=[]
    if work.get("result_ref"):
        work["comparison_ref"]=work.pop("result_ref")
        previous=store.get_json(work["comparison_ref"]).get("receipts",[])
    record = {"kind": "local-limitation", "claim_id": claim_id, "code": code, "reason": reason,
              "scientific_status": None, "evidence_grade": None, "receipts":list(dict.fromkeys([*previous,*(receipts or [])]))}
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
                     "authority": "not_independently_attested", "redistribution": "not_authorized"}
        key = keep(store, state, reference)
        work["reference_refs"].append(key)
        return {"outcome": "reference_fetched", "reference_ref": key, "untrusted_reference": reference}
    if name in {"load_local_resource","fetch_local_asset"}:
        from .local_resources import inspect_resource,import_configured
        settings=settings_for(store,state)
        if name=="load_local_resource":
            raw,metadata=import_configured(settings,args["resource_name"])
            metadata={**{key:value for key,value in metadata.items() if key!="path"},"url":"operator-resource:"+args["resource_name"]}
        else:
            check_reference_host(settings,args["url"])
            raw,_=catalog.fetch_bytes(args["url"],max_bytes=settings["max_file_bytes"])
            if digest(raw)!=args["sha256"]:
                raise Fault("resource_changed","Downloaded asset differs from the requested digest.")
            metadata={key:args[key] for key in ("url","version","license","units")}
        inspection=inspect_resource(raw,args["format"],settings)
        raw_ref=store.put(raw)
        if raw_ref not in state["objects"]:
            state["objects"].append(raw_ref)
        reference={"kind":"local-reference",**metadata,**inspection,"text":inspection.get("text",""),
                   "raw_ref":raw_ref,"retrieved_at":utc_now(),"authority":"not_independently_attested","redistribution":"not_authorized"}
        key=keep(store,state,reference)
        work["reference_refs"].append(key)
        return {"outcome":"reference_fetched","reference_ref":key,"untrusted_reference":reference}
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
        key = args["candidate_ref"]
        allowed = {value["candidate_ref"] for value in store.get_json(work["lookup_ref"])["candidates"]}
        if key not in allowed | set(work["candidate_refs"]):
            raise Fault("candidate_not_returned", "Select a candidate returned by this claim's lookup or qualification.")
        candidate = pin_candidate(store, state, key)
        work["candidate_ref"] = key
        from .local_science import environment_digest
        work["selection_ref"] = keep(store, state, {"candidate_ref": key, "applicability": args["applicability"],
             "snapshot_ref": state["source_ref"], "subject_config": state["subject_config"],
             "source_digest":store.get_json(state["source_ref"])["digest"],
             "environment_digest":environment_digest(settings_for(store,state),state["subject_config"]),
             "method_version": candidate["method_version"], "trials_per_case": settings_for(store,state)["trial_count"], "claim_id": claim_id})
        from .local_science import audit
        claim=next(item for item in store.get_json(state["manifest_ref"])["claims"] if item["claim_id"]==claim_id)
        audit_record=audit(candidate,claim,settings_for(store,state),store.get_json(work["selection_ref"]))
        work["audit_ref"]=keep(store,state,audit_record)
        if not audit_record["mechanically_accepted"]:
            return {"outcome":"local_audit_rejected","audit":audit_record}
        state["claim_states"][claim_id] = "local_ready"
        return {"outcome": "local_plan_fixed", "candidate": candidate, "selection_ref": work["selection_ref"],"audit":audit_record}
    return execute(store, state, claim_id, subject)


def settings_for(store,state):
    from .local_config import load_configuration
    return store.get_json(state["local_settings_ref"]) if state.get("local_settings_ref") else {**load_configuration(),"trial_count":1,"max_subject_calls":64,"documentary_assessment":False}


def check_reference_host(settings,url):
    from urllib.parse import urlsplit
    if settings["allowed_reference_hosts"] and urlsplit(url).hostname not in settings["allowed_reference_hosts"]:
        raise Fault("resource_not_authorized","Reference host is outside the operator's configured list.")


def compare(candidate,case,text,settings,subject,artifacts=None):
    if candidate["method"]!="python":
        return catalog.compare(candidate["method"],text,case["expected"])
    from .local_evaluators import score
    return score(candidate,case,text,settings,log=getattr(subject,"log",None),artifacts=artifacts)["status"]


def documentary_step(store,state,claim_id,name,args,subject):
    from .documentary import assess,RUBRIC,RUBRIC_REF
    from .scientific import implementation_bytes
    if digest(implementation_bytes())!=state["local_method_ref"] or subject.identity!=state["subject_config"]:
        return limitation(store,state,claim_id,"assessment_identity_changed","Runtime or assessor settings changed after bootstrap.")
    work=state["local_work"][claim_id]
    if not work.get("lookup_ref"):
        raise Fault("catalog_lookup_required","Check available evaluators before concluding this claim.")
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
        claim=next(item for item in store.get_json(state["manifest_ref"])["claims"] if item["claim_id"]==claim_id)
        packet={"claim":{key:claim[key] for key in ("statement","scope","expected_behavior")},"evidence":evidence,"rubric":RUBRIC,"limitations":args["limitations"]}
        packet_ref=keep(store,state,packet)
        work["documentary_packet_ref"]=packet_ref
        marker=no_links(store.run_dir(state["run_id"])/("assessor-"+str(sorted(state["claim_states"]).index(claim_id))+".json"))
        if marker.exists():
            return limitation(store,state,claim_id,"interrupted_assessment","A prior assessment request exists and was not automatically replayed.",retained["receipts"])
        atomic_write(marker,canonical({"packet_ref":packet_ref,"created_at":utc_now()}))
        try:
            response=assess(subject,packet)
        except (Fault,OSError,AttributeError) as error:
            return limitation(store,state,claim_id,getattr(error,"code","assessor_unavailable"),"The independent assessment did not complete; this is not missing scientific evidence.",retained["receipts"])
        assessment_ref=keep(store,state,response)
        work["assessment_ref"]=assessment_ref
        approved=bool(settings_for(store,state)["documentary_review"]) and not state["subject_config"]["synthetic"]
        record={**retained,"kind":"local-documentary","assessment_ref":assessment_ref,"packet_ref":packet_ref,
                "scientific_status":response["assessment"]["status"] if approved else None,"evidence_grade":"D" if approved else None,
                "documentary_status":response["assessment"]["status"],"ai_involvement":{"orchestration":True,"evidence_generation":True,"verdict":True},
                "limitations":["Documentary consistency only; scientific performance remains unverified.",
                    response["assessment"]["limitations"],"Independent rubric authorization recorded." if approved else "Independent rubric authorization absent; assessment is ungraded."]}
    work["result_ref"]=keep(store,state,record)
    state["claim_states"][claim_id]="terminal_result"
    return {"outcome":"local_documentary_complete" if name=="assess_local_documentary" else "local_unverified_recorded","result":record}


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
    settings=settings_for(store,state)
    trials=store.get_json(work["selection_ref"])["trials_per_case"]
    if work.get("audit_ref"):
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
            return limitation(store, state, claim_id, code, "Subject execution did not return a complete verified observation. No retry was made.", receipts)
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
            if "observed_models_ref" not in work:
                work["observed_models_ref"]=keep(store,state,models)
            elif store.get_json(work["observed_models_ref"])!=models:
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
    result = {"kind": "local-comparison", "claim_id": claim_id, "candidate_ref": work["candidate_ref"],
              "selection_ref": work["selection_ref"], "observations": observations, "receipts": receipts,
              "comparison_status": "invalid" if any(row["comparison_status"] == "invalid" for row in observations)
              else "pass" if all(row["comparison_status"] == "pass" for row in observations) else "fail",
              "scientific_status": None, "evidence_grade": None, "synthetic": subject.identity["synthetic"],
              "limitations": candidate["qualification_limitations"] + [candidate["limitations"]]}
    if work.get("audit_ref"):
        from .local_science import decide
        result.update(decide(store.get_json(work["audit_ref"]),observations,candidate["cases"],trials,synthetic=subject.identity["synthetic"]))
    work["result_ref"] = keep(store, state, result)
    needs_documentary=not result["evidence_grade"] and settings["documentary_assessment"]
    state["claim_states"][claim_id] = "local_documentary" if needs_documentary else "terminal_result"
    return {"outcome": "local_documentary_required" if needs_documentary else "local_comparison_complete", "result": result}


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
                              "session_id": observed.get("session_id") if observed else None,
                              "observed_model_ids": observed.get("observed_model_ids", []) if observed else []})
        execution_counts={"planned":len(tests),"attempted":sum(item.get("kind")=="local-subject-request" for item in responses),
                          "obtained":len(answers),"evaluated":sum("comparison_status" in item for item in responses),
                          "invalid":sum(item.get("comparison_status")=="invalid" for item in responses),"missing":len(tests)-len(answers)}
        required_grade=settings_for(store,state).get("minimum_grade")
        achieved=terminal.get("evidence_grade")
        meets_required=None if required_grade is None else bool(achieved in {"A","B","C","D"} and "ABCD".index(achieved)<= "ABCD".index(required_grade))
        rows.append({"claim": claim, "record": terminal, "tests": tests, "references": sources,"execution_counts":execution_counts,
                     "required_grade":required_grade,"meets_required_grade":meets_required,
                     "audit":store.get_json(work["audit_ref"]) if work.get("audit_ref") else None,
                     "documentary_assessment":store.get_json(work["assessment_ref"]) if work.get("assessment_ref") else None,
                     "candidate_scope": candidate["scope"] if candidate else None})
        lines.extend(["## " + cell(claim["statement"]), "",
                      "Outcome: " + terminal.get("comparison_status", terminal.get("documentary_status",terminal.get("code",terminal.get("scientific_status") or "unavailable"))), "",
                      "Scientific status: "+cell(terminal.get("scientific_status") or "unassigned")+"; evidence grade: "+cell(terminal.get("evidence_grade") or "unassigned"),""])
        if required_grade:
            lines.extend(["Required grade: "+required_grade+"; requirement "+("met" if meets_required else "not met"),""])
        lines.extend(["Trials: "+"; ".join(key+" "+str(value) for key,value in execution_counts.items())+".",""])
        if work.get("audit_ref"):
            review=store.get_json(work["audit_ref"]).get("review")
            if review:
                lines.extend(["Reviewed scope: "+cell(review["scope"]),"","Coverage: "+cell(review["coverage"]),"",
                              "Uncertainty: "+cell(review["uncertainty"]),"","Review provenance: "+cell(review["provenance"]),""])
            else:
                lines.extend(["Independent scientific review: absent. Coverage and uncertainty are not scientifically approved.",""])
        if tests:
            lines.extend(["| Input | Expected | Observed | Comparison | Case | Trial |", "| --- | --- | --- | --- | --- | --- |"])
            for case in tests:
                lines.append("| " + " | ".join(cell(case[key]) for key in ("input", "expected", "observed", "comparison_status","case_id","trial")) + " |")
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
