from __future__ import annotations

import unittest

from sci_ai_verifier.claims import ClaimExtractionError, extract_claim_manifest
from sci_ai_verifier.models import DraftClaim, ExtractionResponse, SkillDocument


class FakeExtractor:
    def __init__(self, source_quote: str) -> None:
        self.source_quote = source_quote

    def extract(self, document: SkillDocument) -> ExtractionResponse:
        return ExtractionResponse(
            claims=(
                DraftClaim(
                    statement="The skill calculates monoisotopic mass from a molecular formula.",
                    scope="Small molecules represented by molecular formula",
                    expected_behavior="Return the corresponding monoisotopic mass.",
                    source_quote=self.source_quote,
                    needs_human_review=False,
                    review_reason="",
                ),
            ),
            notes="",
            provider="anthropic",
            model="company-approved-claude-model",
            response_id="msg_test",
        )


class ClaimManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = SkillDocument(
            path="C:/skills/mass/SKILL.md",
            name="SKILL.md",
            content="Calculate the monoisotopic mass from a molecular formula.",
            sha256="a" * 64,
        )

    def test_python_assigns_ids_after_extraction(self) -> None:
        manifest = extract_claim_manifest(
            self.document,
            FakeExtractor("Calculate the monoisotopic mass from a molecular formula."),
        )

        self.assertEqual(manifest.status, "draft")
        self.assertRegex(manifest.manifest_id, r"^cmf-[0-9a-f]{12}$")
        self.assertRegex(manifest.claims[0].claim_id, r"^clm-[0-9a-f]{12}$")
        self.assertEqual(manifest.claims[0].status, "draft")

    def test_untraceable_source_quote_is_rejected(self) -> None:
        with self.assertRaisesRegex(ClaimExtractionError, "not present"):
            extract_claim_manifest(self.document, FakeExtractor("A quote Claude invented."))


if __name__ == "__main__":
    unittest.main()

