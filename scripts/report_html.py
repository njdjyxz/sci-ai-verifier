"""Write a finished run's HTML page from its records and notes (src/sci_ai_verifier/report_html.py).

    python scripts/report_html.py RUN [--notes FILE] [--out FILE] [--workspace DIR]

RUN is a run ID, a unique prefix of one, or a run directory. By default the notes are read from,
and the page is written to, `.verifier/reports/<run ID>.notes.json` and `.html`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sci_ai_verifier.report_html import main  # noqa: E402

if __name__ == "__main__":
    main()
