"""Validate provenance and structural claim fields; do not judge scientific meaning."""

import re

from .common import Fault, canonical, digest, fenced_blocks, normalize
from .ingest import read_file

# An ATX heading. A `#` line inside a fenced code block is a comment, not a heading.
HEADING = re.compile(r" {0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*")

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


def sections(text):
    """A skill file's sections ("Claims" in local-contract.md): the text under each heading, down to the
    next heading of any level, with its heading, level, first line and body. Text before the first
    heading, other than YAML frontmatter, is a section without one."""
    lines = text.split("\n")
    fenced = set()
    for first, _, body in fenced_blocks(text):
        fenced.update(range(first - 1, first + len(body) + 1))  # The opener, the body and the closer.
    front = 0
    if lines and lines[0].strip() == "---":
        front = next((number for number, line in enumerate(lines[1:], 2) if line.strip() in ("---", "...")), 0)
    found = [{"heading": None, "level": 0, "line": front + 1, "body": []}]
    for number, line in enumerate(lines, 1):
        if number <= front:
            continue
        match = None if number in fenced else HEADING.fullmatch(line)
        if match:
            found.append({"heading": match.group(2), "level": len(match.group(1)), "line": number, "body": []})
        else:
            found[-1]["body"].append(line)
    return [item for item in found if any(line.strip() for line in item["body"])]


def section_coverage(files, claims):
    """Which sections of SKILL.md the claims cover, or `None` when the skill has no SKILL.md.

    A claim quoting SKILL.md covers the section its quote starts in; a claim quoting another file
    covers the first section that names that file, so an index of files at the end credits nothing.
    `files` maps snapshot paths to text.
    """
    text = files.get("SKILL.md")
    if text is None:
        return None
    parts = sections(text)
    starts = [item["line"] for item in parts]
    covered = {index: [] for index in range(len(parts))}
    outside = []
    for claim in claims:
        places = []
        if claim["source_path"] == "SKILL.md" and claim["source_quote"] in text:
            line = text[:text.index(claim["source_quote"])].count("\n") + 1
            before = [index for index, start in enumerate(starts) if start <= line]
            places = before[-1:]
        else:
            places = [index for index, item in enumerate(parts) if claim["source_path"] in "\n".join(item["body"])][:1]
        for index in places:
            covered[index].append(claim["claim_id"])
        if not places:
            outside.append(claim["claim_id"])
    listed = []
    for index, item in enumerate(parts):
        body = "\n".join(item["body"])
        listed.append({"heading": item["heading"], "level": item["level"], "line": item["line"],
                       "files": sorted(path for path in files if path != "SKILL.md" and path in body),
                       "claims": covered[index]})
    return {"file": "SKILL.md", "sections": listed,
            "uncovered": [item["heading"] or "(before the first heading)" for item in listed if not item["claims"]],
            "claims_outside_sections": outside}
