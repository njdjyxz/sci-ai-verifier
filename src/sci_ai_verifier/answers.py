"""An expected value and its quote: reading a value, and finding it in the text it is quoted from.

A task design's quoted values must appear in their quotes, and a planted or reported number is
compared as an exact decimal (`local-tasks.md`). Until 2026-10-05 this module also read free-text
replies by answer type; question tests were retired then, and that reader lives in Git history.
"""

import re
import unicodedata
from decimal import Decimal, InvalidOperation

# The installed tolerance a number with no tolerance of its own is compared with.
TOLERANCE = Decimal("0.000001")
WORD = re.compile(r"[^\W_]+")
ARTICLES = {"a", "an", "the"}


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
    """True when a token has exactly one way to write it: a number, or a token whose casing is fixed
    by a case change, digit or underscore. A plain single-case word like `molar` is not."""
    if not text or re.search(r"\s", text):
        return False
    if parsed(text) is not None:
        return True
    return bool(re.search(r"[0-9_]", text) or (re.search(r"[a-z]", text) and re.search(r"[A-Z]", text)))


def key_items(expected):
    """A set value's items: `expected` split on commas and semicolons."""
    return [item.strip() for item in re.split(r"[,;]", expected)]


def item_type(item):
    """How one item of a set is found in its quote: by its own form."""
    return "numeric" if parsed(item) is not None else "exact" if forced_surface_form(item) else "term"


def in_quote(method, answer, quote, *, tokens=False):
    """True when an expected value appears in its source quote.

    A `term` is found as the same words, whatever their case, plural or hyphenation; every
    other value verbatim, and with `tokens` as a complete token, which is what the grade's
    traceability asks of it. A `set` is found item by item.
    """
    if method in ("list", "set"):
        return all(in_quote(item_type(item), item, quote, tokens=tokens) for item in key_items(answer))
    if method == "term":
        wanted, found = term_words(answer), words(quote)
        return bool(wanted) and any(found[index:index + len(wanted)] == wanted for index in range(len(found)))
    if method == "numeric" or tokens:
        return whole_token_in(answer, quote)
    return answer.strip() in quote
