from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from sci_ai_verifier.models import (
    Claim,
    ClaimManifest,
    ClaimRoute,
    ClaimType,
    ClaimTypeDecision,
    EvaluatorRegistration,
    RoutingManifest,
    TypeAssignmentResponse,
)


class RoutingError(ValueError):
    """The claim-type index, evaluator registry, or route is invalid."""


class ClaimTypeAssigner(Protocol):
    """Define the claim-type assignment behavior required by routing."""

    def assign_claim_types(
        self,
        claims: tuple[Claim, ...],
        claim_types: tuple[ClaimType, ...],
    ) -> TypeAssignmentResponse:
        """Choose an indexed type or propose a new type for every claim."""

        ...


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    """Read a registry object or return the default when the file is absent."""

    if not path.exists():
        return default
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingError(f"Cannot read JSON registry file: {path}") from exc
    if not isinstance(payload, dict):
        raise RoutingError(f"Registry file must contain a JSON object: {path}")
    return payload


def _json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize a registry payload into a consistent UTF-8 representation."""

    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _write_json(path: Path, payload: dict[str, Any]) -> bytes:
    """Write a registry atomically and return the exact bytes that were stored."""

    content = _json_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)
    return content


def _load_claim_types(path: Path) -> tuple[int, tuple[ClaimType, ...]]:
    """Load and validate the claim-type index, bootstrapping an empty index."""

    payload = _read_json(
        path,
        {"schema_version": "1", "revision": 0, "claim_types": []},
    )
    if set(payload) != {"schema_version", "revision", "claim_types"}:
        raise RoutingError("Claim-type index does not match its schema.")
    if payload["schema_version"] != "1":
        raise RoutingError("Unsupported claim-type index schema version.")
    if not isinstance(payload["revision"], int) or payload["revision"] < 0:
        raise RoutingError("Claim-type index revision must be a nonnegative integer.")
    if not isinstance(payload["claim_types"], list):
        raise RoutingError("Claim-type index claim_types must be a list.")
    try:
        claim_types = tuple(ClaimType.from_mapping(item) for item in payload["claim_types"])
    except ValueError as exc:
        raise RoutingError(str(exc)) from exc
    ids = [claim_type.claim_type_id for claim_type in claim_types]
    if len(ids) != len(set(ids)):
        raise RoutingError("Claim-type index contains duplicate IDs.")
    return payload["revision"], claim_types


def _load_evaluators(
    path: Path,
    known_claim_type_ids: set[str],
) -> tuple[tuple[EvaluatorRegistration, ...], dict[str, Any]]:
    """Load evaluators and verify that every referenced claim type exists."""

    payload = _read_json(path, {"schema_version": "1", "evaluators": []})
    if set(payload) != {"schema_version", "evaluators"}:
        raise RoutingError("Evaluator registry does not match its schema.")
    if payload["schema_version"] != "1":
        raise RoutingError("Unsupported evaluator registry schema version.")
    if not isinstance(payload["evaluators"], list):
        raise RoutingError("Evaluator registry evaluators must be a list.")
    try:
        evaluators = tuple(
            EvaluatorRegistration.from_mapping(item) for item in payload["evaluators"]
        )
    except ValueError as exc:
        raise RoutingError(str(exc)) from exc
    evaluator_ids = [evaluator.evaluator_id for evaluator in evaluators]
    if len(evaluator_ids) != len(set(evaluator_ids)):
        raise RoutingError("Evaluator registry contains duplicate evaluator IDs.")
    for evaluator in evaluators:
        unknown_ids = set(evaluator.claim_type_ids) - known_claim_type_ids
        if unknown_ids:
            raise RoutingError(
                f"Evaluator '{evaluator.evaluator_id}' references unknown claim types: "
                f"{sorted(unknown_ids)}"
            )
    return evaluators, payload


def _normalized(value: str) -> str:
    """Collapse whitespace before generating stable claim-type identities."""

    return re.sub(r"\s+", " ", value).strip()


def _new_claim_type_id(decision: ClaimTypeDecision) -> str:
    """Create a deterministic ID from the normalized proposed type definition."""

    basis = {
        "name": _normalized(decision.proposed_name).casefold(),
        "definition": _normalized(decision.proposed_definition).casefold(),
        "inputs": sorted(_normalized(item).casefold() for item in decision.proposed_inputs),
        "outputs": sorted(_normalized(item).casefold() for item in decision.proposed_outputs),
        "boundaries": _normalized(decision.proposed_boundaries).casefold(),
    }
    digest = hashlib.sha256(
        json.dumps(basis, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return f"ct-{digest[:16]}"


def _validate_decision(
    decision: ClaimTypeDecision,
    known_claim_type_ids: set[str],
) -> None:
    """Reject routing decisions that violate existing-type or proposal rules."""

    if decision.existing_claim_type_id:
        if decision.existing_claim_type_id not in known_claim_type_ids:
            raise RoutingError(
                f"Claude selected an unknown claim type: {decision.existing_claim_type_id}"
            )
        if any(
            (
                decision.proposed_name.strip(),
                decision.proposed_definition.strip(),
                decision.proposed_inputs,
                decision.proposed_outputs,
                decision.proposed_boundaries.strip(),
            )
        ):
            raise RoutingError("An existing-type route must leave all proposed fields empty.")
        return

    if not decision.proposed_name.strip() or not decision.proposed_definition.strip():
        raise RoutingError("A new claim type requires a name and definition.")


def route_claims(
    claim_manifest: ClaimManifest,
    assigner: ClaimTypeAssigner,
    *,
    claim_type_index_path: Path,
    evaluator_registry_path: Path,
) -> RoutingManifest:
    """Assign claim types, update the index, and find registered evaluators."""

    revision, original_claim_types = _load_claim_types(claim_type_index_path)
    claim_types = list(original_claim_types)
    type_by_id = {claim_type.claim_type_id: claim_type for claim_type in claim_types}

    if claim_manifest.claims:
        assignment = assigner.assign_claim_types(
            claim_manifest.claims,
            tuple(claim_types),
        )
    else:
        assignment = TypeAssignmentResponse((), "none", "", "")

    decisions = {decision.claim_id: decision for decision in assignment.decisions}
    expected_claim_ids = {claim.claim_id for claim in claim_manifest.claims}
    if set(decisions) != expected_claim_ids or len(decisions) != len(assignment.decisions):
        raise RoutingError("Type assignment must contain exactly one decision per claim.")

    created_type_ids: set[str] = set()
    claim_type_for_claim: dict[str, tuple[str, str, str]] = {}
    timestamp = datetime.now(timezone.utc).isoformat()

    for claim in claim_manifest.claims:
        decision = decisions[claim.claim_id]
        _validate_decision(decision, set(type_by_id))

        if decision.existing_claim_type_id:
            claim_type_id = decision.existing_claim_type_id
            source = "existing"
        else:
            claim_type_id = _new_claim_type_id(decision)
            if claim_type_id in type_by_id:
                source = "existing"
            else:
                claim_type = ClaimType(
                    claim_type_id=claim_type_id,
                    name=decision.proposed_name.strip(),
                    definition=decision.proposed_definition.strip(),
                    inputs=tuple(item.strip() for item in decision.proposed_inputs),
                    outputs=tuple(item.strip() for item in decision.proposed_outputs),
                    boundaries=decision.proposed_boundaries.strip(),
                    status="provisional",
                    created_at=timestamp,
                    created_from_claim_id=claim.claim_id,
                    created_by_model=assignment.model,
                )
                type_by_id[claim_type_id] = claim_type
                claim_types.append(claim_type)
                created_type_ids.add(claim_type_id)
                source = "created"
        claim_type_for_claim[claim.claim_id] = (
            claim_type_id,
            source,
            decision.report_note.strip(),
        )

    new_revision = revision + (1 if created_type_ids else 0)
    claim_type_payload = {
        "schema_version": "1",
        "revision": new_revision,
        "claim_types": [asdict(claim_type) for claim_type in claim_types],
    }

    evaluators, evaluator_payload = _load_evaluators(
        evaluator_registry_path,
        set(type_by_id),
    )
    evaluators_by_type: dict[str, list[str]] = {}
    for evaluator in evaluators:
        for claim_type_id in evaluator.claim_type_ids:
            evaluators_by_type.setdefault(claim_type_id, []).append(evaluator.evaluator_id)

    claim_type_content = _write_json(claim_type_index_path, claim_type_payload)
    evaluator_content = _write_json(evaluator_registry_path, evaluator_payload)

    routes: list[ClaimRoute] = []
    for claim in claim_manifest.claims:
        claim_type_id, source, report_note = claim_type_for_claim[claim.claim_id]
        evaluator_ids = tuple(sorted(evaluators_by_type.get(claim_type_id, [])))
        routes.append(
            ClaimRoute(
                claim_id=claim.claim_id,
                claim_type_id=claim_type_id,
                claim_type_source=source,
                route_status="evaluator_found" if evaluator_ids else "evaluator_not_found",
                evaluator_ids=evaluator_ids,
                report_note=report_note,
            )
        )

    return RoutingManifest(
        schema_version="0.1",
        created_at=datetime.now(timezone.utc).isoformat(),
        claim_manifest_id=claim_manifest.manifest_id,
        claim_type_index_revision=new_revision,
        claim_type_index_sha256=hashlib.sha256(claim_type_content).hexdigest(),
        evaluator_registry_sha256=hashlib.sha256(evaluator_content).hexdigest(),
        type_assignment_provider=assignment.provider,
        type_assignment_model=assignment.model,
        type_assignment_response_id=assignment.response_id,
        routes=tuple(routes),
    )
