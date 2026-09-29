"""Small shared primitives, with no workflow policy."""

import hashlib
import json
import re
from datetime import datetime, timezone


class Fault(Exception):
    def __init__(self, code, message, fields=(), *, fatal=False):
        super().__init__(message)
        self.code, self.fields, self.fatal = code, list(fields), fatal


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


# A CommonMark fence opener: up to three spaces, then three or more backticks or tildes.
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")


def fenced_blocks(text):
    """(first body line number, info string, body lines) for each fenced code block, CommonMark style.

    A skill's install commands count only inside fenced blocks ("Skill environment" in
    local-contract.md): glycoengineering's prose says "`uv pip install glycoshield` fails", and
    inline code in a sentence is not a declaration. A reply's answer line may sit inside one
    ("Reading a reply" in tool-contracts.md).
    """
    blocks, lines, index = [], text.split("\n"), 0
    while index < len(lines):
        opening = FENCE.fullmatch(lines[index])
        if not opening or (opening.group(1)[0] == "`" and "`" in opening.group(2)):
            index += 1
            continue
        marker, body, start = opening.group(1), [], index + 2
        index += 1
        while index < len(lines):
            closing = re.fullmatch(r" {0,3}(`{3,}|~{3,})\s*", lines[index])
            if closing and closing.group(1)[0] == marker[0] and len(closing.group(1)) >= len(marker):
                break
            body.append(lines[index])
            index += 1
        blocks.append((start, opening.group(2).strip(), body))
        index += 1
    return blocks


def validate(value, schema, field="arguments"):
    """Validate only the JSON Schema vocabulary used by our published tools and reply schemas.

    Objects never take keys their schema does not name, so a reply schema states
    `additionalProperties: false` for Claude Code and means the same thing here.
    """
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                return validate(value, option, field)
            except Fault:
                continue
        raise Fault("invalid_arguments", f"{field} matches none of its allowed forms.", [field])
    kind = schema["type"]
    types = {"object": dict, "array": list, "string": str, "integer": int}
    if type(value) is not types[kind]:
        raise Fault("invalid_arguments", f"{field} must be {kind}.", [field])
    if "enum" in schema and value not in schema["enum"]:
        raise Fault("invalid_arguments",
                    f"{field} must be one of: {', '.join(map(str, schema['enum']))}.", [field])
    if kind == "object":
        properties = schema["properties"]
        if set(value) - set(properties) or set(schema["required"]) - set(value):
            raise Fault("invalid_arguments", f"{field} has missing or unknown fields.", [field])
        for key, child in value.items():
            validate(child, properties[key], f"{field}.{key}")
    elif kind == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema["maxItems"]:
            raise Fault("invalid_arguments", f"{field} has an invalid entry count.", [field])
        for i, child in enumerate(value):
            validate(child, schema["items"], f"{field}[{i}]")
    elif kind == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema["maxLength"]:
            raise Fault("invalid_arguments", f"{field} has an invalid length.", [field])
        # JSON Schema patterns search rather than match, as re.search does.
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise Fault("invalid_arguments", f"{field} does not match its pattern.", [field])
    elif not schema["minimum"] <= value <= schema["maximum"]:
        raise Fault("invalid_arguments", f"{field} is outside its bounds.", [field])
