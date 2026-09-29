"""Data-only local candidates. Mechanical qualification never grants scientific approval."""

import http.client
import ipaddress
import re
import socket
import ssl
import time
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

from . import __version__
from .answers import (NONE_OF_THESE, TOLERANCE, TYPES, compare, in_quote, item_type, key_items, key_problem,
                      number, parsed, probe_passed, probes, singular, whole_token_in)
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
# from the question; -7 adds the term, expression, list and set answer types, a numeric
# unit, and the reader and controls of answers.py.
METHOD_VERSION = "local-reference-comparison-7"
# Four real alternatives plus the reserved one. Two options let a coin flip carry a case
# 12.5% of the time across three trials; four drops that to 1.6%.
MINIMUM_OPTIONS = 5
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
        if len(word) >= 4 and word not in COMMON_WORDS:
            found.add(singular(word))
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


INSTALLED_METHODS = TYPES


def case_method(candidate, case):
    """The comparison a case is scored with. A `mixed` design names one per case; any
    other design names one for all of them, and its cases carry none, so each case has
    exactly one source for its method."""
    return case.get("method") if candidate["method"] == "mixed" else candidate["method"]


def case_compare(candidate, case, text):
    """One reply to one case, read by the case's own answer type ("Reading a reply" in tool-contracts.md)."""
    return compare(case_method(candidate, case), text, case["expected"], case.get("options"), case.get("unit"))


# A number's complete-token test is every value's: `1.0` is not read out of `21.09`.
whole_number_in = whole_token_in


def at_precision(value, printed):
    """`value` rounded half away from zero to the last place `printed` shows: 7.522879 at
    `7.5` is 7.5. `None` when the rounded value cannot be represented."""
    try:
        return number(value).quantize(Decimal(1).scaleb(number(printed).as_tuple().exponent), rounding=ROUND_HALF_UP)
    except (ValueError, InvalidOperation):
        return None


def reference_refs(candidate):
    """Every reference a candidate's answers rest on: its cases' and its calculation's anchors'."""
    refs = [case["reference_ref"] for case in candidate["cases"] if case.get("reference_ref")]
    calculation = candidate.get("calculation")
    if calculation:
        refs += [calculation["reference_ref"], *(anchor["reference_ref"] for anchor in calculation["anchors"])]
    return list(dict.fromkeys(refs))


def calculated(proposal, references, calculate, problems):
    """The expected answer and quote Python supplies for each calculated case, and the receipts.

    `qualify_local_candidate` in tool-contracts.md owns the rule. `calculate(code, inputs)`
    runs the planner's program once per distinct input and returns what each printed.
    Problems are appended to `problems`; a case whose answer was not calculated is left out.
    """
    calculation = proposal.get("calculation")
    wanted = [case for case in proposal["cases"] if "arguments" in case or "decimals" in case]
    if not calculation or not wanted:
        if calculation or wanted:
            problems.append("A calculation keys at least one case, and a case with arguments needs the design's calculation.")
        return {}, None
    formula = references.get(calculation["reference_ref"])
    if not formula or calculation["formula_quote"] not in formula["text"]:
        problems.append("The calculation's formula must be quoted exactly from a fetched reference.")
        return {}, None
    if any("arguments" not in case or "decimals" not in case or case.get("options")
           or case_method(proposal, case) != "numeric" for case in wanted):
        problems.append("Only a numeric case may be calculated, and it gives both arguments and decimals.")
        return {}, None
    for anchor in calculation["anchors"]:
        reference = references.get(anchor["reference_ref"])
        try:
            number(anchor["expected"])
        except ValueError:
            reference = None
        if (not reference or anchor["source_quote"] not in reference["text"]
                or not whole_number_in(anchor["expected"].strip(), anchor["source_quote"])):
            problems.append("Each anchor is a worked example: its expected value must be a complete number in an "
                            "exact quote from a fetched reference.")
            return {}, None
    if calculate is None:
        problems.append("Calculated answers need the operator's pinned sandbox image.")
        return {}, None
    inputs = list(dict.fromkeys([anchor["arguments"] for anchor in calculation["anchors"]]
                                + [case["arguments"] for case in wanted]))
    receipts = calculate(calculation["code"], inputs)
    outputs = receipts["outputs"]
    anchors = []
    for anchor in calculation["anchors"]:
        printed = outputs.get(anchor["arguments"])
        reproduced = printed is not None and at_precision(printed, anchor["expected"]) == number(anchor["expected"])
        anchors.append({**anchor, "output": printed, "reproduced": reproduced})
        if not reproduced:
            problems.append("The calculation gives " + (repr(printed) if printed is not None else "no number")
                            + " for the anchor with arguments " + repr(anchor["arguments"]) + ", where its reference "
                            "prints " + repr(anchor["expected"]) + ".")
    receipts = {**receipts, "anchors": anchors}
    if not all(item["reproduced"] for item in anchors):
        return {}, receipts
    keyed = {}
    for case in wanted:
        printed = outputs.get(case["arguments"])
        value = at_precision(printed, "1e-" + str(case["decimals"])) if printed is not None else None
        if value is None:
            problems.append("The calculation printed no usable number for case " + case["case_id"] + ".")
            continue
        supplied = {"expected": str(value), "reference_ref": calculation["reference_ref"],
                    "source_quote": calculation["formula_quote"]}
        if any(key in case and case[key] != supplied[key] for key in supplied):
            problems.append("Python supplies a calculated case's expected, reference_ref and source_quote; omit them "
                            "from case " + case["case_id"] + ".")
            continue
        keyed[case["case_id"]] = supplied
    return keyed, receipts


def recorded(candidate):
    """A calculator that answers from a saved candidate's receipts, so selection re-checks it
    without running the program again."""
    receipts = candidate.get("calculation_receipts") or {}

    def replay(code, inputs):
        if (digest(code.encode("utf-8")) != receipts.get("code_sha256")
                or any(value not in receipts.get("outputs", {}) for value in inputs)):
            raise Fault("candidate_integrity", "A calculated candidate's program or outputs changed.", fatal=True)
        return {key: receipts[key] for key in ("code_sha256", "image_id", "outputs")}
    return replay


def qualify(proposal, references, calculate=None):
    """Check a proposed design mechanically. `calculate` runs a calculation's program; see `calculated`."""
    from .common import validate
    from .local import schemas
    from .tools import obj,string
    validate({**proposal,"claim_id":"candidate"},schemas({},obj,string)["qualify_local_candidate"])
    safe_payload(proposal)
    problems, controls, positions = [], [], []
    design = proposal["method"]
    if design not in {*INSTALLED_METHODS, "mixed"}:
        problems.append("Only the installed comparison methods (" + ", ".join(INSTALLED_METHODS) + "), or a mixed "
                        "design of them, are available.")
    if len({case["input"] for case in proposal["cases"]}) != len(proposal["cases"]):
        problems.append("Case inputs must be distinct.")
    keyed, receipts = calculated(proposal, references, calculate, problems)
    cases = [{**case, **keyed.get(case["case_id"], {})} for case in proposal["cases"]]
    for case in cases:
        if "arguments" in case and case["case_id"] not in keyed:
            continue  # Its answer was not calculated, and `calculated` said why.
        if not all(case.get(key) for key in ("expected", "reference_ref", "source_quote")):
            problems.append("A case Python does not calculate needs its expected answer, reference_ref and source_quote.")
            continue
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
        if method != "numeric" and "unit" in case:
            problems.append("Only a numeric case takes a unit.")
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
            # The option count is enforced by the schema this function validates against. A reply
            # may name an option by its text regardless of case, so case alone cannot tell two apart.
            if len({value.casefold() for value in options}) != len(options):
                problems.append("Choice options must be distinct, and not only in their case.")
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
            # A reply of that number would name the option at that position, not this text.
            numbered = [(value, position) for position, value in enumerate(options, 1)
                        if parsed(value) is not None and parsed(value) == parsed(value).to_integral_value()
                        and 1 <= parsed(value) <= len(options) and parsed(value) != position]
            if numbered:
                value, position = numbered[0]
                problems.append("In case " + case["case_id"] + " option " + str(position) + ", " + repr(value)
                                + ", reads as the number of option " + str(int(parsed(value))) + ", so a reply of it "
                                "names two options. Write it with its unit or in words, or put it at that position.")
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
        # A calculated answer's provenance is its quoted formula and reproduced anchors.
        quoted = "arguments" not in case
        if quoted and (not reference or case["source_quote"] not in reference["text"]
                       or not in_quote(method, answer, case["source_quote"])):
            problems.append("Each expected value needs an exact quote from a fetched reference"
                            + (": a term's words, and each item, must appear in it." if method in ("term", "list", "set")
                               else "."))
            continue
        problem = key_problem(method, case)
        if problem:
            problems.append("Case " + case["case_id"] + ": " + problem)
            continue
        if method == "numeric" and quoted and not whole_number_in(trimmed, case["source_quote"]):
            problems.append("Expected numeric values must be complete tokens in the reference quote.")
            continue
        if method == "choice":
            positions.append(index)
        # Controls ("Reading a reply" in tool-contracts.md): the answer in every form the reader
        # accepts must pass, and near misses -- a sentence, a suffix, a truncation, every other
        # option, the tolerance boundary -- must not.
        checks = probes(method, case)
        passed = all(probe_passed(compare(method, actual, expected, options or None, case.get("unit")), wanted)
                     for actual, wanted in checks)
        controls.append({"case_id": case["case_id"], "passed": passed,
                         "positive_negative_boundary_checks": len(checks)})
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
    return {"schema_version": 1, "method_version": METHOD_VERSION, **proposal, "cases": cases,
            **({"calculation_receipts": receipts} if receipts else {}),
            "status": "rejected" if problems else "qualified_local",
            "scientific_approval": "provisional", "qualification_problems": sorted(set(problems)),
            "controls": controls, "qualification_limitations": QUALIFICATION_LIMITS,
            "qualified_at": utc_now(),
            "absolute_tolerance": str(TOLERANCE) if any(
                case_method(proposal, case) == "numeric" or (case_method(proposal, case) in ("list", "set") and any(
                    item_type(item) == "numeric" for item in key_items(case.get("expected") or "")))
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
