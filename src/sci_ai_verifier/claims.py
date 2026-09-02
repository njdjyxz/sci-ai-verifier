from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Protocol

from sci_ai_verifier.models import Claim, ClaimManifest, ExtractionResponse, SkillDocument


class ClaimExtractionError(ValueError):
    """Claude's response cannot safely become a claim manifest."""


class ClaimExtractor(Protocol):
    def extract(self, document: SkillDocument) -> ExtractionResponse: ...


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _claim_id(document: SkillDocument, statement: str, scope: str) -> str:
    identity = "\0".join(
        (
            document.sha256,
            _normalized_text(statement).casefold(),
            _normalized_text(scope).casefold(),
        )
    )
    return f"clm-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:12]}"


def build_claim_manifest(
    document: SkillDocument,
    extractor: ClaimExtractor,
) -> ClaimManifest:
    extraction = extractor.extract(document)
    normalized_source = _normalized_text(document.content)
    seen_claims: set[tuple[str, str]] = set()
    claims: list[Claim] = []

    for draft in extraction.claims:
        if _normalized_text(draft.source_quote) not in normalized_source:
            raise ClaimExtractionError(
                "Claude returned a source quote that is not present in the submitted skill: "
                f"{draft.source_quote!r}"
            )

        duplicate_key = (
            _normalized_text(draft.statement).casefold(),
            _normalized_text(draft.scope).casefold(),
        )
        if duplicate_key in seen_claims:
            raise ClaimExtractionError(f"Claude returned a duplicate claim: {draft.statement!r}")
        seen_claims.add(duplicate_key)

        claim_id = _claim_id(document, draft.statement, draft.scope)
        claims.append(
            Claim(
                claim_id=claim_id,
                statement=draft.statement.strip(),
                scope=draft.scope.strip(),
                expected_behavior=draft.expected_behavior.strip(),
                source_quote=draft.source_quote.strip(),
                report_note=draft.report_note.strip(),
            )
        )

    manifest_basis = {
        "source_sha256": document.sha256,
        "claims": [
            {"claim_id": claim.claim_id, "statement": claim.statement, "scope": claim.scope}
            for claim in claims
        ],
    }
    manifest_digest = hashlib.sha256(
        json.dumps(manifest_basis, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    return ClaimManifest(
        schema_version="0.1",
        manifest_id=f"cmf-{manifest_digest[:12]}",
        created_at=datetime.now(timezone.utc).isoformat(),
        source_path=document.path,
        source_name=document.name,
        source_sha256=document.sha256,
        extraction_provider=extraction.provider,
        extraction_model=extraction.model,
        extraction_response_id=extraction.response_id,
        claims=tuple(claims),
    )
