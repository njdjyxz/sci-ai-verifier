from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SkillDocument:
    """Hold submitted skill text together with immutable source metadata."""

    path: str
    name: str
    content: str
    sha256: str


@dataclass(frozen=True)
class ExtractedClaim:
    """Represent one untrusted claim candidate returned by the AI adapter."""

    statement: str
    scope: str
    expected_behavior: str
    source_quote: str
    report_note: str

    @classmethod
    def from_mapping(cls, value: Any) -> "ExtractedClaim":
        """Validate an external mapping and convert it into an extracted claim."""

        if not isinstance(value, dict):
            raise ValueError("Each extracted claim must be a JSON object.")

        required = {
            "statement": str,
            "scope": str,
            "expected_behavior": str,
            "source_quote": str,
            "report_note": str,
        }
        if set(value) != set(required):
            missing = sorted(set(required) - set(value))
            extra = sorted(set(value) - set(required))
            raise ValueError(
                f"Extracted claim fields do not match the schema; missing={missing}, extra={extra}."
            )

        for field_name, field_type in required.items():
            if not isinstance(value[field_name], field_type):
                raise ValueError(f"Claim field '{field_name}' must be {field_type.__name__}.")

        for field_name in ("statement", "scope", "expected_behavior", "source_quote"):
            if not value[field_name].strip():
                raise ValueError(f"Claim field '{field_name}' cannot be empty.")

        return cls(**value)


@dataclass(frozen=True)
class ExtractionResponse:
    """Group extracted claims with the AI response provenance."""

    claims: tuple[ExtractedClaim, ...]
    provider: str
    model: str
    response_id: str


@dataclass(frozen=True)
class ClaimType:
    """Describe a reusable category of scientific claims in the shared index."""

    claim_type_id: str
    name: str
    definition: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    boundaries: str
    status: str
    created_at: str
    created_from_claim_id: str
    created_by_model: str

    @classmethod
    def from_mapping(cls, value: Any) -> "ClaimType":
        """Validate a registry mapping and convert it into a claim type."""

        required = {
            "claim_type_id": str,
            "name": str,
            "definition": str,
            "inputs": list,
            "outputs": list,
            "boundaries": str,
            "status": str,
            "created_at": str,
            "created_from_claim_id": str,
            "created_by_model": str,
        }
        if not isinstance(value, dict) or set(value) != set(required):
            raise ValueError("Claim-type entry does not match the index schema.")
        for field_name, field_type in required.items():
            if not isinstance(value[field_name], field_type):
                raise ValueError(f"Claim-type field '{field_name}' must be {field_type.__name__}.")
        if not all(isinstance(item, str) and item.strip() for item in value["inputs"]):
            raise ValueError("Claim-type inputs must be nonempty strings.")
        if not all(isinstance(item, str) and item.strip() for item in value["outputs"]):
            raise ValueError("Claim-type outputs must be nonempty strings.")
        for field_name in ("claim_type_id", "name", "definition", "status"):
            if not value[field_name].strip():
                raise ValueError(f"Claim-type field '{field_name}' cannot be empty.")
        return cls(
            claim_type_id=value["claim_type_id"],
            name=value["name"],
            definition=value["definition"],
            inputs=tuple(value["inputs"]),
            outputs=tuple(value["outputs"]),
            boundaries=value["boundaries"],
            status=value["status"],
            created_at=value["created_at"],
            created_from_claim_id=value["created_from_claim_id"],
            created_by_model=value["created_by_model"],
        )


@dataclass(frozen=True)
class ClaimTypeDecision:
    """Record the AI choice to reuse a claim type or propose a new one."""

    claim_id: str
    existing_claim_type_id: str
    proposed_name: str
    proposed_definition: str
    proposed_inputs: tuple[str, ...]
    proposed_outputs: tuple[str, ...]
    proposed_boundaries: str
    report_note: str

    @classmethod
    def from_mapping(cls, value: Any) -> "ClaimTypeDecision":
        """Validate an external routing mapping and convert it into a decision."""

        required = {
            "claim_id": str,
            "existing_claim_type_id": str,
            "proposed_name": str,
            "proposed_definition": str,
            "proposed_inputs": list,
            "proposed_outputs": list,
            "proposed_boundaries": str,
            "report_note": str,
        }
        if not isinstance(value, dict) or set(value) != set(required):
            raise ValueError("Claim-type decision does not match the response schema.")
        for field_name, field_type in required.items():
            if not isinstance(value[field_name], field_type):
                raise ValueError(
                    f"Claim-type decision field '{field_name}' must be {field_type.__name__}."
                )
        for field_name in ("proposed_inputs", "proposed_outputs"):
            if not all(isinstance(item, str) for item in value[field_name]):
                raise ValueError(f"Claim-type decision field '{field_name}' must contain strings.")
        return cls(
            claim_id=value["claim_id"],
            existing_claim_type_id=value["existing_claim_type_id"],
            proposed_name=value["proposed_name"],
            proposed_definition=value["proposed_definition"],
            proposed_inputs=tuple(value["proposed_inputs"]),
            proposed_outputs=tuple(value["proposed_outputs"]),
            proposed_boundaries=value["proposed_boundaries"],
            report_note=value["report_note"],
        )


@dataclass(frozen=True)
class TypeAssignmentResponse:
    """Group claim-type decisions with the AI response provenance."""

    decisions: tuple[ClaimTypeDecision, ...]
    provider: str
    model: str
    response_id: str


@dataclass(frozen=True)
class Claim:
    """Represent one validated atomic claim in the claim manifest."""

    claim_id: str
    statement: str
    scope: str
    expected_behavior: str
    source_quote: str
    report_note: str


@dataclass(frozen=True)
class ClaimManifest:
    """Store validated claims and their source and extraction provenance."""

    schema_version: str
    manifest_id: str
    created_at: str
    source_path: str
    source_name: str
    source_sha256: str
    extraction_provider: str
    extraction_model: str
    extraction_response_id: str
    claims: tuple[Claim, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the manifest into a JSON-serializable dictionary."""

        return asdict(self)


@dataclass(frozen=True)
class EvaluatorRegistration:
    """Associate a registered evaluator with the claim types it supports."""

    evaluator_id: str
    claim_type_ids: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Any) -> "EvaluatorRegistration":
        """Validate a registry mapping and convert it into an evaluator record."""

        if not isinstance(value, dict) or set(value) != {"evaluator_id", "claim_type_ids"}:
            raise ValueError("Evaluator registration does not match the registry schema.")
        if not isinstance(value["evaluator_id"], str) or not value["evaluator_id"].strip():
            raise ValueError("Evaluator ID must be a nonempty string.")
        if not isinstance(value["claim_type_ids"], list) or not all(
            isinstance(item, str) and item.strip() for item in value["claim_type_ids"]
        ):
            raise ValueError("Evaluator claim_type_ids must contain nonempty strings.")
        return cls(value["evaluator_id"], tuple(value["claim_type_ids"]))


@dataclass(frozen=True)
class ClaimRoute:
    """Record the assigned claim type and matching evaluators for one claim."""

    claim_id: str
    claim_type_id: str
    claim_type_source: str
    route_status: str
    evaluator_ids: tuple[str, ...]
    report_note: str


@dataclass(frozen=True)
class RoutingManifest:
    """Store all claim routes with the index and AI provenance used to build them."""

    schema_version: str
    created_at: str
    claim_manifest_id: str
    claim_type_index_revision: int
    claim_type_index_sha256: str
    evaluator_registry_sha256: str
    type_assignment_provider: str
    type_assignment_model: str
    type_assignment_response_id: str
    routes: tuple[ClaimRoute, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the routing manifest into a JSON-serializable dictionary."""

        return asdict(self)
