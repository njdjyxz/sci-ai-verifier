"""Bounded data-only catalogs, exact release verification and immutable run pins."""

import json
import math
import re
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .common import Fault, canonical, digest
from .storage import atomic_write, no_links

REPOSITORY = "njdjyxz/sci-ai-verifier"
ASSETS = {"claim_types": 1, "evaluators": 2, "subject_runners": 1}
MAX_BYTES = 1024 * 1024
MAX_ENTRIES = 200


def invalid(message, code="catalog_invalid"):
    raise Fault(code, message, fatal=True)


def decode(data):
    def number(raw):
        value = float(raw)
        if not math.isfinite(value):
            invalid("Non-finite catalog number.")
        return value
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                invalid("Duplicate catalog JSON key.")
            result[key] = value
        return result
    try:
        if len(data) > MAX_BYTES:
            invalid("Catalog file exceeds 1 MiB.")
        value = json.loads(data, object_pairs_hook=pairs, parse_float=number,
                           parse_constant=lambda _: invalid("Non-finite catalog number."))
        pending = [(value, 0)]
        while pending:
            item, depth = pending.pop()
            if depth > 32:
                invalid("Catalog JSON nesting exceeds 32 levels.")
            children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
            pending.extend((child, depth + 1) for child in children)
        return value
    except (ValueError, UnicodeError, RecursionError):
        invalid("Catalog is not bounded valid JSON.")


def text_fields(value, fields):
    if not isinstance(value, dict) or any(
            not isinstance(value.get(key), str) or not value[key].strip()
            or len(value[key]) > 16000 for key in fields):
        invalid("Missing or invalid catalog text fields: " + ", ".join(fields))


def strings(value, name, *, allow_empty=False):
    if (not isinstance(value, list) or len(value) > MAX_ENTRIES
            or (not value and not allow_empty)
            or any(not isinstance(v, str) or not v or len(v) > 16000 for v in value)
            or len(set(value)) != len(value)):
        invalid("Invalid catalog list: " + name)


def sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def records(registry, key):
    entries = registry.get(key)
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        invalid("Invalid or oversized registry: " + key)
    seen = set()
    for entry in entries:
        text_fields(entry, ("id", "version", "status", "provenance"))
        if len(entry["id"]) > 160:
            invalid("Catalog ID exceeds the routing interface's 160-character bound.")
        if entry["id"] in seen:
            invalid("Duplicate registry identity: " + entry["id"])
        seen.add(entry["id"])
        if entry["status"] not in {"validated", "approved", "provisional", "retired"}:
            invalid("Unknown review status.")
    return entries


def validate_registries(assets):
    for name, schema in ASSETS.items():
        value = assets[name]
        if (not isinstance(value, dict) or type(value.get("schema_version")) is not int
                or value["schema_version"] != schema):
            invalid("Unsupported registry schema: " + name, "catalog_incompatible")
        if type(value.get("revision")) is not int or value["revision"] < 0:
            invalid("Invalid registry revision.")
    types = records(assets["claim_types"], "claim_types")
    type_ids = {item["id"] for item in types}
    for item in types:
        text_fields(item, ("name", "definition", "inputs", "outputs", "boundaries"))
    capabilities = (records(assets["evaluators"], "evaluators")
                    + records(assets["evaluators"], "harnesses"))
    if len({item["id"] for item in capabilities}) != len(capabilities):
        invalid("Evaluator and harness identities overlap.")
    for item in capabilities:
        for field in ("claim_type_ids", "scopes", "grades", "limitations"):
            strings(item.get(field), field, allow_empty=field == "limitations")
        if not set(item["claim_type_ids"]) <= type_ids or not set(item["grades"]) <= set("ABCD"):
            invalid("Unknown capability type or grade.")
        if "D" in item["grades"]:
            text_fields(item, ("rubric", "assessor_contract"))
        if set(item["grades"]) & set("ABC"):
            text_fields(item, ("input_interface", "output_interface", "configuration_contract",
                               "scoring_contract", "aggregation_contract", "trial_grade_policy"))
        pins = item.get("resources")
        if not isinstance(pins, list) or len(pins) > MAX_ENTRIES:
            invalid("Invalid resource pins.")
        for pin in pins:
            text_fields(pin, ("id", "version", "sha256"))
            if not sha(pin["sha256"]):
                invalid("Invalid resource digest.")
        if len({pin["id"] for pin in pins}) != len(pins):
            invalid("Duplicate capability resource identities.")
    for item in records(assets["subject_runners"], "subject_runners"):
        text_fields(item, ("input_interface", "output_interface", "configuration_contract"))


def manifest_for(raw, version, provenance):
    """Build reproducible metadata; never claim this function performs review."""
    return {"schema_version": 1, "catalog_version": version, "runtime_interface": 1,
            "skill_interface": 1, "provenance": provenance,
            "assets": {name: {"path": name + ".json", "version": str(decode(raw[name])["revision"]),
                               "sha256": digest(raw[name]), "bytes": len(raw[name])}
                       for name in ASSETS}}


def validate_manifest(raw, expected=None):
    if expected is not None and (not sha(expected) or digest(raw) != expected):
        invalid("Catalog manifest failed its expected SHA-256 check.", "catalog_integrity")
    manifest = decode(raw)
    text_fields(manifest, ("catalog_version", "provenance"))
    if any(type(manifest.get(k)) is not int or manifest[k] != 1
           for k in ("schema_version", "runtime_interface", "skill_interface")):
        invalid("Unsupported catalog schema or runtime/skill interface.", "catalog_incompatible")
    assets = manifest.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(ASSETS):
        invalid("Catalog must include exactly the three approved registry assets.")
    for name, entry in assets.items():
        text_fields(entry, ("path", "version", "sha256"))
        if (entry["path"] != name + ".json" or not sha(entry["sha256"])
                or type(entry.get("bytes")) is not int or not 0 < entry["bytes"] <= MAX_BYTES):
            invalid("Invalid catalog asset path, size, or digest.")
    return manifest


def verify(raw_manifest, raw_assets, expected=None):
    manifest = validate_manifest(raw_manifest, expected)
    if set(raw_assets) != set(ASSETS):
        invalid("Missing catalog assets.")
    assets = {}
    for name, entry in manifest["assets"].items():
        raw = raw_assets[name]
        if len(raw) != entry["bytes"] or digest(raw) != entry["sha256"]:
            invalid("Catalog asset failed verification: " + name, "catalog_integrity")
        assets[name] = decode(raw)
        if isinstance(assets[name], dict) and str(assets[name].get("revision")) != entry["version"]:
            invalid("Catalog asset revision differs from its release pin.", "catalog_integrity")
    validate_registries(assets)
    return manifest, assets


def bounded_read(path):
    with no_links(path).open("rb") as stream:
        return stream.read(MAX_BYTES + 1)


def read_release(directory, expected=None):
    try:
        manifest = bounded_read(Path(directory) / "manifest.json")
        validate_manifest(manifest, expected)
        assets = {name: bounded_read(Path(directory) / (name + ".json")) for name in ASSETS}
    except OSError:
        invalid("The selected catalog release is unavailable.", "catalog_unavailable")
    verify(manifest, assets, expected)
    return manifest, assets


def bundled_release(directory):
    try:
        raw = {name: bounded_read(Path(directory) / (name + ".json")) for name in ASSETS}
    except OSError:
        invalid("Bundled reviewed registries are unavailable.", "catalog_unavailable")
    validate_registries({name: decode(value) for name, value in raw.items()})
    manifest = canonical(manifest_for(raw, "bundled", "Installed repository registries; not a remote release"))
    return manifest, raw


def pin(store, state, registry_root, release_directory=None):
    selection_path = store.root / "catalog-selection.json"
    if release_directory is not None:
        raw_manifest, raw = read_release(release_directory)
        origin = {"kind": "operator_local", "path": str(release_directory)}
    elif no_links(selection_path).exists():
        selection = decode(bounded_read(selection_path))
        if (not isinstance(selection, dict) or not sha(selection.get("manifest_sha256"))
                or selection.get("repository") != REPOSITORY
                or not isinstance(selection.get("commit"), str)
                or not re.fullmatch("[0-9a-f]{40}", selection["commit"])):
            invalid("Invalid configured catalog selection.")
        raw_manifest, raw = read_release(store.root / "catalogs" / selection["manifest_sha256"],
                                         selection["manifest_sha256"])
        try:
            receipt = decode(bounded_read(store.root / "catalogs" / selection["manifest_sha256"] /
                                           "receipts" / (selection["commit"] + ".json")))
        except OSError:
            invalid("The configured release lacks its verified source receipt.", "catalog_unavailable")
        if receipt != selection:
            invalid("Configured catalog receipt failed origin verification.", "catalog_integrity")
        origin = {"kind": "verified_cache", **selection}
    else:
        raw_manifest, raw = bundled_release(registry_root)
        origin = {"kind": "bundled"}
    manifest, _ = verify(raw_manifest, raw)
    keys = {name: store.put(value) for name, value in raw.items()}
    manifest_ref = store.put(raw_manifest)
    lock = {"schema_version": 1, "catalog_version": manifest["catalog_version"],
            "manifest_ref": manifest_ref, "assets": keys, "origin": origin}
    lock_ref = store.put_json(lock)
    for key in [manifest_ref, *keys.values(), lock_ref]:
        if key not in state["objects"]:
            state["objects"].append(key)
    state["catalog_ref"] = lock_ref


def pinned(store, state):
    lock = store.get_json(state["catalog_ref"])
    raw_manifest = store.get(lock["manifest_ref"])
    raw = {name: store.get(key) for name, key in lock["assets"].items()}
    _, assets = verify(raw_manifest, raw, lock["manifest_ref"])
    return lock, assets


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise URLError("Catalog redirects are not permitted.")


def download(path, commit, timeout):
    url = f"https://api.github.com/repos/{REPOSITORY}/contents/catalog/{path}?ref={commit}"
    request = Request(url, headers={"Accept": "application/vnd.github.raw+json",
                                   "User-Agent": "sci-ai-verifier-catalog"})
    with build_opener(NoRedirect).open(request, timeout=timeout) as response:
        deadline = time.monotonic() + timeout
        chunks, size = [], 0
        while size <= MAX_BYTES:
            if time.monotonic() >= deadline:
                raise TimeoutError("Catalog response deadline exceeded.")
            chunk = response.read1(min(65536, MAX_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        return b"".join(chunks)


def fetch_release(store, commit, expected, *, offline=False, transport=None):
    if not isinstance(commit, str) or not re.fullmatch("[0-9a-f]{40}", commit) or not sha(expected):
        invalid("Supply a full commit SHA and an independently obtained manifest SHA-256.")
    directory = store.root / "catalogs" / expected
    selection = {"repository": REPOSITORY, "commit": commit, "manifest_sha256": expected}
    receipt = directory / "receipts" / (commit + ".json")
    if offline:
        read_release(directory, expected)
        try:
            cached_origin = decode(bounded_read(receipt))
        except OSError:
            invalid("No verified cache receipt exists for this exact commit.", "catalog_unavailable")
        if cached_origin != selection:
            invalid("The offline cache origin does not match the requested release.", "catalog_integrity")
    else:
        transport = transport or download
        deadline = time.monotonic() + 30
        def get(path):
            left = deadline - time.monotonic()
            if left <= 0:
                invalid("Catalog download time limit exceeded.", "catalog_unavailable")
            try:
                raw = transport(path, commit, min(10, left))
            except (OSError, URLError, TimeoutError):
                invalid("Catalog download unavailable; selected release is unchanged.", "catalog_unavailable")
            if time.monotonic() > deadline:
                invalid("Catalog download time limit exceeded.", "catalog_unavailable")
            return raw
        raw_manifest = get("manifest.json")
        manifest = validate_manifest(raw_manifest, expected)
        raw = {name: get(entry["path"]) for name, entry in manifest["assets"].items()}
        verify(raw_manifest, raw, expected)
        for name, value in raw.items():
            atomic_write(directory / (name + ".json"), value)
        atomic_write(directory / "manifest.json", raw_manifest)
        atomic_write(receipt, canonical(selection))
    atomic_write(store.root / "catalog-selection.json", canonical(selection))
    return selection
