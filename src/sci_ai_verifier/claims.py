"""Validate provenance and structural claim fields; do not judge scientific meaning."""

import re

from .common import Fault, canonical, digest, fenced_blocks, normalize
from .ingest import read_file

# An ATX heading. A `#` line inside a fenced code block is a comment, not a heading.
HEADING = re.compile(r" {0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*")

FIELDS = ("statement", "scope", "expected_behavior", "source_path", "source_quote", "report_note")
# Text before the first heading is a section with no heading of its own.
UNHEADED = "(before the first heading)"


def build_manifest(store, state, snapshot, candidates, set_aside=None):
    """`set_aside` is given only by the local profile, whose claims name their sections; its
    manifest must then hold every section of the top-level file ("Claims" in local-tasks.md)."""
    accepted, statements, identities = [], set(), set()
    listed = None
    if set_aside is not None:
        listed = skill_sections(store, snapshot)
        check_sections(listed, candidates, set_aside)
    for index, candidate in enumerate(candidates):
        claim = {key: normalize(value) if isinstance(value, str) else value for key, value in candidate.items()}
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
            # Run fbd49132's planner answered this by cutting a quote to two of its five gotchas
            # while the statement kept all five, so the repair is spelled out.
            raise Fault("quote_not_found", "The exact quote must occur in a delivered source range. Correct "
                        "its characters, spaces included, against the file; a shorter quote needs a shorter "
                        "statement.", [f"claims[{index}].source_quote"])
        identities.add(identity)
        statements.add(statement)
        accepted.append({"claim_id": "claim-" + identity, **claim})
    manifest_id = "manifest-" + digest(canonical({
        "snapshot_digest": snapshot["digest"], "claims": accepted,
    }))
    manifest = {
        "schema_version": 1, "id": manifest_id, "run_id": state["run_id"],
        "created_at": state["updated_at"], "implementation_version": state["implementation_version"],
        "snapshot_id": snapshot["id"], "snapshot_digest": snapshot["digest"],
        "claims": accepted, "count": len(accepted),
        "extraction_provenance": state["agent"],
        "verification_complete": False,
        "semantic_review": "not_established_by_structural_validation",
    }
    if listed is not None:
        manifest.update(sections=listed, set_aside=[{"section": item["section"], "reason": normalize(item["reason"])}
                                                     for item in set_aside])
    return manifest


def section_list(text):
    """The numbered sections of a skill file ("Claims" in local-tasks.md): `S1`, `S2`, ... in order,
    each with its heading, level, first line and word count."""
    return [{"section": "S" + str(number), "heading": item["heading"] or UNHEADED, "level": item["level"],
             "line": item["line"], "words": len(re.findall(r"\w+", " ".join(item["body"])))}
            for number, item in enumerate(sections(text), 1)]


def skill_sections(store, snapshot):
    """The numbered sections of a snapshot's top-level file, or an empty list when it has none."""
    entry = next((item for item in snapshot["files"] if item["path"] == snapshot.get("top_path", "SKILL.md")), None)
    if entry is None or entry["encoding"] != "utf-8":
        return []
    return section_list(normalize(store.get(entry["digest"]).decode("utf-8")))


def check_sections(listed, claims, set_aside):
    """Refuse a local manifest that leaves a section out, holds one twice or names an unknown one."""
    places = {}
    for index, claim in enumerate(claims):
        if len(set(claim["sections"])) != len(claim["sections"]):
            raise Fault("sections_incomplete", "A claim names one of its sections twice.",
                        [f"claims[{index}].sections"])
        for section in claim["sections"]:
            places.setdefault(section, []).append(f"claims[{index}]")
    for index, item in enumerate(set_aside):
        places.setdefault(item["section"], []).append(f"set_aside[{index}]")
    known = {item["section"]: item["heading"] for item in listed}
    unknown = sorted(set(places) - set(known), key=lambda name: (len(name), name))
    twice = [name for name in known if len(places.get(name, [])) > 1]
    missing = [name for name in known if name not in places]
    if unknown or twice or missing:
        parts = []
        if missing:
            parts.append("left out: " + "; ".join(name + " " + repr(known[name]) for name in missing))
        if twice:
            parts.append("in more than one place: " + "; ".join(name + " (" + ", ".join(places[name]) + ")"
                                                                for name in twice))
        if unknown:
            parts.append("unknown: " + ", ".join(unknown))
        raise Fault("sections_incomplete", "Every section of the skill file goes in exactly one claim or in "
                    "set_aside with a reason (\"Claims\" in local-tasks.md). Sections " + "; ".join(parts) + ".",
                    ["claims", "set_aside"])


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


def section_texts(store, snapshot, wanted, limit=12000, total=150000):
    """The text of the named sections of a snapshot's top-level file, each cut at `limit` characters and
    all together at `total`, so a claim of many long sections still fits the critique's packet."""
    entry = next((item for item in snapshot["files"] if item["path"] == snapshot.get("top_path", "SKILL.md")), None)
    if entry is None or entry["encoding"] != "utf-8":
        return []
    found, left = [], total
    for number, item in enumerate(sections(normalize(store.get(entry["digest"]).decode("utf-8"))), 1):
        if "S" + str(number) in wanted:
            body = "\n".join(item["body"]).strip("\n")
            room = min(limit, left)
            text = body if len(body) <= room else body[:room] + " [truncated]"
            left -= min(len(body), room)
            found.append({"section": "S" + str(number), "heading": item["heading"] or UNHEADED, "text": text})
    return found


def manifest_coverage(manifest, files):
    """Which claim holds each section, or why it was set aside, for a manifest whose claims name their
    sections ("Claims" in local-tasks.md); `None` for one from before they did. `files` maps paths to text."""
    if "sections" not in manifest:
        return None
    aside = {item["section"]: item["reason"] for item in manifest.get("set_aside") or []}
    holders = {}
    for claim in manifest["claims"]:
        for name in claim.get("sections") or []:
            holders.setdefault(name, []).append(claim["claim_id"])
    text = files.get("SKILL.md") or ""
    bodies = ["\n".join(item["body"]) for item in sections(text)]
    listed = []
    for index, item in enumerate(manifest["sections"]):
        body = bodies[index] if index < len(bodies) else ""
        listed.append({**item, "files": sorted(path for path in files if path != "SKILL.md" and path in body),
                       "claims": holders.get(item["section"], []),
                       **({"set_aside": aside[item["section"]]} if item["section"] in aside else {})})
    return {"file": "SKILL.md", "sections": listed,
            "uncovered": [item["heading"] for item in listed if not item["claims"] and "set_aside" not in item],
            "set_aside": [{"section": item["section"], "heading": item["heading"], "reason": item["set_aside"]}
                          for item in listed if "set_aside" in item],
            "claims_outside_sections": []}
