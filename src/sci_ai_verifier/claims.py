"""Validate provenance and structural claim fields; do not judge scientific meaning."""

from .common import Fault, canonical, digest, normalize
from .ingest import read_file

FIELDS = ("statement", "scope", "expected_behavior", "source_path", "source_quote", "report_note")


def build_manifest(store, state, snapshot, candidates):
    accepted, statements, identities = [], set(), set()
    for index, candidate in enumerate(candidates):
        claim = {key: normalize(value) for key, value in candidate.items()}
        if any(not claim[key].strip() for key in FIELDS if key != "report_note"):
            raise Fault("empty_claim_field", "Claim fields other than report_note must be nonempty.",
                        [f"claims[{index}]"])
        if "\n" in claim["statement"].strip():
            raise Fault("non_atomic_structure", "Use a single statement per claim.",
                        [f"claims[{index}].statement"])
        statement = " ".join(claim["statement"].split()).casefold()
        identity = digest(canonical({"snapshot_digest": snapshot["digest"], **claim}))
        if identity in identities or statement in statements:
            raise Fault("duplicate_claim", "Duplicate claim statements are not accepted.",
                        [f"claims[{index}]"])
        matches = [r for r in state["read_receipts"] if r["path"] == claim["source_path"]]
        if not matches:
            raise Fault("source_not_read", "Read the claim's source file before committing it.",
                        [f"claims[{index}].source_path"])
        delivered = [read_file(store, snapshot, r["path"], r["start"], r["end"],
                               state["limits"]["max_read_bytes"])["content"] for r in matches]
        if not any(claim["source_quote"] in text for text in delivered):
            raise Fault("quote_not_found", "The exact quote must occur in a delivered source range.",
                        [f"claims[{index}].source_quote"])
        identities.add(identity)
        statements.add(statement)
        accepted.append({"claim_id": "claim-" + identity, **claim})
    manifest_id = "manifest-" + digest(canonical({
        "snapshot_digest": snapshot["digest"], "claims": accepted,
    }))
    return {
        "schema_version": 1, "id": manifest_id, "run_id": state["run_id"],
        "created_at": state["updated_at"], "implementation_version": state["implementation_version"],
        "snapshot_id": snapshot["id"], "snapshot_digest": snapshot["digest"],
        "claims": accepted, "count": len(accepted),
        "extraction_provenance": state["agent"],
        "verification_complete": False,
        "semantic_review": "not_established_by_structural_validation",
    }
