"""Build catalog data for review, or activate an exact verified GitHub release."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci_ai_verifier.catalog import ASSETS, bounded_read, fetch_release, manifest_for, verify
from sci_ai_verifier.common import Fault, canonical, digest
from sci_ai_verifier.storage import Store, atomic_write


def build(source, output, version, provenance):
    raw = {name: bounded_read(source / (name + ".json")) for name in ASSETS}
    manifest = canonical(manifest_for(raw, version, provenance))
    verify(manifest, raw)
    for name, data in raw.items():
        atomic_write(output / (name + ".json"), data)
    atomic_write(output / "manifest.json", manifest)
    return {"directory": str(output), "manifest_sha256": digest(manifest),
            "review_status": "building_does_not_establish_review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    local = commands.add_parser("build")
    local.add_argument("--source", type=Path, required=True)
    local.add_argument("--output", type=Path, required=True)
    local.add_argument("--version", required=True)
    local.add_argument("--provenance", required=True)
    fetch = commands.add_parser("fetch")
    fetch.add_argument("--workspace", type=Path, required=True)
    fetch.add_argument("--commit", required=True)
    fetch.add_argument("--manifest-sha256", required=True)
    fetch.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        result = (build(args.source, args.output, args.version, args.provenance)
                  if args.command == "build" else fetch_release(
                      Store(args.workspace), args.commit, args.manifest_sha256, offline=args.offline))
    except (Fault, OSError, KeyError) as error:
        parser.exit(2, f"Catalog operation failed: {error}\n")
    print(canonical(result).decode("utf-8"))


if __name__ == "__main__":
    main()
