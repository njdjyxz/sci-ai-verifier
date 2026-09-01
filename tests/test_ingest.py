from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sci_ai_verifier.ingest import SkillInputError, load_skill


class LoadSkillTests(unittest.TestCase):
    def test_directory_resolves_top_level_skill_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_directory = Path(temporary_directory)
            skill_file = skill_directory / "SKILL.md"
            skill_file.write_bytes(b"# Protein skill\n")

            document = load_skill(skill_directory)

            self.assertEqual(document.name, "SKILL.md")
            self.assertEqual(document.content, "# Protein skill\n")
            self.assertEqual(len(document.sha256), 64)

    def test_directory_without_skill_markdown_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(SkillInputError, "top-level SKILL.md"):
                load_skill(temporary_directory)


if __name__ == "__main__":
    unittest.main()
