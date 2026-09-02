from __future__ import annotations

import unittest

from sci_ai_verifier.cli import _parser


class CliTests(unittest.TestCase):
    def test_skill_is_the_only_positional_argument(self) -> None:
        args = _parser().parse_args(["C:/skills/example"])

        self.assertEqual(args.skill, "C:/skills/example")


if __name__ == "__main__":
    unittest.main()
