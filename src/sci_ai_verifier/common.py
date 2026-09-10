"""Small shared primitives, with no workflow policy."""

import hashlib
import json
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


def validate(value, schema, field="arguments"):
    """Validate only the JSON Schema vocabulary used by our published tools."""
    kind = schema["type"]
    types = {"object": dict, "array": list, "string": str, "integer": int}
    if type(value) is not types[kind]:
        raise Fault("invalid_arguments", f"{field} must be {kind}.", [field])
    if kind == "object":
        properties = schema["properties"]
        if set(value) - set(properties) or set(schema["required"]) - set(value):
            raise Fault("invalid_arguments", f"{field} has missing or unknown fields.", [field])
        for key, child in value.items():
            validate(child, properties[key], f"{field}.{key}")
    elif kind == "array":
        if len(value) > schema["maxItems"]:
            raise Fault("invalid_arguments", f"{field} has too many entries.", [field])
        for i, child in enumerate(value):
            validate(child, schema["items"], f"{field}[{i}]")
    elif kind == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema["maxLength"]:
            raise Fault("invalid_arguments", f"{field} has an invalid length.", [field])
    elif not schema["minimum"] <= value <= schema["maximum"]:
        raise Fault("invalid_arguments", f"{field} is outside its bounds.", [field])
