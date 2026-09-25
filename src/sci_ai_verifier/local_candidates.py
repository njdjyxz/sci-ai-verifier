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

from . import __version__
from .common import Fault, canonical, digest, utc_now
from .ingest import SECRET_BYTES
from .storage import atomic_write, no_links

# The fetch_local_reference section of tool-contracts.md owns both numbers. A page's raw
# size says little about its text, so the page limit is generous and the planner's reply
# is what stays small: a host spills a large reply to a file the planner cannot open.
MAX_REFERENCE = 2 * 1024 * 1024
REPLY_TEXT_BYTES = 40 * 1024
# Bumped when qualification rules change, because a locally saved candidate is reused by
# lookup without being re-qualified: only this string keeps one that passed superseded
# rules out of a later run. -2 added the answer-form rule; -3 replaced its string-matched
# closed choice with the indexed `choice` method; -4 reads numeric replies through
# reply_number() and adds the controls that prove it; -5 reads exact replies from their
# first line and requires a design's choice answers to vary in position; -6 rejects a
# correct option that alone starts differently from the others or alone repeats a word
# from the question.
METHOD_VERSION = "local-reference-comparison-6"
# Reserved final option. Never the answer, so scoring stays ungameable, but a case whose
# trials all select it is far more likely to have a broken option set than a wrong subject.
NONE_OF_THESE = "none of these"
# Four real alternatives plus the reserved one. Two options let a coin flip carry a case
# 12.5% of the time across three trials; four drops that to 1.6%.
MINIMUM_OPTIONS = 5
TOLERANCE = Decimal("0.000001")
QUALIFICATION_LIMITS = [
    "Mechanical qualification only; source authority and input/reference applicability are planner assertions.",
    "Cases are illustrative, not a representative scientific benchmark.",
    "Qualification alone carries no scientific verdict or evidence grade; the grade is settled separately.",
    "Choice options are checked for distinctness, count, presence in the prompt, a correct "
    "option that neither alone starts differently from the others nor alone repeats a word of "
    "the question, and a varied answer position across the design, not for being genuinely "
    "wrong or plausible; a subject that recognises the conventional-looking option can pass "
    "without knowing, and distractor quality remains a planner assertion.",
]
# Words too common to mark an option when the question shares them: function words and the
# reply instructions every choice case carries ("Reply with the number of the correct option
# on the first line, and nothing else on that line").
COMMON_WORDS = {"about", "above", "after", "also", "answer", "before", "being", "below", "been", "both",
                "correct", "could", "does", "each", "else", "every", "first", "following", "from", "have",
                "into", "line", "more", "most", "must", "none", "nothing", "number", "once", "only",
                "option", "other", "reply", "same", "should", "some", "such", "than", "that", "their",
                "them", "then", "there", "these", "they", "this", "those", "were", "what", "when", "where",
                "which", "will", "with", "would", "your"}


def content_words(text):
    """The words of four letters or more, one form per word: `CompleteRingsOnly` gives
    complete and ring, `queries` gives query, so a question and an option compare as a
    reader matching them would."""
    found = set()
    for word in re.findall(r"[A-Za-z]+", re.sub(r"([a-z])([A-Z])", r"\1 \2", text)):
        word = word.lower()
        if len(word) < 4 or word in COMMON_WORDS:
            continue
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith(("sses", "shes", "ches", "xes", "zes")):
            word = word[:-2]
        elif word.endswith("s") and not word.endswith("ss") and len(word) > 4:
            word = word[:-1]
        found.add(word)
    return found


def lone_echo(text, options, index):
    """The question's words that only the correct option repeats, sorted; empty when none.

    Run 3b3f3c94 keyed "results cannot include lone ring atoms" to a question naming
    `CompleteRingsOnly`, the only option mentioning rings, and its critique counted it.
    """
    question = text
    for value in sorted(options, key=len, reverse=True):
        question = question.replace(value, " ")
    others = set().union(*(content_words(value) for number, value in enumerate(options[:-1], 1)
                           if number != index))
    return sorted((content_words(options[index - 1]) & content_words(question)) - others)


def lone_start(options, index):
    """How the correct option alone starts differently from every other one, or `None`.

    Run 84e90683's key was the one option without a leading "the", and run 31b67427's
    critique counted another such key. A reader spots the answer without knowing the claim.
    """
    def first(value):
        return (value.split() or [""])[0]
    key = options[index - 1]
    others = [value for number, value in enumerate(options[:-1], 1) if number != index]
    words = {first(value).lower() for value in others}
    if len(words) == 1 and first(key).lower() not in words:
        return ("starts with " + repr(first(key)) + " where every other option starts with "
                + repr(first(others[0])))
    capitals = {value[:1].isupper() for value in others}
    if len(capitals) == 1 and key[:1].isupper() not in capitals:
        return "is the only option " + ("capitalised" if key[:1].isupper() else "not capitalised")
    return None


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


def reply_number(text):
    """The number a subject's reply gives: presentation removed, content never searched.

    Live run 7efbdd8c answered 57 of 57 cases correctly and still scored five invalid,
    because the subject wrote `**1**` and sometimes explained itself below. So the first
    non-empty line is read, with whitespace and markdown emphasis stripped from its
    ends. Nothing is extracted from inside it: `The answer is 1` stays invalid, since
    pulling a number out of prose is how a wrong reply becomes a false pass. A number
    cannot contain these characters, so stripping them cannot change its meaning.
    """
    return number(first_line(text).strip("*_`").strip())


def first_line(text):
    """The first non-empty line of a reply, with surrounding whitespace removed."""
    lines = [line for line in text.strip().split("\n") if line.strip()]
    return lines[0].strip() if lines else ""


def presentation_probes(answer):
    """Controls proving reply_number(): a formatted right answer reads as right, and a
    sentence containing the right answer does not -- the guard against greedy parsing."""
    return [("**%s**" % answer, "pass"),
            ("**%s**\n\nThe reference states this value." % answer, "pass"),
            ("The answer is %s" % answer, "invalid")]


INSTALLED_METHODS = ("exact", "numeric", "choice")


def case_method(candidate, case):
    """The comparison a case is scored with. A `mixed` design names one per case; any
    other design names one for all of them, and its cases carry none, so each case has
    exactly one source for its method."""
    return case.get("method") if candidate["method"] == "mixed" else candidate["method"]


def compare(method, actual, expected):
    if method == "exact":
        # Read from the first line like the numeric methods, so an explanation below the
        # answer cannot fail it: run 0a243b7e scored six correct `R1`-style answers as
        # fails. Characters are never removed: `_` and `*` are content here --
        # `rgroup_label`, SMARTS `[*]` -- so `**R1**` still fails.
        return "pass" if first_line(actual) == expected.strip() else "fail"
    if method == "choice":
        # The reply is an option number, so no wording, casing or plural of a right
        # answer can score as a wrong one. A reply that is not a number is `invalid`,
        # which reports a harness problem rather than a verdict about the skill.
        try:
            return "pass" if reply_number(actual) == number(expected) else "fail"
        except ValueError:
            return "invalid"
    if method != "numeric":
        raise ValueError("Unknown installed comparison method")
    try:
        return "pass" if abs(reply_number(actual) - number(expected)) <= TOLERANCE else "fail"
    except ValueError:
        return "invalid"


def forced_surface_form(text):
    """True when an open answer has exactly one way to write it.

    A number, or a token whose own casing is fixed by a case change, digit or
    underscore. A plain single-case word like `molar` is not: a subject answering in
    one word naturally capitalises it, and string equality then reports a correct
    answer as wrong. Those belong in an indexed choice.
    """
    if not text or re.search(r"\s", text):
        return False
    try:
        number(text)
        return True
    except ValueError:
        pass
    return bool(re.search(r"[0-9_]", text) or (re.search(r"[a-z]", text) and re.search(r"[A-Z]", text)))


def qualify(proposal, references):
    from .common import validate
    from .local import schemas
    from .tools import obj,string
    validate({**proposal,"claim_id":"candidate"},schemas({},obj,string)["qualify_local_candidate"])
    safe_payload(proposal)
    problems, controls, positions = [], [], []
    design = proposal["method"]
    if design not in {*INSTALLED_METHODS, "mixed"}:
        problems.append("Only installed exact, numeric and choice comparison methods, or a mixed design of them, are available.")
    if len({case["input"] for case in proposal["cases"]}) != len(proposal["cases"]):
        problems.append("Case inputs must be distinct.")
    for case in proposal["cases"]:
        reference = references.get(case["reference_ref"])
        expected = case["expected"]
        trimmed = expected.strip()
        options = [value.strip() for value in case.get("options", [])]
        if not trimmed:
            problems.append("Expected answers cannot be blank.")
            continue
        if (design == "mixed") != ("method" in case):
            problems.append("In a mixed design every case names its method; in any other design no case does.")
            continue
        method = case_method(proposal, case)
        if method not in INSTALLED_METHODS:
            continue
        if method != "choice" and options:
            problems.append("Only the choice method takes options; an open answer is compared directly.")
            continue
        # The answer key must come from the retrieved bytes rather than the planner. For a
        # choice the index is the planner's own ordering, so the option it selects carries
        # that guarantee instead: same anchor, one level down.
        answer = trimmed
        if method == "choice":
            # A case marked choice with no options used to crash on options[-1] and reached the
            # planner of run 74eadedd twice as a bare internal error; now it is told what is missing.
            if not options:
                problems.append("A choice case lists its options in `options`, the last being the reserved "
                                + repr(NONE_OF_THESE) + ".")
                continue
            # The option count is enforced by the schema this function validates against.
            if len(set(options)) != len(options):
                problems.append("Choice options must be distinct.")
                continue
            if options[-1] != NONE_OF_THESE:
                problems.append("The last option must be the reserved " + repr(NONE_OF_THESE) + " and is never the answer.")
                continue
            try:
                index = int(number(trimmed))
            except ValueError:
                index = 0
            if str(index) != trimmed or not 1 <= index < len(options):
                problems.append("A choice answer must be the 1-based number of an option, never the reserved last one.")
                continue
            absent = [value for value in options if value not in case["input"]]
            if absent:
                problems.append("Every option must appear verbatim in the case input.")
                continue
            style = lone_start(options, index)
            if style:
                problems.append("In case " + case["case_id"] + " the correct option " + style + ", so its "
                                "style marks it as the answer. Write every option in the style of the quoted key.")
                continue
            echoed = lone_echo(case["input"], options, index)
            if echoed:
                problems.append("In case " + case["case_id"] + " only the correct option repeats "
                                + ", ".join(repr(word) for word in echoed) + " from the question, so a reader can "
                                "match words instead of knowing the claim. Use the word in other options too, or "
                                "keep it out of the question.")
                continue
            answer = options[index - 1]
        if (not reference or case["source_quote"] not in reference["text"]
                or answer not in case["source_quote"]):
            problems.append("Each expected value needs an exact quote from a fetched reference.")
            continue
        if method == "numeric":
            try:
                center = number(expected)
            except ValueError:
                problems.append("Numeric expected answers must be bounded plain decimal numbers.")
                continue
            if not re.search(r"(?<![\w.+-])" + re.escape(trimmed) + r"(?!\w|\.\d)", case["source_quote"]):
                problems.append("Expected numeric values must be complete tokens in the reference quote.")
                continue
            probes = [(expected, "pass"), (str(center + TOLERANCE), "pass"),
                      (str(center - TOLERANCE), "pass"), (str(center + 2*TOLERANCE), "fail"),
                      (str(center - 2*TOLERANCE), "fail"), ("not-a-number", "invalid")]
            probes += presentation_probes(trimmed)
        elif method == "choice":
            positions.append(index)
            # Every other option number must be rejected, including the reserved one, so a
            # case has to separate its own alternatives; a non-numeric reply is `invalid`.
            probes = [(expected, "pass"), ("not-a-number", "invalid"), (str(len(options) + 1), "fail")]
            probes += [(str(other), "fail") for other in range(1, len(options) + 1) if other != index]
            probes += presentation_probes(trimmed)
        else:
            if not forced_surface_form(trimmed):
                problems.append("An open answer must have one possible surface form -- a number, or a "
                                "token fixed by a case change, digit or underscore. Use an indexed choice.")
                continue
            # A single appended-suffix probe only tests that `==` works. Probe a
            # prefix, a suffix and a truncation so a near miss has to be rejected.
            probes = [(expected, "pass"), (expected + " __incorrect_control__", "fail"),
                      ("__incorrect_control__ " + expected, "fail"),
                      (trimmed[:-1] or "__empty_control__", "fail"),
                      # The answer on its own line with an explanation below it passes; the
                      # answer inside a sentence does not, since nothing is searched for.
                      (trimmed + "\n\nThe reference spells it this way.", "pass"),
                      ("The answer is " + trimmed, "fail")]
        passed = all(compare(method, actual, expected) == wanted for actual, wanted in probes)
        controls.append({"case_id": case["case_id"], "passed": passed,
                         "positive_negative_boundary_checks": len(probes)})
        if not passed:
            problems.append("A comparison control failed.")
    if len({case["case_id"] for case in proposal["cases"]}) != len(proposal["cases"]):
        problems.append("Case IDs must be unique.")
    # All eleven choice cases of run 0a243b7e answered option 1, so a subject that always
    # picks the first option would have passed every one of them.
    if len(positions) > 1 and len(set(positions)) == 1:
        problems.append("Vary which option position holds the correct answer across the design's choice "
                        "cases: with every answer at position " + str(positions[0]) + ", a subject that "
                        "always picks that position passes every case.")
    return {"schema_version": 1, "method_version": METHOD_VERSION, **proposal,
            "status": "rejected" if problems else "qualified_local",
            "scientific_approval": "provisional", "qualification_problems": sorted(set(problems)),
            "controls": controls, "qualification_limitations": QUALIFICATION_LIMITS,
            "qualified_at": utc_now(),
            "absolute_tolerance": str(TOLERANCE) if any(case_method(proposal, case) == "numeric"
                                                        for case in proposal["cases"]) else None}


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
            from .local_evaluators import METHOD_VERSION as PYTHON_VERSION
            if candidate["status"] == "qualified_local" and candidate["method_version"] in {METHOD_VERSION,PYTHON_VERSION}:
                found.append({"candidate_ref": path.stem, "name": candidate["name"],
                              "scope": candidate["scope"], "method": candidate["method"],
                              "limitations": candidate["limitations"], "scientific_approval": "provisional"})
                from .local_science import fingerprint
                found[-1]["candidate_fingerprint"]=fingerprint(candidate)
    return found
