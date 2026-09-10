"""Content-addressed objects and an atomic event journal with readable projections."""

import json
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

from . import __version__
from .common import Fault, canonical, digest, utc_now

# A saved run is only read by an implementation that understands its record shape.
# There is no automatic migration: an unsupported record is rejected, never rewritten.
SCHEMA_VERSION = 1
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})
REQUIRED_STATE_FIELDS = frozenset({
    "schema_version", "implementation_version", "profile", "run_id", "created_at",
    "updated_at", "last_activity_at", "revision", "state_token", "run_state",
    "claim_states", "source_path", "source_root", "limits", "steps_used",
    "retries_remaining", "illegal_transitions_remaining", "objects", "context_manifest",
    "operational_refs", "read_receipts", "source_ref", "manifest_ref",
    "verification_complete", "finished_at", "completion_reason", "finalization",
    "agent", "host_limitations",
})
REQUIRED_LIMIT_FIELDS = frozenset({
    "max_steps", "repair_retries", "illegal_transitions", "max_files", "max_file_bytes",
    "max_total_bytes", "max_read_bytes", "max_claims", "resumption_window_seconds",
})
LOCK_TIMEOUT_SECONDS = 2.0
LOCK_INTERVAL_SECONDS = 0.05


def no_links(path):
    """Reject symlinks and Windows junction/reparse components before resolving."""
    try:
        path = Path(os.path.abspath(path))
    except (OSError, ValueError):
        raise Fault("invalid_path", f"Not a usable filesystem path: {path!r}") from None
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise Fault("unsafe_path", f"Links are not permitted: {part}", fatal=True)
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            # A malformed path is a correctable request, not a storage failure.
            raise Fault("invalid_path", f"Not a usable filesystem path: {part}") from None
        if getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise Fault("unsafe_path", f"Reparse points are not permitted: {part}", fatal=True)
    return path


def compatible(state):
    """Reject a saved run this implementation cannot read; never rewrite it."""
    found = state.get("schema_version")
    if found not in SUPPORTED_SCHEMA_VERSIONS:
        raise Fault("incompatible_run_record",
                    f"This run was written with record schema {found!r}; implementation "
                    f"{__version__} reads {sorted(SUPPORTED_SCHEMA_VERSIONS)} and performs no "
                    "migration. Read it with the implementation that wrote it.", fatal=True)
    limits = state.get("limits")
    missing = sorted(REQUIRED_STATE_FIELDS - set(state)) or (
        [] if isinstance(limits, dict) and REQUIRED_LIMIT_FIELDS <= set(limits)
        else ["limits"])
    if missing:
        raise Fault("incompatible_run_record",
                    f"The saved run record is missing required fields: {', '.join(missing)}. "
                    "It was not written by a compatible implementation.", fatal=True)


def file_lock(fileno):
    """Non-blocking acquire/release for this platform, so contention cannot hang."""
    if os.name == "nt":
        import msvcrt
        return (lambda: msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1),
                lambda: msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1))
    import fcntl
    return (lambda: fcntl.flock(fileno, fcntl.LOCK_EX | fcntl.LOCK_NB),
            lambda: fcntl.flock(fileno, fcntl.LOCK_UN))


def atomic_write(path, data):
    path = no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Store:
    def __init__(self, workspace):
        self.root = no_links(Path(workspace) / ".verifier")
        self.root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id):
        try:
            if str(UUID(run_id)) != run_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise Fault("invalid_run_id", "Use a returned run ID.", ["run_id"]) from None
        return no_links(self.root / "runs" / run_id)

    @contextmanager
    def lock(self, run_id):
        directory = self.run_dir(run_id)
        if not directory.is_dir():
            raise Fault("run_not_found", "No saved run has that ID.", ["run_id"])
        lock_path = no_links(directory / ".lock")
        with lock_path.open("a+b") as stream:
            stream.seek(0, 2)
            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            acquire, release = file_lock(stream.fileno())
            deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
            while True:
                stream.seek(0)
                try:
                    acquire()
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        # Contention leaves the saved run exactly as it was.
                        raise Fault("run_busy", "Another request holds this run; "
                                    "retry after the current one returns.", ["run_id"]) from None
                    time.sleep(LOCK_INTERVAL_SECONDS)
            try:
                yield
            finally:
                stream.seek(0)
                release()

    def put(self, data):
        key = digest(data)
        target = no_links(self.root / "store" / key)
        if target.exists():
            self.get(key)
        else:
            atomic_write(target, data)
        return key

    def put_json(self, data):
        return self.put(canonical(data))

    def get(self, key):
        if not isinstance(key, str) or not re.fullmatch("[0-9a-f]{64}", key):
            raise Fault("corrupted_state", "Invalid committed object reference.", fatal=True)
        try:
            data = no_links(self.root / "store" / key).read_bytes()
        except OSError:
            raise Fault("corrupted_state", "A committed object is unavailable.", fatal=True) from None
        if digest(data) != key:
            raise Fault("corrupted_state", "A committed object failed its digest check.", fatal=True)
        return data

    def get_json(self, key):
        try:
            return json.loads(self.get(key))
        except (ValueError, UnicodeError):
            raise Fault("corrupted_state", "A committed object is invalid JSON.", fatal=True) from None

    def read(self, run_id, *, verify_objects=True):
        directory = self.run_dir(run_id)
        files = sorted(no_links(directory / "events").glob("*.json"))
        if not files:
            raise Fault("run_not_found", "No committed run exists.", ["run_id"])
        previous = None
        try:
            for sequence, path in enumerate(files, 1):
                event = json.loads(no_links(path).read_bytes())
                saved_digest = event.pop("digest")
                if (path.name != f"{sequence:08d}.json" or digest(canonical(event)) != saved_digest
                        or event["previous_digest"] != previous or event["sequence"] != sequence
                        or event["run_id"] != run_id):
                    raise ValueError()
                previous = saved_digest
            state = event["state_after"]
            if (state["run_id"] != run_id or state["revision"] != len(files)
                    or state["profile"] != "stage2"):
                raise ValueError()
            projection = no_links(directory / "run.json")
            if projection.exists():
                try:
                    cached = json.loads(projection.read_bytes())
                except (ValueError, UnicodeError):
                    cached = {}
                if cached.get("revision", 0) > state["revision"]:
                    raise ValueError("Journal tail is missing.")
        except (KeyError, TypeError, ValueError, OSError):
            raise Fault("corrupted_state", "The event journal failed validation.", fatal=True) from None
        compatible(state)
        if verify_objects:
            for key in state["objects"]:
                self.get(key)
        return state, previous

    def record(self, state, previous, event_type, before, request, result):
        event = {
            "schema_version": SCHEMA_VERSION, "implementation_version": __version__,
            "run_id": state["run_id"], "sequence": state["revision"],
            "created_at": utc_now(), "event_type": event_type,
            "request": request, "result": result,
            "state_before": before, "state_after": state,
            "artifact_refs": state["objects"], "previous_digest": previous,
        }
        event["digest"] = digest(canonical(event))
        target = self.run_dir(state["run_id"]) / "events" / f'{state["revision"]:08d}.json'
        if target.exists():
            raise Fault("corrupted_state", "An event sequence already exists.", fatal=True)
        atomic_write(target, canonical(event))
        # The event is already committed. A cache-write failure cannot undo it.
        self.project(state)

    def project(self, state):
        directory = self.run_dir(state["run_id"])
        def write_projection(path, key=None, data=None):
            try:
                atomic_write(path, self.get(key) if key else data)
            except (OSError, Fault):
                pass  # A missing/corrupt cache never rolls back a journal commit.
        write_projection(directory / "run.json", data=canonical(state))
        for key, filename in (("source_ref", "source-snapshot.json"),
                              ("manifest_ref", "claim-manifest.json")):
            if state.get(key):
                write_projection(directory / filename, key=state[key])
        for key in state["operational_refs"]:
            try:
                outcome = self.get_json(key)
            except Fault:
                continue
            write_projection(directory / "operational-outcomes" / f'{outcome["id"]}.json', key=key)

    def finalize(self, state):
        directory = self.run_dir(state["run_id"])
        failures = []
        for folder in (directory, directory / "events", directory / "operational-outcomes"):
            try:
                no_links(folder)
                for path in folder.glob(".write-*"):
                    no_links(path).unlink()
            except (OSError, Fault):
                failures.append(folder.relative_to(directory).as_posix())
        return {"status": "warnings" if failures else "complete",
                "retained": ["journal", "committed_objects", "readable_projections"],
                "discarded": ["run_temporary_writes"], "cleanup_failures": failures,
                "shared_store_gc": "deferred"}
