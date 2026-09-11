"""Validate semantic assignments and deterministically select declared capabilities."""

from .catalog import pinned
from .common import Fault, canonical, digest

MAX_MATCHES = 16


def save(store, state, routing):
    state["routing_ref"] = store.put_json(routing)
    if state["routing_ref"] not in state["objects"]:
        state["objects"].append(state["routing_ref"])


def list_types(store, state):
    lock, assets = pinned(store, state)
    index = assets["claim_types"]
    routing = {"schema_version": 1, "run_id": state["run_id"],
               "manifest_ref": state["manifest_ref"], "catalog_ref": state["catalog_ref"],
               "index_digest": lock["assets"]["claim_types"], "index_revision": index["revision"],
               "routes": [], "proposed_types": [], "selections": []}
    save(store, state, routing)
    return {"outcome": "claim_type_index_loaded", "index_digest": routing["index_digest"],
            "index_revision": index["revision"], "claim_types": index["claim_types"],
            "payload_trust": "untrusted_payload"}


def assign(store, state, arguments):
    if not state["routing_ref"]:
        raise Fault("index_not_read", "Read the pinned claim-type index first.", ["index_digest"])
    routing = store.get_json(state["routing_ref"])
    manifest = store.get_json(state["manifest_ref"])
    if (arguments["manifest_id"] != manifest["id"]
            or arguments["index_digest"] != routing["index_digest"]):
        raise Fault("stale_routing_parent", "Use the committed manifest and delivered index digest.",
                    ["manifest_id", "index_digest"])
    _, assets = pinned(store, state)
    known = {entry["id"] for entry in assets["claim_types"]["claim_types"]
             if entry["status"] in {"approved", "validated"}}
    claims = {claim["claim_id"] for claim in manifest["claims"]}
    assignments = arguments["assignments"]
    ids = [item["claim_id"] for item in assignments]
    if len(ids) != len(set(ids)) or set(ids) != claims:
        raise Fault("incomplete_assignments", "Assign every accepted claim exactly once.", ["assignments"])
    routes, proposed = [], {}
    for item in assignments:
        type_id, proposal = item["claim_type_id"], item["proposal"]
        if type_id:
            if proposal or type_id not in known:
                raise Fault("unknown_claim_type", "Use one returned active type or a complete proposal.",
                            ["assignments"])
        else:
            fields = {"name", "definition", "inputs", "outputs", "boundaries"}
            if set(proposal) != fields or any(not value.strip() for value in proposal.values()):
                raise Fault("incomplete_type_proposal", "Supply all five nonempty proposed type fields.",
                            ["assignments"])
            type_id = "type-" + digest(canonical(proposal))
            proposed[type_id] = {"id": type_id, **proposal, "status": "provisional", "origin": "runtime"}
        route = {"claim_id": item["claim_id"], "claim_type_id": type_id,
                 "claim_type_source": "created" if proposal else "existing",
                 "index_digest": routing["index_digest"], "index_revision": routing["index_revision"],
                 "report_note": item["report_note"]}
        route["route_id"] = "route-" + digest(canonical(route))
        routes.append(route)
    routing["routes"] = sorted(routes, key=lambda r: r["claim_id"])
    routing["proposed_types"] = [proposed[key] for key in sorted(proposed)]
    save(store, state, routing)
    state["claim_states"] = {key: "capability_selection" for key in state["claim_states"]}
    state["run_state"] = "active"
    return {"outcome": "claim_routes_committed", "routing": routing}


def identity(entry):
    return {"id": entry["id"], "version": entry["version"], "sha256": digest(canonical(entry))}


def select(store, state, arguments):
    routing = store.get_json(state["routing_ref"])
    manifest = store.get_json(state["manifest_ref"])
    claim = next((c for c in manifest["claims"] if c["claim_id"] == arguments["claim_id"]), None)
    route = next((r for r in routing["routes"] if r["claim_id"] == arguments["claim_id"]), None)
    if claim is None or route is None or arguments["route_id"] != route["route_id"]:
        raise Fault("unknown_route", "Use the returned claim and its exact route ID.", ["claim_id", "route_id"])
    if arguments["scope"] != claim["scope"] or arguments["intended_grade"] != state["intended_grade"]:
        raise Fault("selection_parameters_changed", "Scope and target must match the committed claim and run.",
                    ["scope", "intended_grade"])
    lock, assets = pinned(store, state)
    pairs, resolved, kind, missing_runner = [], None, None, False
    pair_count, capability_contracts, runner_contracts = 0, {}, {}
    for grade in "ABCD"["ABCD".index(state["intended_grade"]):]:
        for group, candidate_kind in (("evaluators", "registered"), ("harnesses", "target")):
            for entry in sorted(assets["evaluators"][group], key=lambda e: e["id"]):
                if (entry["status"] not in ({"validated"} if group == "evaluators" else {"approved", "validated"})
                        or route["claim_type_id"] not in entry["claim_type_ids"]
                        or claim["scope"] not in entry["scopes"] or grade not in entry["grades"]):
                    continue
                runners = ([None] if grade == "D" else [runner for runner in
                           assets["subject_runners"]["subject_runners"]
                           if runner["status"] == "validated"
                           and runner["input_interface"] == entry["input_interface"]
                           and runner["output_interface"] == entry["output_interface"]])
                if not runners:
                    missing_runner = True
                for runner in sorted(runners, key=lambda e: e["id"] if e else ""):
                    pair_count += 1
                    if len(pairs) < MAX_MATCHES:
                        pairs.append({"capability": identity(entry),
                                      "subject_runner": identity(runner) if runner else "not_applicable",
                                      "resources": entry["resources"]})
                        capability_contracts[entry["id"]] = entry
                        if runner:
                            runner_contracts[runner["id"]] = runner
            if pairs:
                resolved, kind = grade, candidate_kind
                break
        if pairs:
            break
    if pairs:
        outcome = ("lower_grade_available" if resolved != state["intended_grade"] else
                   "registered_evaluator_available" if kind == "registered" else "generic_harness_available")
    else:
        outcome = "subject_runner_unavailable" if missing_runner else "implementation_required"
    selection = {"claim_id": claim["claim_id"], "route_id": route["route_id"], "revision": 1,
                 "scope": claim["scope"], "intended_grade": state["intended_grade"],
                 "capability_outcome": outcome, "resolved_grade": resolved or "not_applicable",
                 "capability_kind": kind or "not_applicable", "matches": pairs,
                 "compatible_pair_count": pair_count, "matches_truncated": pair_count > MAX_MATCHES,
                 "capability_contracts": list(capability_contracts.values()),
                 "runner_contracts": list(runner_contracts.values()),
                 "catalog_assets": lock["assets"], "operational_outcome_id": None,
                 "downgrade_reason": "No complete compatible pair at a stronger grade." if
                 pairs and resolved != state["intended_grade"] else None,
                 "limitations": ["Catalog capability selection only; no execution or scientific verdict."]}
    if not pairs:
        outcome_record = {"schema_version": 1,
                          "run_id": state["run_id"], "claim_id": claim["claim_id"],
                          "created_at": state["updated_at"], "implementation_version": state["implementation_version"],
                          "scope": "claim", "category": outcome, "reason": "No complete compatible capability pair.",
                          "workflow_state": "capability_selection", "attempted_tool": "find_registered_evaluators",
                          "artifact_refs": list(state["objects"]), "terminal": True,
                          "scientific_status": None, "evidence_grade": None}
        outcome_record["id"] = "outcome-" + digest(canonical(outcome_record))
        key = store.put_json(outcome_record)
        state["objects"].append(key)
        state["operational_refs"].append(key)
        selection["operational_outcome_id"] = outcome_record["id"]
    selection["selection_id"] = "selection-" + digest(canonical(selection))
    state["claim_states"][claim["claim_id"]] = "planning" if pairs else "terminal_operational"
    routing["selections"].append(selection)
    save(store, state, routing)
    return {"outcome": outcome, "selection": selection}
