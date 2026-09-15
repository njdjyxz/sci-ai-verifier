"""Prepared local catalog releases. Catalog membership never grants a claim grade.

The agent prepares a release with one recorded assessment per candidate and proposes it
through a draft pull request. A person reviews those assessments there and decides by
merging. Nothing in this module treats a recorded assessment as an approval.
"""

import re

from . import __version__
from .common import Fault, canonical, digest, utc_now
from .local_catalog import MAX_BUNDLE, import_bundle

# Version 2 replaced the pre-review independent review records with the preparer's own
# per-candidate assessments, which a reviewer judges on the pull request.
RELEASE_SCHEMA = 2
from .mcp import parse_json
from .ingest import SECRET_BYTES


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]{0,5})\.(?:0|[1-9][0-9]{0,5})\.(?:0|[1-9][0-9]{0,5})", value):
        raise ValueError("Use a three-part numeric version.")
    return tuple(map(int, value.split(".")))


def validate(raw, *, compatibility=True):
    """Check release shape and assessment coverage before any candidate is installed."""
    try:
        if len(raw) > MAX_BUNDLE or SECRET_BYTES.search(raw):
            raise ValueError()
        item = parse_json(raw)
        fields = {"schema_version", "kind", "catalog_id", "version", "minimum_runtime",
                  "maximum_runtime_exclusive", "previous_release_sha256", "bundle_sha256",
                  "bundle", "assessments", "created_at"}
        if not isinstance(item, dict) or set(item) != fields or type(item["schema_version"]) is not int or item["schema_version"] != RELEASE_SCHEMA or item["kind"] != "local-catalog-release":
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
        assessments = item["assessments"]
        if not isinstance(assessments, list) or len(assessments) != len(refs):
            raise ValueError()
        # Every candidate must carry a complete, explicitly unapproved assessment. This
        # checks that the reviewer has something to review, not that anyone approved it.
        required = {"candidate_ref", "proposal", "prepared_by", "prepared_at", "provenance",
                    "scope", "coverage", "uncertainty", "redistribution", "scientific_approval"}
        seen = set()
        for assessment in assessments:
            if (not isinstance(assessment, dict) or set(assessment) != required
                    or any(not isinstance(assessment[key], str) or not 1 <= len(assessment[key]) <= 4000 for key in required)
                    or assessment["candidate_ref"] not in refs or assessment["candidate_ref"] in seen
                    or assessment["scientific_approval"] != "not_conferred"
                    or assessment["proposal"] not in {"propose_for_catalog", "propose_retirement"}):
                raise ValueError()
            seen.add(assessment["candidate_ref"])
        return item
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        raise Fault("catalog_release_invalid", "Release shape, exact bundle pin, runtime range or per-candidate assessment coverage is invalid.") from None


def build(store, bundle_raw, settings, metadata, assessments, *, previous_raw=None):
    """Assemble a release for review. Requalifies every candidate before it can be proposed."""
    required = {"catalog_id", "version", "minimum_runtime", "maximum_runtime_exclusive"}
    if not isinstance(metadata, dict) or set(metadata) != required:
        raise Fault("catalog_release_invalid", "Provide catalog ID, version and the supported runtime range.")
    item = {"schema_version": RELEASE_SCHEMA, "kind": "local-catalog-release", **metadata,
            "previous_release_sha256": digest(previous_raw) if previous_raw is not None else None,
            "bundle_sha256": digest(canonical(parse_json(bundle_raw))), "bundle": parse_json(bundle_raw),
            "assessments": assessments, "created_at": utc_now()}
    raw = canonical(item)
    validate(raw)
    if previous_raw is not None:
        previous = validate(previous_raw, compatibility=False)
        if (previous["catalog_id"] != item["catalog_id"] or version(previous["version"]) >= version(item["version"])
                or not set(previous["bundle"]["candidate_refs"]) <= set(item["bundle"]["candidate_refs"])):
            raise Fault("catalog_release_conflict", "Updates must keep the catalog ID, increase its version and retain previous candidate IDs with an explicit retirement proposal.")
    # Requalification is local and may run generated controls in the configured container.
    import_bundle(store, canonical(item["bundle"]), settings)
    return raw


def install(store, raw, settings, *, log=None):
    release = validate(raw)
    receipt = import_bundle(store, canonical(release["bundle"]), settings, log=log)
    receipt.update(release_sha256=digest(raw), catalog_id=release["catalog_id"], version=release["version"],
                   retired_candidate_refs=[entry["candidate_ref"] for entry in release["assessments"]
                                           if entry["proposal"] == "propose_retirement"],
                   scientific_approval_imported=False)
    return receipt
