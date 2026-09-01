from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from sci_ai_verifier.adapters.claude import (
    ClaudeClaimExtractor,
    ClaudeConfigurationError,
    ClaudeResponseError,
)
from sci_ai_verifier.claims import ClaimExtractionError, extract_claim_manifest
from sci_ai_verifier.ingest import SkillInputError, load_skill


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sci-ai-verifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser(
        "extract-claims",
        help="Extract a draft scientific claim manifest from a submitted skill.",
    )
    extract.add_argument(
        "skill",
        help="A UTF-8 skill file, or a directory containing a top-level SKILL.md.",
    )
    extract.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_MODEL"),
        help="Company-approved Claude model ID; defaults to CLAUDE_MODEL.",
    )
    extract.add_argument(
        "--output",
        type=Path,
        help="Manifest path; defaults to .verifier/runs/<run-id>/claim-manifest.json.",
    )
    extract.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of an explicitly selected output file.",
    )
    return parser


def _default_output(source_sha256: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{source_sha256[:8]}"
    return Path(".verifier") / "runs" / run_id / "claim-manifest.json"


def _write_manifest(path: Path, payload: dict[str, object], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists; choose another path or use --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command != "extract-claims":
        parser.error(f"Unsupported command: {args.command}")
    if not args.model:
        parser.error("--model is required when CLAUDE_MODEL is not set.")

    try:
        document = load_skill(args.skill)
        extractor = ClaudeClaimExtractor(model=args.model)
        manifest = extract_claim_manifest(document, extractor)
        output = (args.output or _default_output(document.sha256)).resolve()
        if output == Path(document.path):
            raise ValueError("Output path cannot overwrite the submitted skill file.")
        _write_manifest(output, manifest.to_dict(), force=args.force)
    except (
        ClaimExtractionError,
        ClaudeConfigurationError,
        ClaudeResponseError,
        FileExistsError,
        SkillInputError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    review_count = sum(claim.needs_human_review for claim in manifest.claims)
    print(f"Wrote {len(manifest.claims)} draft claim(s) to {output}")
    if review_count:
        print(f"Human review required for {review_count} claim(s).")
    return 0

