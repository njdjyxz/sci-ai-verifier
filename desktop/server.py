"""Entry point shared by the source checkout and packaged desktop extension."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if not (ROOT / "src").is_dir():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from sci_ai_verifier.__main__ import main

if __name__ == "__main__":
    main()
