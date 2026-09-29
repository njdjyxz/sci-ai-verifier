"""How a subject's reply is read and compared, one installed answer type at a time.

`qualify_local_candidate` in tool-contracts.md owns the answer types, the reading rules and the
controls; this module implements them. Python finds a reply's answer line -- inside a code fence,
past an `Answer:` label, above any explanation -- and reads it whole, then again with one layer of
presentation taken off both ends at a time. Nothing is ever searched for inside the line, because
extracting an answer from prose is how a wrong reply becomes a false pass. A reply this reader
does not pass goes on to the AI reader ("Reading replies" in local-contract.md).
"""

import ast
import re
import unicodedata
import warnings
from decimal import Decimal, InvalidOperation

from .common import FENCE, fenced_blocks, normalize

# `choice` last: every other type makes the subject produce the answer, which "Answer form" in
# evidence-rubric.md calls generated.
TYPES = ("numeric", "exact", "term", "expression", "list", "set", "choice")
OPEN_TYPES = TYPES[:-1]
TOLERANCE = Decimal("0.000001")
# Reserved final option. Never the answer, so scoring stays ungameable, but a case whose
# trials all select it is far more likely to have a broken option set than a wrong subject.
NONE_OF_THESE = "none of these"
MAX_TERM_WORDS = 8
MAX_ITEMS = 20
MAX_EXPRESSION = 1000
MAX_UNIT = 20
# `Answer: 7.6`, `**Final answer:** 7.6`, `**Answer**: 7.6`; and a label alone on its line.
# Emphasis closing a label must be followed by a space, so `Answer: __init__` keeps its underscores.
LABEL = re.compile(r"[#>*_\s]*(?:final\s+)?answer\s*[*_]*\s*[:：]\s*(?:[*_]+\s+)?(.*)", re.IGNORECASE)
BARE_LABEL = re.compile(r"[#>*_\s]*(?:final\s+)?answer[*_:：\s]*", re.IGNORECASE)
# Wrappers taken off both ends, one layer per reading. Inline code is handled on its own,
# because its delimiter is any run of backticks.
WRAPPERS = (("**", "**"), ("__", "__"), ("*", "*"), ("_", "_"),
            ('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"))
INLINE_CODE = re.compile(r"(`+)(.+)\1", re.DOTALL)
BULLET = re.compile(r"\s{0,3}(?:[-*+•]|\d{1,2}[.)])\s+(.+)")
OPTION = re.compile(r"(?:option\s*)?[(\[]?\s*(\d{1,2})\s*[)\].:]?(?:\s+(.+))?", re.IGNORECASE)
MINUS = str.maketrans({"−": "-", "‒": "-", "–": "-", "﹣": "-", "－": "-",
                       " ": " ", " ": " ", " ": " "})
WORD = re.compile(r"[^\W_]+")
ARTICLES = {"a", "an", "the"}
# A term is words, spaces, hyphens and apostrophes; anything else carries meaning a term drops.
TERM_TEXT = re.compile(r"(?:[^\W_]|[\s'’‐‑‒–—-])+")
FORMS = {"numeric": "the number", "choice": "the number of the correct option",
         "exact": "the exact token, written as it appears in code or data",
         "term": "the term", "expression": "the Python expression, on one line and not in a code block",
         "list": "the items in order, separated by commas", "set": "the items in any order, separated by commas"}


def number(text):
    """A bounded plain decimal, or ValueError."""
    if not isinstance(text, str) or not re.fullmatch(r"[+-]?(?:\d{1,32}(?:\.\d{0,32})?|\.\d{1,32})(?:[eE][+-]?\d{1,2})?", text.strip()):
        raise ValueError("Not a bounded decimal")
    try:
        value = Decimal(text.strip())
        if not value.is_finite():
            raise ValueError("Not finite")
        return value
    except InvalidOperation:
        raise ValueError("Not a decimal") from None


def parsed(text):
    """`number(text)`, or `None` when it is not one."""
    try:
        return number(text)
    except ValueError:
        return None


def whole_token_in(value, quote):
    """True when `value` is the whole quote, or appears in it as a complete token rather than
    inside a longer one: `1.0` is not read out of `21.09`."""
    value = value.strip()
    if not value:
        return False
    if value == quote.strip():
        return True
    return bool(re.search(r"(?<![\w.+-])" + re.escape(value) + r"(?!\w|\.\d)", quote))


def singular(word):
    """One form per word, so a plural and its singular compare equal: `queries` gives `query`."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("sses", "shes", "ches", "xes", "zes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def words(text):
    """A text's words, case-folded and singular, punctuation and hyphens dropped."""
    return [singular(word) for word in WORD.findall(unicodedata.normalize("NFKC", text).casefold())]


def term_words(text):
    """A term's words without a leading article: `The Kaplan-Meier estimators` is kaplan meier estimator."""
    found = words(text)
    return found[1:] if len(found) > 1 and found[0] in ARTICLES else found


def forced_surface_form(text):
    """True when an open token has exactly one way to write it.

    A number, or a token whose own casing is fixed by a case change, digit or underscore. A
    plain single-case word like `molar` is not: a subject answering in one word naturally
    capitalises it. That is a `term`.
    """
    if not text or re.search(r"\s", text):
        return False
    if parsed(text) is not None:
        return True
    return bool(re.search(r"[0-9_]", text) or (re.search(r"[a-z]", text) and re.search(r"[A-Z]", text)))


def answer_block(text, labelled=False):
    """The reply's answer line, with the lines below it: see "Reading a reply" in tool-contracts.md.

    Empty when the reply has no answer line.
    """
    lines = normalize(text).lstrip("﻿").split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return []
    if FENCE.fullmatch(lines[0]):
        blocks = fenced_blocks("\n".join(lines))
        if blocks and blocks[0][0] == 2:  # The fence opens on the reply's first line.
            return answer_block("\n".join(blocks[0][2]), labelled)
    first = lines[0].strip()
    if not labelled:
        if BARE_LABEL.fullmatch(first):
            return answer_block("\n".join(lines[1:]), True)
        match = LABEL.fullmatch(first)
        if match and match.group(1).strip():
            answer = match.group(1).strip()
            # `**Answer: 42**`: emphasis opened before the label closes after the answer. An answer
            # that starts with the same characters is wrapped itself, and its readings unwrap it.
            opened = re.match(r"[*_]+", first)
            if opened and answer.endswith(opened.group()) and not answer.startswith(opened.group()):
                answer = answer[:-len(opened.group())].rstrip()
            return [answer, *lines[1:]]
    return [first, *lines[1:]]


def answer_line(text):
    """The reply's answer line alone, or an empty string."""
    block = answer_block(text)
    return block[0] if block else ""


def unwrap(text):
    """`text` with one layer of presentation off both ends, or `text` itself when there is none."""
    code = INLINE_CODE.fullmatch(text)
    if code and code.group(1) not in code.group(2) and code.group(2).strip():
        return code.group(2).strip()
    for left, right in WRAPPERS:
        inner = text[len(left):-len(right)]
        if (len(text) > len(left) + len(right) and text.startswith(left) and text.endswith(right)
                and left not in inner and inner.strip()):
            return inner.strip()
    if text.endswith(".") and not text.endswith(".."):
        return text[:-1].rstrip()
    return text


def readings(line):
    """The line, then the line with one more layer of presentation off both ends, until none is left."""
    found, current = [], line.strip()
    while current and current not in found and len(found) < 12:
        found.append(current)
        current = unwrap(current)
    return found


def read_number(line, unit=None):
    """The number an answer line gives, in `unit` when the case has one, or `None`."""
    texts = [reading.translate(MINUS).strip() for reading in readings(line)]
    if unit:
        texts += [inner for text in texts if text.endswith(unit) for inner in readings(text[:-len(unit)])]
    for text in texts:
        value = parsed(text)
        if value is not None:
            return value
    return None


def same_text(first, second):
    """Equal apart from case, spacing and a final full stop: how a reply may name an option."""
    def plain(text):
        return " ".join(text.split()).rstrip(".").casefold()
    return plain(first) == plain(second)


def read_option(line, options=None):
    """The 1-based option an answer line names, or `None`.

    A bare number is an option number, as the reply instruction asks; one past the list, or a
    fraction, may still be an option's own text. A number followed by text must be followed by
    its own option's text: `2. <option 3's text>` contradicts itself and names nothing.
    """
    count = len(options) if options else None
    for reading in readings(line):
        named = [index for index, option in enumerate(options or [], 1) if same_text(reading, option)]
        value = parsed(reading)
        if value is not None:
            whole = value == value.to_integral_value()
            if whole and (count is None or 1 <= value <= count):
                return int(value)
            if len(named) == 1:
                return named[0]
            return int(value) if whole else None
        if len(named) == 1:
            return named[0]
        match = OPTION.fullmatch(reading)
        if match:
            index, rest = int(match.group(1)), match.group(2)
            if rest is None:
                return index
            if count and 1 <= index <= count and same_text(rest, options[index - 1]):
                return index
            return None
    return None


def expression_tree(text):
    """A one-line Python expression or statement as a comparable syntax tree, or `None`.

    Parsing never runs the code. Spacing, quote style and redundant parentheses leave the tree
    unchanged, so they never decide a comparison.
    """
    text = text.strip()
    if not text or len(text) > MAX_EXPRESSION or "\n" in text:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for mode in ("eval", "exec"):
            try:
                tree = ast.parse(text, mode=mode)
            except (SyntaxError, ValueError, RecursionError, MemoryError, OverflowError):
                continue
            if mode == "eval":
                return ast.dump(tree.body)
            if len(tree.body) != 1:
                return None
            node = tree.body[0]
            return ast.dump(node.value if isinstance(node, ast.Expr) else node)
    return None


def key_items(expected):
    """A `list` or `set` key's items: `expected` split on commas and semicolons."""
    return [item.strip() for item in re.split(r"[,;]", expected)]


def item_type(item):
    """How one item of a `list` or `set` is compared: by its own form."""
    return "numeric" if parsed(item) is not None else "exact" if forced_surface_form(item) else "term"


def reply_items(block):
    """Each way the answer block splits into items: bullet lines, or the answer line split on
    commas and semicolons, with a final `and` or `or` taken as a separator too."""
    bullets = []
    for line in block:
        if not line.strip():
            if bullets:
                break
            continue
        match = BULLET.fullmatch(line)
        if not match:
            break
        bullets.append(match.group(1).strip())
    if bullets:
        return [bullets]
    found = []
    for reading in readings(block[0]) if block else []:
        items = [re.sub(r"^(?:and|or)\s+", "", item.strip(), flags=re.IGNORECASE) for item in re.split(r"[,;]", reading)]
        items = [item for item in items if item]
        if not items:
            continue
        found.append(items)
        # `a, b and c`: the last joiner separates the last two items.
        for joiner in (" and ", " or "):
            head, separated, tail = items[-1].rpartition(joiner)
            if separated and head.strip() and tail.strip():
                found.append(items[:-1] + [head.strip(), tail.strip()])
    return found


def compare_items(method, block, expected):
    keys = key_items(expected)
    candidates = reply_items(block)
    if not candidates:
        return "invalid"
    for items in candidates:
        if len(items) != len(keys):
            continue
        if method == "list":
            if all(compare(item_type(key), item, key) == "pass" for item, key in zip(items, keys)):
                return "pass"
            continue
        unmatched = list(keys)
        for item in items:
            match = next((key for key in unmatched if compare(item_type(key), item, key) == "pass"), None)
            if match is None:
                break
            unmatched.remove(match)
        if not unmatched:
            return "pass"
    return "fail"


def compare(method, reply, expected, options=None, unit=None):
    """`pass`, `fail` or `invalid` for one reply under one installed answer type."""
    block = answer_block(reply)
    line = block[0] if block else ""
    if method in ("list", "set"):
        return compare_items(method, block, expected)
    if method == "numeric":
        value = read_number(line, unit)
        try:
            return "invalid" if value is None else "pass" if abs(value - number(expected)) <= TOLERANCE else "fail"
        except ValueError:
            return "invalid"
    if method == "choice":
        index = read_option(line, options)
        try:
            return "invalid" if index is None else "pass" if index == int(number(expected)) else "fail"
        except ValueError:
            return "invalid"
    if not line:
        return "invalid"
    if method == "exact":
        return "pass" if expected.strip() in readings(line) else "fail"
    if method == "term":
        wanted = term_words(expected)
        return "pass" if any(term_words(reading) == wanted for reading in readings(line)) else "fail"
    if method == "expression":
        trees = [expression_tree(reading) for reading in readings(line)]
        if expression_tree(expected) in trees:
            return "pass"
        return "fail" if any(tree is not None for tree in trees) else "invalid"
    raise ValueError("Unknown installed comparison method")


def settles_otherwise(method, text, expected, options=None, unit=None):
    """True when Python's reader reads `text` as a well-formed answer that is not the key.

    Only a number or an option number can say that. Two tokens, terms or expressions that
    differ may still be two ways of writing one answer, so a difference there settles nothing.
    """
    line = answer_line(text)
    try:
        if method == "numeric":
            value = read_number(line, unit)
            return value is not None and abs(value - number(expected)) > TOLERANCE
        if method == "choice":
            index = read_option(line, options)
            return index is not None and index != int(number(expected))
    except ValueError:
        return False
    return False


def instruction(method, unit=None):
    """The line Python adds to a case's input, stating its answer form."""
    form = FORMS[method] + (" in " + unit if method == "numeric" and unit else "")
    return "Write only the answer on the first line of your reply: " + form + "."


def displayed(method, case):
    """The expected answer as the AI reader is shown it."""
    expected = case["expected"].strip()
    if method == "choice":
        options = case.get("options") or []
        index = int(number(expected))
        return "option " + expected + (": " + options[index - 1] if 1 <= index <= len(options) else "")
    if method == "numeric" and case.get("unit"):
        return expected + " " + case["unit"]
    if method in ("list", "set"):
        return ", ".join(key_items(expected)) + (" (in this order)" if method == "list" else " (in any order)")
    return expected


def in_quote(method, answer, quote, *, tokens=False):
    """True when an expected answer appears in its source quote.

    A `term` is found as the same words, whatever their case, plural or hyphenation; every
    other answer verbatim, and with `tokens` as a complete token, which is what the grade's
    traceability asks of it.
    """
    if method in ("list", "set"):
        return all(in_quote(item_type(item), item, quote, tokens=tokens) for item in key_items(answer))
    if method == "term":
        wanted, found = term_words(answer), words(quote)
        return bool(wanted) and any(found[index:index + len(wanted)] == wanted for index in range(len(found)))
    if method == "numeric" or tokens:
        return whole_token_in(answer, quote)
    return answer.strip() in quote


def term_problem(text):
    """Why `text` cannot be a `term`, or `None`."""
    if parsed(text) is not None:
        return "A number is a `numeric` answer, not a term."
    if not TERM_TEXT.fullmatch(text) or not WORD.search(text):
        return ("A term is a word or phrase of letters, digits, hyphens and apostrophes; an answer with other "
                "characters is an `exact` token or an `expression`.")
    found = WORD.findall(text)
    if len(found) > MAX_TERM_WORDS:
        return "A term has at most " + str(MAX_TERM_WORDS) + " words."
    if len(found) == 1 and len(found[0]) == 1:
        return "A lone letter carries meaning in its case, so it is an `exact` answer."
    marked = [word for word in found if any(char.isupper() for char in word[1:]) and not word.isupper()]
    if marked:
        return ("In a term case is ignored, but " + ", ".join(repr(word) for word in marked) + " has a capital after "
                "its first letter, so its case carries meaning; answer it as an `exact` token.")
    if not term_words(text):
        return "A term needs a word besides a leading article."
    return None


def item_form(item):
    """What one item compares as, so two items that would pass for each other are caught."""
    kind = item_type(item)
    if kind == "numeric":
        return ("numeric", number(item).normalize())
    return (kind, item) if kind == "exact" else (kind, tuple(term_words(item)))


def key_problem(method, case):
    """Why a case's expected answer cannot be read as `method`, or `None`. A choice's options
    are checked where its option rules live, in `local_candidates.qualify`."""
    expected = case["expected"].strip()
    unit = case.get("unit")
    if "\n" in expected:
        return "An expected answer is one line."
    if method == "numeric":
        if parsed(expected) is None:
            return "Numeric expected answers must be bounded plain decimal numbers."
        if unit is not None and (unit != unit.strip() or not 1 <= len(unit) <= MAX_UNIT or "\n" in unit
                                 or unit[0].isdigit() or parsed(unit) is not None):
            return "A unit is the unit's own symbol, such as nM or g/mol, of at most " + str(MAX_UNIT) + " characters."
        return None
    if method == "exact":
        if not forced_surface_form(expected):
            return ("An `exact` answer is one token whose casing is forced by a case change, digit or underscore. "
                    "A word or phrase whose case carries no meaning is a `term`.")
        return None
    if method == "term":
        return term_problem(expected)
    if method == "expression":
        if expression_tree(expected) is None:
            return "An `expression` answer is one line of Python, at most " + str(MAX_EXPRESSION) + " characters, that parses."
        return None
    if method in ("list", "set"):
        items = key_items(expected)
        if not 2 <= len(items) <= MAX_ITEMS or not all(items):
            return ("A `" + method + "` answer is 2 to " + str(MAX_ITEMS) + " non-empty items separated by commas.")
        for item in items:
            if item_type(item) == "term" and term_problem(item):
                return "Item " + repr(item) + ": " + term_problem(item)
        forms = [item_form(item) for item in items]
        if len(set(forms)) != len(forms):
            return "The items of a `" + method + "` answer must be distinct as they are compared."
        return None
    return None


def varied(word):
    """Another number of `word` that compares equal to it, or `None`: `molar` gives `molars`."""
    for other in (word + "s", word + "es", singular(word)):
        if other != word and singular(other.casefold()) == singular(word.casefold()):
            return other
    return None


def probes(method, case):
    """(reply, wanted) controls for one case. `miss` wants anything but `pass`."""
    expected = case["expected"]
    key = expected.strip()
    unit = case.get("unit")
    explained = "\n\nThe reference states this."
    shown = [("**" + key + "**", "pass"), ("**" + key + "**" + explained, "pass"), ("```\n" + key + "\n```", "pass"),
             ("Answer: " + key, "pass"), (key + explained, "pass")]
    if method == "numeric":
        center = number(expected)
        found = [(expected, "pass"), (str(center + TOLERANCE), "pass"), (str(center - TOLERANCE), "pass"),
                 (str(center + 2 * TOLERANCE), "fail"), (str(center - 2 * TOLERANCE), "fail"),
                 ("not-a-number", "invalid"), ("The answer is " + key, "invalid"), (key + " __unit_control__", "invalid")]
        if unit:
            found += [(key + " " + unit, "pass"), (key + unit, "pass"), ("**" + key + "** " + unit, "pass")]
        return found + shown
    if method == "choice":
        options = [value.strip() for value in case.get("options") or []]
        index = int(number(key))
        found = [(expected, "pass"), ("not-a-number", "invalid"), (str(len(options) + 1), "fail"),
                 ("The answer is " + key, "invalid"), ("Option " + key, "pass"), ("(" + key + ")", "pass"),
                 (key + ")", "pass"), (options[index - 1], "pass"), (key + ". " + options[index - 1], "pass")]
        found += [(str(other), "fail") for other in range(1, len(options) + 1) if other != index]
        found += [(key + ". " + options[other - 1], "invalid") for other in range(1, len(options) + 1) if other != index][:1]
        return found + shown
    near = [(key + " __incorrect_control__", "miss"), ("__incorrect_control__ " + key, "miss"),
            ("The answer is " + key, "miss")]
    if method == "exact":
        found = [(expected, "pass"), (key[:-1] or "__empty_control__", "fail"), ("`" + key + "`", "pass")]
        if key.swapcase() != key:
            found.append((key.swapcase(), "fail"))
        return found + near + shown
    if method == "term":
        found = [(expected, "pass"), (key.upper(), "pass"), (key[:1].upper() + key[1:], "pass"),
                 (key + ".", "pass"), ("not " + key, "fail"), (key[1:] or "__empty_control__", "fail")]
        pieces = key.split()
        base = " ".join(pieces[1:]) if len(pieces) > 1 and pieces[0].casefold() in ARTICLES else key
        found.append(("The " + base, "pass"))
        other = varied(pieces[-1])
        if other:
            found.append((" ".join(pieces[:-1] + [other]), "pass"))
        return found + near + shown
    if method == "expression":
        found = [(expected, "pass"), ("`" + key + "`", "pass"), ("```python\n" + key + "\n```", "pass"),
                 (key[:-1] or "__empty_control__", "miss")]
        try:
            found.append((ast.unparse(ast.parse(key)), "pass"))
        except (SyntaxError, ValueError, RecursionError):
            pass
        if expression_tree("(" + key + ")") is not None:
            found.append(("(" + key + ") + 1", "fail"))
        return found + near + shown
    items = key_items(expected)
    joined = ", ".join(items)
    found = [(joined, "pass"), ("; ".join(items), "pass"), ("\n".join("- " + item for item in items), "pass"),
             ("\n".join(str(place) + ". " + item for place, item in enumerate(items, 1)), "pass"),
             (", ".join(items[:-1]) + " and " + items[-1], "pass"), ("```\n" + joined + "\n```", "pass"),
             (joined + explained, "pass"), (", ".join(items[:-1]), "fail"),
             (joined + ", __incorrect_control__", "fail"), ("The answer is " + joined, "miss")]
    found.append((", ".join(reversed(items)), "pass" if method == "set" else "fail"))
    return found


def probe_passed(status, wanted):
    return status != "pass" if wanted == "miss" else status == wanted
