"""Durable, redacted observable workflow events, separate from scientific state."""

import errno
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID, uuid4

from .common import Fault, canonical, digest, utc_now
from .ingest import SECRET_BYTES
from .storage import atomic_write, file_lock, no_links

SENSITIVE = re.compile(r"token|secret|password|authorization|api.?key|credential", re.I)
MAX_EVENTS = 20000
MAX_LOG_BYTES = 32*1024*1024
MAX_TEXT = 16000


def redact(value, secrets=(), depth=0):
    if depth > 20:
        return "[depth limit]"
    if isinstance(value, dict):
        if value.get("type") in {"thinking", "redacted_thinking", "thinking_delta", "signature_delta"}:
            return {"type": "private_content_omitted"}
        return {str(key): "[redacted]" if SENSITIVE.search(str(key)) else
                "[private content omitted]" if key in {"thinking", "signature"} else
                redact(item, secrets, depth+1) for key, item in list(value.items())[:200]}
    if isinstance(value, (list, tuple)):
        return [redact(item, secrets, depth+1) for item in value[:200]]
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, "[redacted]")
        value = re.sub(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?(?:-----END [^-]*PRIVATE KEY-----|$)",
                       "[redacted private key]", value, flags=re.S)
        value = SECRET_BYTES.sub(b"[redacted]", value.encode("utf-8", errors="replace")).decode("utf-8")
        value = re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1[redacted]", value)
        return value[:MAX_TEXT] + (" [truncated; inspect referenced artifacts]" if len(value) > MAX_TEXT else "")
    if value is None or type(value) in (bool, int, float):
        return value
    return redact(str(value), secrets, depth+1)


@contextmanager
def locked(path):
    with no_links(path).open("a+b") as handle:
        handle.seek(0, 2)
        if not handle.tell():
            handle.write(b"0")
            handle.flush()
        acquire, release = file_lock(handle.fileno())
        deadline = time.monotonic()+5
        while True:
            handle.seek(0)
            try:
                acquire()
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK} or time.monotonic() >= deadline:
                    raise Fault("workflow_log_unavailable", "Could not acquire the workflow log lock.") from None
                time.sleep(0.01)
        try:
            yield
        finally:
            handle.seek(0)
            release()


class WorkflowLog:
    def __init__(self, workspace, *, attempt_id=None):
        create = attempt_id is None
        self.attempt_id = str(uuid4()) if create else attempt_id
        try:
            if str(UUID(self.attempt_id)) != self.attempt_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise Fault("invalid_attempt_id", "Use the recorded workflow attempt ID.") from None
        self.directory = no_links(Path(workspace)/".verifier"/"attempts"/self.attempt_id)
        if create:
            self.directory.mkdir(parents=True, exist_ok=False)
            (self.directory/"events").mkdir()
            atomic_write(self.directory/"attempt.json", canonical({"schema_version": 1,
                "attempt_id": self.attempt_id, "created_at": utc_now()}))
        elif not (self.directory/"attempt.json").is_file():
            raise Fault("attempt_not_found", "The supplied workflow attempt does not exist.")
        metadata = json.loads(no_links(self.directory/"attempt.json").read_bytes())
        if metadata.get("attempt_id") != self.attempt_id or metadata.get("schema_version") != 1:
            raise Fault("workflow_log_corrupted", "Workflow attempt metadata does not match its directory.")
        self.secrets = sorted({value for key, value in os.environ.items()
                               if SENSITIVE.search(key) and len(value) >= 4}, key=len, reverse=True)
        from .execution_control import CURRENT
        self.control=CURRENT.get()

    @property
    def paths(self):
        return {"attempt_id": self.attempt_id, "directory": str(self.directory),
                "jsonl_path": str(self.directory/"workflow.jsonl"),
                "markdown_path": str(self.directory/"workflow.md")}

    def emit(self, event, **data):
        try:
            with locked(self.directory/".lock"):
                files = sorted(no_links(self.directory/"events").glob("[0-9]*.json"))
                if len(files) >= MAX_EVENTS:
                    raise Fault("workflow_log_limit", "The workflow event limit was reached.")
                records, previous, total_bytes = [], None, 0
                for sequence, path in enumerate(files, 1):
                    raw=no_links(path).read_bytes()
                    total_bytes+=len(raw)
                    if total_bytes>MAX_LOG_BYTES:
                        raise Fault("workflow_log_limit","The attempt event byte limit was reached.")
                    item = json.loads(raw)
                    content = {key: value for key, value in item.items() if key != "digest"}
                    if (path.name != f"{sequence:08d}.json" or item.get("sequence") != sequence
                            or item.get("attempt_id") != self.attempt_id or item.get("previous_digest") != previous
                            or item.get("digest") != digest(canonical(content))):
                        raise Fault("workflow_log_corrupted", "The workflow event chain failed validation.")
                    records.append(item)
                    previous = item["digest"]
                record = {"schema_version": 1, "attempt_id": self.attempt_id,
                          "sequence": len(files)+1, "created_at": utc_now(), "event": event,
                          "previous_digest": previous, "data": redact(data, self.secrets)}
                record["digest"] = digest(canonical(record))
                payload = canonical(record)
                if len(payload) > 256*1024 or total_bytes+len(payload)>MAX_LOG_BYTES:
                    raise Fault("workflow_log_limit", "A workflow event exceeded its size limit.")
                target = self.directory/"events"/f'{record["sequence"]:08d}.json'
                if target.exists():
                    raise Fault("workflow_log_corrupted", "A workflow sequence already exists.")
                atomic_write(target, payload)
                records.append(record)
                atomic_write(self.directory/"workflow.jsonl", b"".join(canonical(item)+b"\n" for item in records))
                lines = ["# Verification workflow", "", "Attempt: "+self.attempt_id, "",
                         "Observable activity only. Scientific state and results remain in the run journal.", ""]
                for item in records:
                    detail = json.dumps(item["data"], ensure_ascii=False, sort_keys=True)
                    # Indented JSON stays inert even if untrusted output contains Markdown fences/HTML.
                    lines += [f'{item["sequence"]}. {item["created_at"]} - {item["event"]}', "",
                              "       "+detail, ""]
                atomic_write(self.directory/"workflow.md", "\n".join(lines).encode("utf-8"))
                if self.control:
                    self.control.notify(event)
                return record
        except (OSError, ValueError, UnicodeError) as error:
            raise Fault("workflow_log_unavailable", "Workflow log storage is unavailable.") from None


class StreamLog:
    """Log complete public stream messages; never retain partial thinking deltas."""
    def __init__(self, log, role, session_id):
        self.log, self.role, self.session_id = log, role, session_id
        self.pending = {"stdout": bytearray(), "stderr": bytearray()}
        self.received = False
        self.private_key_diagnostic = False

    def __call__(self, stream, chunk):
        self.received = True
        buffer = self.pending[stream]
        buffer.extend(chunk)
        while b"\n" in buffer:
            line, _, rest = buffer.partition(b"\n")
            buffer[:] = rest
            self.line(stream, line)
        if len(buffer) > 1024*1024:
            # Do not emit fragments: a credential could span fragment boundaries.
            raise Fault("workflow_stream_limit", "A process log line exceeded its size limit.")

    def line(self, stream, line):
        if not line.strip():
            return
        if stream == "stderr":
            if b"PRIVATE KEY-----" in line and b"-----BEGIN" in line:
                self.private_key_diagnostic = True
            if self.private_key_diagnostic:
                if b"-----END" in line and b"PRIVATE KEY-----" in line:
                    self.private_key_diagnostic = False
                return
            self.log.emit("process_diagnostic", role=self.role, session_id=self.session_id,
                          text=line.decode("utf-8", errors="replace"))
            return
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            self.log.emit("process_unparsed_output", role=self.role, session_id=self.session_id,
                          bytes=len(line))
            return
        if isinstance(event, dict) and event.get("type") in {"assistant", "user", "result", "system"}:
            self.log.emit("claude_event", role=self.role, session_id=self.session_id, payload=event)

    def close(self):
        for stream, pending in self.pending.items():
            if pending:
                self.line(stream, bytes(pending))
                pending.clear()


def recorded_call(log, runtime, name, arguments, call_id=None):
    if log is None:
        return runtime.call(name, arguments, call_id)
    invocation = str(uuid4())
    started = time.monotonic()
    log.emit("tool_started", tool=name, invocation_id=invocation, arguments=arguments)
    try:
        result = runtime.call(name, arguments, call_id)
    except BaseException as error:
        log.emit("tool_failed", tool=name, invocation_id=invocation,
                 code=getattr(error, "code", type(error).__name__), duration_seconds=time.monotonic()-started)
        raise
    data = result.get("data", {})
    log.emit("tool_finished", tool=name, invocation_id=invocation, status=result.get("status"),
             outcome=data.get("outcome"), error=result.get("error"), run_id=data.get("run_id"),
             duration_seconds=time.monotonic()-started,
             evidence="Full tool request/result is retained by the scientific run journal when committed.")
    return result
