from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sci_ai_verifier.models import (
    Claim,
    ClaimManifest,
    ClaimTypeDecision,
    TypeAssignmentResponse,
)
from sci_ai_verifier.routing import route_claims


class FakeAssigner:
    def __init__(self, decision: ClaimTypeDecision) -> None:
        self.decision = decision

    def assign_claim_types(self, claims, claim_types) -> TypeAssignmentResponse:
        return TypeAssignmentResponse(
            decisions=(self.decision,),
            provider="anthropic",
            model="company-approved-claude-model",
            response_id="msg-routing",
        )


def claim_manifest() -> ClaimManifest:
    return ClaimManifest(
        schema_version="0.1",
        manifest_id="cmf-test",
        created_at="2026-09-01T00:00:00+00:00",
        source_path="C:/skills/SKILL.md",
        source_name="SKILL.md",
        source_sha256="a" * 64,
        extraction_provider="anthropic",
        extraction_model="company-approved-claude-model",
        extraction_response_id="msg-extraction",
        claims=(
            Claim(
                claim_id="clm-test",
                statement="The skill calculates monoisotopic mass.",
                scope="Small molecules",
                expected_behavior="Return a monoisotopic mass.",
                source_quote="Calculates monoisotopic mass.",
                report_note="",
            ),
        ),
    )


class RoutingTests(unittest.TestCase):
    def test_missing_type_is_created_and_routes_to_no_evaluator(self) -> None:
        decision = ClaimTypeDecision(
            claim_id="clm-test",
            existing_claim_type_id="",
            proposed_name="Monoisotopic mass from formula",
            proposed_definition="Calculate monoisotopic mass from a molecular formula.",
            proposed_inputs=("molecular formula",),
            proposed_outputs=("monoisotopic mass",),
            proposed_boundaries="Excludes average molecular weight.",
            report_note="Automatically created claim type.",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry = Path(temporary_directory)
            result = route_claims(
                claim_manifest(),
                FakeAssigner(decision),
                claim_type_index_path=registry / "claim_types.json",
                evaluator_registry_path=registry / "evaluators.json",
            )

            saved_index = json.loads(
                (registry / "claim_types.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_index["revision"], 1)
            self.assertEqual(saved_index["claim_types"][0]["status"], "provisional")
            self.assertEqual(result.routes[0].claim_type_source, "created")
            self.assertEqual(result.routes[0].route_status, "evaluator_not_found")

            repeated = route_claims(
                claim_manifest(),
                FakeAssigner(decision),
                claim_type_index_path=registry / "claim_types.json",
                evaluator_registry_path=registry / "evaluators.json",
            )
            repeated_index = json.loads(
                (registry / "claim_types.json").read_text(encoding="utf-8")
            )
            self.assertEqual(repeated_index["revision"], 1)
            self.assertEqual(len(repeated_index["claim_types"]), 1)
            self.assertEqual(repeated.routes[0].claim_type_source, "existing")

    def test_existing_type_with_registered_evaluator_is_found(self) -> None:
        decision = ClaimTypeDecision(
            claim_id="clm-test",
            existing_claim_type_id="ct-existing",
            proposed_name="",
            proposed_definition="",
            proposed_inputs=(),
            proposed_outputs=(),
            proposed_boundaries="",
            report_note="",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry = Path(temporary_directory)
            (registry / "claim_types.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "revision": 1,
                        "claim_types": [
                            {
                                "claim_type_id": "ct-existing",
                                "name": "Monoisotopic mass from formula",
                                "definition": "Calculate monoisotopic mass from a formula.",
                                "inputs": ["molecular formula"],
                                "outputs": ["monoisotopic mass"],
                                "boundaries": "Excludes average molecular weight.",
                                "status": "active",
                                "created_at": "2026-09-01T00:00:00+00:00",
                                "created_from_claim_id": "clm-origin",
                                "created_by_model": "company-approved-claude-model",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (registry / "evaluators.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "evaluators": [
                            {
                                "evaluator_id": "mass-reference-v1",
                                "claim_type_ids": ["ct-existing"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = route_claims(
                claim_manifest(),
                FakeAssigner(decision),
                claim_type_index_path=registry / "claim_types.json",
                evaluator_registry_path=registry / "evaluators.json",
            )

            self.assertEqual(result.routes[0].claim_type_source, "existing")
            self.assertEqual(result.routes[0].route_status, "evaluator_found")
            self.assertEqual(result.routes[0].evaluator_ids, ("mass-reference-v1",))


if __name__ == "__main__":
    unittest.main()
