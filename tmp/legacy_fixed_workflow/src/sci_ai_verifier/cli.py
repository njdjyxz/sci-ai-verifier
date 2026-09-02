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
from sci_ai_verifier.claims import ClaimExtractionError, build_claim_manifest
from sci_ai_verifier.ingest import SkillInputError, load_skill
from sci_ai_verifier.routing import RoutingError, route_claims


def _parser() -> argparse.ArgumentParser:
    """Define the command-line arguments accepted by the verifier."""

    parser = argparse.ArgumentParser(
        prog="sci-ai-verifier",
        description=(
            "Start scientific skill verification. The current implementation builds the "
            "claim manifest, assigns claim types, and checks for registered evaluators."
        ),
    )
    parser.add_argument(
        "skill",
        help="A UTF-8 skill file, or a directory containing a top-level SKILL.md.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_MODEL"),
        help="Company-approved Claude model ID; defaults to CLAUDE_MODEL.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Claim-manifest path; routing.json is written beside it. Defaults to "
            ".verifier/runs/<run-id>/claim-manifest.json."
        ),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("registry"),
        help="Directory containing claim_types.json and evaluators.json.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of an explicitly selected output file.",
    )
    return parser


def _default_output(source_sha256: str) -> Path:
    """Build a unique default output path from the run time and source hash."""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{source_sha256[:8]}"
    return Path(".verifier") / "runs" / run_id / "claim-manifest.json"


def _write_json(path: Path, payload: dict[str, object], *, force: bool) -> None:
    """Write a JSON result atomically without replacing files unless allowed."""

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
    """Run skill ingestion, claim extraction, routing, and result writing."""

    parser = _parser()
    args = parser.parse_args(argv)

    if not args.model:
        parser.error("--model is required when CLAUDE_MODEL is not set.")

    try:
        document = load_skill(args.skill)
        output = (args.output or _default_output(document.sha256)).resolve()
        routing_output = output.with_name("routing.json")
        registry = args.registry.resolve()
        if output == Path(document.path):
            raise ValueError("Output path cannot overwrite the submitted skill file.")
        if output == routing_output:
            raise ValueError("Claim-manifest and routing output paths must be different.")
        for result_path in (output, routing_output):
            if result_path.exists() and not args.force:
                raise FileExistsError(
                    f"Output already exists; choose another path or use --force: {result_path}"
                )

        extractor = ClaudeClaimExtractor(model=args.model)
        manifest = build_claim_manifest(document, extractor)
        routing = route_claims(
            manifest,
            extractor,
            claim_type_index_path=registry / "claim_types.json",
            evaluator_registry_path=registry / "evaluators.json",
        )
        _write_json(output, manifest.to_dict(), force=args.force)
        _write_json(routing_output, routing.to_dict(), force=args.force)
    except (
        ClaimExtractionError,
        ClaudeConfigurationError,
        ClaudeResponseError,
        FileExistsError,
        RoutingError,
        SkillInputError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote a claim manifest with {len(manifest.claims)} claim(s) to {output}")
    found_count = sum(route.route_status == "evaluator_found" for route in routing.routes)
    print(
        f"Wrote routing for {len(routing.routes)} claim(s) to {routing_output}; "
        f"registered evaluators found for {found_count}."
    )
    return 0
