"""Public references a local run fetches, and the task designs it saves for reuse.

Mechanical qualification never grants scientific approval; `local_tasks.py` owns how a task
design qualifies.
"""

import http.client
import ipaddress
import socket
import ssl
import time
from html.parser import HTMLParser
from urllib.parse import urlsplit

from . import __version__
from .common import Fault, canonical, digest
from .ingest import SECRET_BYTES
from .storage import atomic_write, no_links

# The fetch_local_reference section of tool-contracts.md owns both numbers. A page's raw
# size says little about its text, so the page limit is generous and the planner's reply
# is what stays small: a host spills a large reply to a file the planner cannot open.
MAX_REFERENCE = 2 * 1024 * 1024
REPLY_TEXT_BYTES = 40 * 1024


def safe_payload(value):
    if SECRET_BYTES.search(canonical(value)):
        raise Fault("secret_material", "Credential-like content cannot enter saved verifier records.")


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def fetch_bytes(url, *, max_bytes=MAX_REFERENCE, text_only=False):
    """Pin the connection to a checked public IP; no proxy, redirect or DNS rebind."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        raise Fault("reference_url_invalid", "Use a well-formed public HTTPS URL.") from None
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or port not in (None, 443) or parts.fragment or len(url) > 4096
            or any(ord(char) < 33 for char in url)):
        raise Fault("reference_url_invalid", "Use a public HTTPS URL without credentials or fragments.")
    try:
        addresses = socket.getaddrinfo(parts.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise Fault("reference_url_invalid", "Private and special network addresses are not permitted.")
        connection = http.client.HTTPSConnection(parts.hostname, timeout=20)
        connection.sock = ssl.create_default_context().wrap_socket(
            socket.create_connection((addresses[0][4][0], 443), timeout=20),
            server_hostname=parts.hostname)
        try:
            target = parts.path or "/"
            if parts.query:
                target += "?" + parts.query
            connection.request("GET", target, headers={"User-Agent": "scientific-verifier-local/" + __version__,
                                                        "Accept-Encoding": "identity"})
            response = connection.getresponse()
            if response.status != 200:
                raise Fault("reference_unavailable", "Reference must return HTTP 200 without redirection.")
            content_type = response.getheader("Content-Type", "").lower()
            if text_only and not any(value in content_type for value in ("text/", "json", "xml")):
                raise Fault("reference_unsupported", "Local v1 reads text/JSON/XML references only.")
            chunks, count, deadline = [], 0, time.monotonic() + 20
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise OSError("Reference deadline exceeded")
                if connection.sock:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(min(8192, max_bytes + 1 - count))
                if not chunk:
                    break
                chunks.append(chunk)
                count += len(chunk)
                if count > max_bytes:
                    break
            raw = b"".join(chunks)
        finally:
            connection.close()
    except (OSError, http.client.HTTPException, ValueError):
        raise Fault("reference_unavailable", "The bounded public reference download failed.") from None
    return bounded_download(raw, max_bytes), content_type


def bounded_download(raw, max_bytes):
    """Refuse an oversized or credential-bearing download, and say which.

    One message used to cover both, so run b0955d2f's planner could only guess why two
    pages were refused, and its guess reached the documentary packet as fact.
    """
    if len(raw) > max_bytes:
        raise Fault("reference_too_large", "The download is larger than its " + str(max_bytes) + "-byte limit.")
    if SECRET_BYTES.search(raw):
        raise Fault("reference_credential_material", "The download contains credential-like material and was not kept.")
    return raw


def reply_text(text):
    """The part of a page's text a tool reply may carry, and its full size when cut."""
    raw = text.encode("utf-8")
    if len(raw) <= REPLY_TEXT_BYTES:
        return text, None
    # Cut on a character boundary; the pinned reference keeps every byte.
    return raw[:REPLY_TEXT_BYTES].decode("utf-8", errors="ignore"), len(raw)


def fetch_public(url):
    raw,content_type=fetch_bytes(url,text_only=True)
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        raise Fault("reference_unsupported", "Reference must be UTF-8 text.") from None
    if "html" in content_type:
        parser = PageText()
        parser.feed(text)
        text = "\n".join(parser.parts)
    return raw, text


def reference_refs(candidate):
    """Every reference a task design rests on: its model, its quoted values and rules, its input files."""
    from .local_tasks import reference_refs as task_refs
    return task_refs(candidate)


def save_candidate(store, candidate):
    key = store.put_json(candidate)
    path = no_links(store.root / "candidates" / (key + ".json"))
    atomic_write(path, canonical(candidate))
    return key


def candidates(store):
    directory = no_links(store.root / "candidates")
    found = []
    if directory.exists():
        for path in sorted(directory.glob("*.json"))[:200]:
            raw = no_links(path).read_bytes()
            if digest(raw) != path.stem:
                raise Fault("candidate_integrity", "A local candidate projection was changed.", fatal=True)
            candidate = store.get_json(path.stem)
            from .local_tasks import METHOD_VERSION
            # Designs of questions and generated evaluators saved before 2026-10-05 stay on disk, unlisted.
            if candidate["status"] == "qualified_local" and candidate["method_version"] == METHOD_VERSION:
                found.append({"candidate_ref": path.stem, "name": candidate["name"],
                              "scope": candidate["scope"], "method": candidate["method"],
                              "limitations": candidate["limitations"], "scientific_approval": "provisional"})
                from .local_science import fingerprint
                found[-1]["candidate_fingerprint"]=fingerprint(candidate)
    return found
