from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from sci_ai_verifier.adapters.claude import ClaudeClaimExtractor
from sci_ai_verifier.models import Claim, ClaimType, SkillDocument


class FakeMessages:
    def __init__(self) -> None:
        self.request = None

    def create(self, **request):
        self.request = request
        schema = request["output_config"]["format"]["schema"]
        if "routes" in schema["properties"]:
            payload = {
                "routes": [
                    {
                        "claim_id": "clm-test",
                        "existing_claim_type_id": "ct-test",
                        "proposed_name": "",
                        "proposed_definition": "",
                        "proposed_inputs": [],
                        "proposed_outputs": [],
                        "proposed_boundaries": "",
                        "report_note": "",
                    }
                ]
            }
        else:
            payload = {
                "claims": [
                    {
                        "statement": "The skill calculates monoisotopic mass.",
                        "scope": "Not specified",
                        "expected_behavior": "Return a monoisotopic mass.",
                        "source_quote": "Calculates monoisotopic mass.",
                        "report_note": "The supported molecule scope is not specified.",
                    }
                ],
            }
        return SimpleNamespace(
            id="msg_test",
            model="company-approved-claude-model",
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text=json.dumps(payload))],
        )


class ClaudeAdapterTests(unittest.TestCase):
    def test_adapter_requests_structured_output_and_returns_claims(self) -> None:
        messages = FakeMessages()
        client = SimpleNamespace(messages=messages)
        document = SkillDocument(
            path="C:/skills/SKILL.md",
            name="SKILL.md",
            content="Calculates monoisotopic mass.",
            sha256="b" * 64,
        )

        result = ClaudeClaimExtractor(
            "company-approved-claude-model",
            client=client,
        ).extract(document)

        self.assertEqual(result.provider, "anthropic")
        self.assertEqual(len(result.claims), 1)
        self.assertEqual(
            result.claims[0].report_note,
            "The supported molecule scope is not specified.",
        )
        self.assertIn("output_config", messages.request)
        self.assertEqual(
            messages.request["output_config"]["format"]["type"],
            "json_schema",
        )

    def test_adapter_routes_claims_using_the_index(self) -> None:
        messages = FakeMessages()
        client = SimpleNamespace(messages=messages)
        adapter = ClaudeClaimExtractor("company-approved-claude-model", client=client)
        claim = Claim(
            claim_id="clm-test",
            statement="The skill calculates monoisotopic mass.",
            scope="Small molecules",
            expected_behavior="Return a monoisotopic mass.",
            source_quote="Calculates monoisotopic mass.",
            report_note="",
        )
        claim_type = ClaimType(
            claim_type_id="ct-test",
            name="Monoisotopic mass from formula",
            definition="Calculate monoisotopic mass from a molecular formula.",
            inputs=("molecular formula",),
            outputs=("monoisotopic mass",),
            boundaries="Excludes average molecular weight.",
            status="active",
            created_at="2026-09-01T00:00:00+00:00",
            created_from_claim_id="clm-origin",
            created_by_model="company-approved-claude-model",
        )

        result = adapter.assign_claim_types((claim,), (claim_type,))

        self.assertEqual(result.decisions[0].existing_claim_type_id, "ct-test")
        self.assertIn("claim_type_index", messages.request["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
