from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SkillDocument:
    path: str
    name: str
    content: str
    sha256: str


@dataclass(frozen=True)
class ExtractedClaim:
    statement: str
    scope: str
    expected_behavior: str
    source_quote: str
    report_note: str

    @classmethod
    def from_mapping(cls, value: Any) -> "ExtractedClaim":
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
    claims: tuple[ExtractedClaim, ...]
    provider: str
    model: str
    response_id: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    scope: str
    expected_behavior: str
    source_quote: str
    report_note: str


@dataclass(frozen=True)
class ClaimManifest:
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
        return asdict(self)
