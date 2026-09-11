"""Run from a source checkout without installation or PYTHONPATH configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.__main__ import main

if __name__ == "__main__":
    main()
