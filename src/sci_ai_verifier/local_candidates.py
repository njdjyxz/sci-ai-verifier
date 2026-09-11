"""Data-only local candidates. Mechanical qualification never grants scientific approval."""

import http.client
import ipaddress
import re
import socket
import ssl
import time
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .common import Fault, canonical, digest, utc_now
from .ingest import SECRET_BYTES
from .storage import atomic_write, no_links

MAX_REFERENCE = 256 * 1024
METHOD_VERSION = "local-reference-comparison-1"
TOLERANCE = Decimal("0.000001")
QUALIFICATION_LIMITS = [
    "Mechanical qualification only; source authority and input/reference applicability are planner assertions.",
    "Cases are illustrative, not a representative scientific benchmark.",
    "No scientific verdict or evidence grade is authorized by this local method.",
]


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


def fetch_public(url):
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
            connection.request("GET", target, headers={"User-Agent": "scientific-verifier-local/0.6",
                                                        "Accept-Encoding": "identity"})
            response = connection.getresponse()
            if response.status != 200:
                raise Fault("reference_unavailable", "Reference must return HTTP 200 without redirection.")
            content_type = response.getheader("Content-Type", "").lower()
            if not any(value in content_type for value in ("text/", "json", "xml")):
                raise Fault("reference_unsupported", "Local v1 reads text/JSON/XML references only.")
            chunks, count, deadline = [], 0, time.monotonic() + 20
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise OSError("Reference deadline exceeded")
                if connection.sock:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(min(8192, MAX_REFERENCE + 1 - count))
                if not chunk:
                    break
                chunks.append(chunk)
                count += len(chunk)
                if count > MAX_REFERENCE:
                    break
            raw = b"".join(chunks)
        finally:
            connection.close()
    except (OSError, http.client.HTTPException, ValueError):
        raise Fault("reference_unavailable", "The bounded public reference download failed.") from None
    if len(raw) > MAX_REFERENCE or SECRET_BYTES.search(raw):
        raise Fault("reference_rejected", "Reference exceeds its byte limit or contains credential-like material.")
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        raise Fault("reference_unsupported", "Reference must be UTF-8 text.") from None
    if "html" in content_type:
        parser = PageText()
        parser.feed(text)
        text = "\n".join(parser.parts)
    return raw, text


def number(text):
    if not isinstance(text, str) or not re.fullmatch(r"[+-]?(?:\d{1,32}(?:\.\d{0,32})?|\.\d{1,32})(?:[eE][+-]?\d{1,2})?", text.strip()):
        raise ValueError("Not a bounded decimal")
    try:
        value = Decimal(text.strip())
        if not value.is_finite():
            raise ValueError("Not finite")
        return value
    except InvalidOperation:
        raise ValueError("Not a decimal") from None


def compare(method, actual, expected):
    if method == "exact":
        return "pass" if actual.strip() == expected.strip() else "fail"
    if method != "numeric":
        raise ValueError("Unknown installed comparison method")
    try:
        return "pass" if abs(number(actual) - number(expected)) <= TOLERANCE else "fail"
    except ValueError:
        return "invalid"


def qualify(proposal, references):
    safe_payload(proposal)
    problems, controls = [], []
    method = proposal["method"]
    if method not in {"exact", "numeric"}:
        problems.append("Only installed exact and numeric comparison methods are available.")
    if len({case["input"] for case in proposal["cases"]}) != len(proposal["cases"]):
        problems.append("Case inputs must be distinct.")
    for case in proposal["cases"]:
        reference = references.get(case["reference_ref"])
        if (not reference or case["source_quote"] not in reference["text"]
                or case["expected"].strip() not in case["source_quote"]):
            problems.append("Each expected value needs an exact quote from a fetched reference.")
            continue
        if not case["expected"].strip():
            problems.append("Expected answers cannot be blank.")
            continue
        if method not in {"exact", "numeric"}:
            continue
        expected = case["expected"]
        if method == "numeric":
            try:
                center = number(expected)
            except ValueError:
                problems.append("Numeric expected answers must be bounded plain decimal numbers.")
                continue
            if not re.search(r"(?<![\w.+-])" + re.escape(expected.strip()) + r"(?!\w|\.\d)", case["source_quote"]):
                problems.append("Expected numeric values must be complete tokens in the reference quote.")
                continue
            probes = [(expected, "pass"), (str(center + TOLERANCE), "pass"),
                      (str(center - TOLERANCE), "pass"), (str(center + 2*TOLERANCE), "fail"),
                      (str(center - 2*TOLERANCE), "fail"), ("not-a-number", "invalid")]
        else:
            probes = [(expected, "pass"), (expected + " __incorrect_control__", "fail")]
        passed = all(compare(method, actual, expected) == wanted for actual, wanted in probes)
        controls.append({"case_id": case["case_id"], "passed": passed,
                         "positive_negative_boundary_checks": len(probes)})
        if not passed:
            problems.append("A comparison control failed.")
    if len({case["case_id"] for case in proposal["cases"]}) != len(proposal["cases"]):
        problems.append("Case IDs must be unique.")
    return {"schema_version": 1, "method_version": METHOD_VERSION, **proposal,
            "status": "rejected" if problems else "qualified_local",
            "scientific_approval": "provisional", "qualification_problems": sorted(set(problems)),
            "controls": controls, "qualification_limitations": QUALIFICATION_LIMITS,
            "qualified_at": utc_now(), "absolute_tolerance": str(TOLERANCE) if method == "numeric" else None}


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
            if candidate["status"] == "qualified_local" and candidate["method_version"] == METHOD_VERSION:
                found.append({"candidate_ref": path.stem, "name": candidate["name"],
                              "scope": candidate["scope"], "method": candidate["method"],
                              "limitations": candidate["limitations"], "scientific_approval": "provisional"})
    return found
