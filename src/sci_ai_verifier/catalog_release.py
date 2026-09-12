"""Reviewed local catalog releases. Catalog membership never grants a claim grade."""

import re

from . import __version__
from .common import Fault, canonical, digest, utc_now
from .local_catalog import MAX_BUNDLE, import_bundle
from .mcp import parse_json
from .ingest import SECRET_BYTES


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]{0,5})\.(?:0|[1-9][0-9]{0,5})\.(?:0|[1-9][0-9]{0,5})", value):
        raise ValueError("Use a three-part numeric version.")
    return tuple(map(int, value.split(".")))


def validate(raw, *, compatibility=True):
    """Check release shape and review coverage before any candidate is installed."""
    try:
        if len(raw) > MAX_BUNDLE or SECRET_BYTES.search(raw):
            raise ValueError()
        item = parse_json(raw)
        fields = {"schema_version", "kind", "catalog_id", "version", "minimum_runtime",
                  "maximum_runtime_exclusive", "previous_release_sha256", "bundle_sha256",
                  "bundle", "reviews", "created_at"}
        if not isinstance(item, dict) or set(item) != fields or type(item["schema_version"]) is not int or item["schema_version"] != 1 or item["kind"] != "local-catalog-release":
            raise ValueError()
        if not isinstance(item["catalog_id"], str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,79}", item["catalog_id"]):
            raise ValueError()
        version(item["version"])
        lower, upper = version(item["minimum_runtime"]), version(item["maximum_runtime_exclusive"])
        if lower < (0, 7, 0) or lower >= upper:
            raise ValueError()
        if compatibility and not lower <= version(__version__) < upper:
            raise Fault("catalog_incompatible", "This catalog release requires a different runtime version; existing runs retain their pins.")
        previous = item["previous_release_sha256"]
        if previous is not None and (not isinstance(previous, str) or not re.fullmatch(r"[0-9a-f]{64}", previous)):
            raise ValueError()
        if digest(canonical(item["bundle"])) != item["bundle_sha256"] or not isinstance(item["created_at"], str) or not 1 <= len(item["created_at"]) <= 100:
            raise ValueError()
        refs = item["bundle"]["candidate_refs"]
        if not isinstance(refs, list) or not 1 <= len(refs) <= 100 or any(not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{64}", key) for key in refs) or len(set(refs)) != len(refs):
            raise ValueError()
        reviews = item["reviews"]
        if not isinstance(reviews, list) or len(reviews) != len(refs):
            raise ValueError()
        required = {"candidate_ref", "decision", "reviewer", "reviewed_at", "provenance",
                    "independent", "scope", "coverage", "uncertainty", "redistribution"}
        seen = set()
        for review in reviews:
            if (not isinstance(review, dict) or set(review) != required or review["independent"] is not True
                    or any(not isinstance(review[key], str) or not 1 <= len(review[key]) <= 4000 for key in required - {"independent"})
                    or review["candidate_ref"] not in refs or review["candidate_ref"] in seen
                    or review["decision"] not in {"approved_for_catalog", "retired"}):
                raise ValueError()
            seen.add(review["candidate_ref"])
        return item
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        raise Fault("catalog_release_invalid", "Release shape, exact bundle pin, runtime range or independent review coverage is invalid.") from None


def build(store, bundle_raw, settings, metadata, reviews, *, approved=False, previous_raw=None):
    if not approved:
        raise Fault("promotion_authorization_required", "Inspect the exact candidate bundle and real independent review records, then explicitly authorize catalog promotion.")
    required = {"catalog_id", "version", "minimum_runtime", "maximum_runtime_exclusive"}
    if not isinstance(metadata, dict) or set(metadata) != required:
        raise Fault("catalog_release_invalid", "Provide catalog ID, version and the supported runtime range.")
    item = {"schema_version": 1, "kind": "local-catalog-release", **metadata,
            "previous_release_sha256": digest(previous_raw) if previous_raw is not None else None,
            "bundle_sha256": digest(canonical(parse_json(bundle_raw))), "bundle": parse_json(bundle_raw),
            "reviews": reviews, "created_at": utc_now()}
    raw = canonical(item)
    validate(raw)
    if previous_raw is not None:
        previous = validate(previous_raw, compatibility=False)
        if (previous["catalog_id"] != item["catalog_id"] or version(previous["version"]) >= version(item["version"])
                or not set(previous["bundle"]["candidate_refs"]) <= set(item["bundle"]["candidate_refs"])):
            raise Fault("catalog_release_conflict", "Updates must keep the catalog ID, increase its version and retain previous candidate IDs with explicit retirement decisions.")
    # Requalification is local and may run generated controls in the configured container.
    import_bundle(store, canonical(item["bundle"]), settings)
    return raw


def install(store, raw, settings, *, log=None):
    item = validate(raw)
    receipt = import_bundle(store, canonical(item["bundle"]), settings, log=log)
    receipt.update(release_sha256=digest(raw), catalog_id=item["catalog_id"], version=item["version"],
                   retired_candidate_refs=[review["candidate_ref"] for review in item["reviews"] if review["decision"] == "retired"],
                   scientific_approval_imported=False)
    return receipt
