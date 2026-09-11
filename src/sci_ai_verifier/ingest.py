"""Bounded source snapshots and exact reads. Never execute or follow references."""

import fnmatch
import os
import re
import stat
from pathlib import Path, PurePosixPath

from .common import Fault, canonical, digest, normalize
from .storage import no_links

POLICY = "stage2-snapshot-v1"
MAX_DIRECTORY_DEPTH = 64
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".verifier", ".venv", "venv", "env",
    "node_modules", "__pycache__", ".pytest_cache", "tmp", "temp", "dist", "build",
}
SECRET_NAMES = (
    ".env*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
    "*credentials*", "*secrets*", ".netrc", ".npmrc", ".pypirc",
)
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".tsv", ".toml",
    ".py", ".r", ".js", ".ts", ".html", ".xml", ".rst", ".ini", ".cfg", ".sh",
}
SECRET_BYTES = re.compile(
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    rb"|(?:sk-ant-|sk-proj-|ghp_|github_pat_)[A-Za-z0-9_-]{16,}"
    rb"|AKIA[A-Z0-9]{16}"
)


def valid_relative(path):
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    parts = PurePosixPath(path).parts
    return (not path.startswith("/") and str(PurePosixPath(path)) == path
            and all(p not in {".", ".."} and not any(c in p for c in ':<>|?*"')
                    and not p.endswith((" ", ".")) for p in parts))


def authorize(source_path, source_root):
    # Resolve only after checking all existing path components for links.
    path = no_links(source_path)
    root = no_links(source_root)
    try:
        path.relative_to(root)
    except ValueError:
        raise Fault("source_not_authorized", "Source is outside the configured submission directory.",
                    ["source_path"], fatal=True) from None
    return path


def authorized_source(supplied, state):
    """Accept any spelling of the pinned path. Only a different location is unauthorized."""
    try:
        path = no_links(supplied)
    except Fault as error:
        raise Fault(error.code, str(error), ["source_path"], fatal=error.fatal) from None
    if path != Path(state["source_path"]):
        raise Fault("source_not_authorized",
                    "This is not the source authorized at bootstrap. Use the path returned in "
                    f"authorized-parameters: {state['source_path']}", ["source_path"], fatal=True)
    return path


def snapshot(store, state):
    source = authorize(state["source_path"], state["source_root"])
    limits = state["limits"]
    if not source.exists():
        raise Fault("source_missing", "The authorized source does not exist.", fatal=True)
    if not source.is_dir() and not source.is_file():
        raise Fault("unsafe_source", "Source must be a regular file or skill directory.", fatal=True)
    top = source / "SKILL.md" if source.is_dir() else source
    if not top.is_file():
        raise Fault("source_missing", "A directory must contain a top-level SKILL.md.", fatal=True)
    files, excluded, seen = [], [], set()
    total = 0
    visited = 0

    def visit():
        nonlocal visited
        visited += 1
        if visited > limits["max_files"] * 10:
            raise Fault("source_too_large", "Source traversal limit exceeded.", fatal=True)

    def add(path, relative):
        nonlocal total
        visit()
        no_links(path)
        if not valid_relative(relative) or relative.casefold() in seen:
            raise Fault("unsafe_source", "Ambiguous or unsafe snapshot path.", fatal=True)
        seen.add(relative.casefold())
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise Fault("unsafe_source", "Only regular files may be snapshotted.", fatal=True)
        if any(fnmatch.fnmatch(path.name.lower(), pattern) for pattern in SECRET_NAMES):
            excluded.append({"path": relative, "reason": "secret_filename"})
            return
        if info.st_size > limits["max_file_bytes"]:
            raise Fault("source_too_large", "A source file exceeds the file-size limit.", fatal=True)
        with path.open("rb") as stream:
            raw = stream.read(limits["max_file_bytes"] + 1)
        if len(raw) > limits["max_file_bytes"]:
            raise Fault("source_too_large", "A source file grew beyond its limit.", fatal=True)
        no_links(path)
        if SECRET_BYTES.search(raw):
            excluded.append({"path": relative, "reason": "credential_material"})
            return
        try:
            text = raw.decode("utf-8")
            if "\x00" in text:
                raise UnicodeError()
        except UnicodeError:
            if path == top or path.suffix.lower() in TEXT_SUFFIXES:
                raise Fault("invalid_source_encoding", "A required text file is not UTF-8 text.",
                            fatal=True) from None
            data, encoding, normalization = raw, "binary", "none"
        else:
            data, encoding, normalization = normalize(text).encode("utf-8"), "utf-8", "LF"
        total += len(data)
        if len(files) >= limits["max_files"] or total > limits["max_total_bytes"]:
            raise Fault("source_too_large", "Snapshot exceeds the configured limits.", fatal=True)
        key = store.put(data)
        files.append({"path": relative, "digest": key, "size": len(data),
                      "encoding": encoding, "normalization": normalization})

    if source.is_dir():
        def walk(directory, depth=0):
            nonlocal visited
            if depth > MAX_DIRECTORY_DEPTH:
                raise Fault("source_too_large", "Source directory depth exceeds 64 levels.", fatal=True)
            # Bound enumeration before sorting; do not consume an unbounded directory.
            entries = []
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    if len(entries) + visited >= limits["max_files"] * 10:
                        raise Fault("source_too_large", "Source traversal limit exceeded.", fatal=True)
                    entries.append(entry.name)
            for name in sorted(entries):
                path = directory / name
                relative = path.relative_to(source).as_posix()
                no_links(path)
                if path.is_dir():
                    visit()
                    if name.lower() in EXCLUDED_DIRS:
                        excluded.append({"path": relative, "reason": "excluded_directory"})
                    else:
                        walk(path, depth + 1)
                else:
                    add(path, relative)
        walk(source)
        top_path = "SKILL.md"
    else:
        add(source, source.name)
        top_path = source.name
    files.sort(key=lambda x: x["path"])
    entry = next((x for x in files if x["path"] == top_path), None)
    if entry is None or not entry["size"]:
        raise Fault("required_source_excluded", "The required top-level skill is excluded or empty.",
                    fatal=True)
    if entry["size"] > limits["max_read_bytes"]:
        raise Fault("source_too_large", "The top-level skill exceeds the bootstrap text limit.",
                    fatal=True)
    identity = digest(canonical({"policy": POLICY, "files": files}))
    record = {
        "schema_version": 1, "id": "snapshot-" + identity, "digest": identity,
        "run_id": state["run_id"], "created_at": state["updated_at"],
        "implementation_version": state["implementation_version"],
        "original_path": str(source), "policy": POLICY, "files": files,
        "excluded": excluded, "total_size": total, "top_path": top_path,
        "integrity": "verified",
    }
    payload = read_file(store, record, top_path, 0, None, limits["max_read_bytes"])
    if not payload["content"].strip():
        raise Fault("empty_source", "The top-level skill contains no text.", fatal=True)
    return record, payload


def verified_snapshot(store, state, snapshot_id=None, snapshot_digest=None):
    record = store.get_json(state["source_ref"])
    expected = digest(canonical({"policy": record["policy"], "files": record["files"]}))
    if record["digest"] != expected or record["id"] != "snapshot-" + expected:
        raise Fault("corrupted_state", "Snapshot manifest identity mismatch.", fatal=True)
    if snapshot_id is not None and (snapshot_id != record["id"]
                                   or snapshot_digest != record["digest"]):
        raise Fault("snapshot_mismatch", "Snapshot ID or digest does not match this run.", fatal=True)
    for entry in record["files"]:
        store.get(entry["digest"])
    return record


def read_file(store, record, path, start, end, max_bytes):
    if not valid_relative(path):
        raise Fault("invalid_snapshot_path", "Use an exact path in the snapshot manifest.", ["path"])
    entry = next((f for f in record["files"] if f["path"] == path), None)
    if entry is None:
        raise Fault("snapshot_path_missing", "Path is not an included snapshot file.", ["path"])
    raw = store.get(entry["digest"])
    if entry["encoding"] != "utf-8":
        raise Fault("non_text_payload", "This snapshot file is binary.", ["path"])
    end = len(raw) if end is None else end
    if start < 0 or end < start or end > len(raw) or (start == end and len(raw) != 0):
        raise Fault("invalid_byte_range", "Use a nonempty half-open range within the file.",
                    ["start", "end"])
    if end - start > max_bytes:
        raise Fault("read_too_large", "Supply a byte range within the returned-text limit.",
                    ["start", "end"])
    try:
        content = raw[start:end].decode("utf-8")
    except UnicodeError:
        raise Fault("invalid_byte_range", "Byte boundaries must not split a UTF-8 character.",
                    ["start", "end"]) from None
    return {"trust_class": "untrusted_payload", "path": path, "digest": entry["digest"],
            "encoding": "utf-8", "size": len(raw), "start": start, "end": end,
            "content": content}
