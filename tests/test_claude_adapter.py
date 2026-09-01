from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from sci_ai_verifier.adapters.claude import ClaudeClaimExtractor
from sci_ai_verifier.models import SkillDocument


class FakeMessages:
    def __init__(self) -> None:
        self.request = None

    def create(self, **request):
        self.request = request
        payload = {
            "claims": [
                {
                    "statement": "The skill calculates monoisotopic mass.",
                    "scope": "Not specified",
                    "expected_behavior": "Return a monoisotopic mass.",
                    "source_quote": "Calculates monoisotopic mass.",
                    "needs_human_review": True,
                    "review_reason": "The supported molecule scope is not specified.",
                }
            ],
            "notes": "One scientific claim found.",
        }
        return SimpleNamespace(
            id="msg_test",
            model="company-approved-claude-model",
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text=json.dumps(payload))],
        )


class ClaudeAdapterTests(unittest.TestCase):
    def test_adapter_requests_structured_output_and_returns_drafts(self) -> None:
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
        self.assertIn("output_config", messages.request)
        self.assertEqual(
            messages.request["output_config"]["format"]["type"],
            "json_schema",
        )


if __name__ == "__main__":
    unittest.main()

