"""Explicit operator-selected replay fixtures. These never invoke the submitted skill."""

from .catalog import bounded_read, decode
from .common import Fault, digest
from .scientific import composition


class ReplaySubject:
    def __init__(self, path):
        raw = bounded_read(path)
        document = decode(raw)
        if (not isinstance(document, dict) or set(document) != {"schema_version", "model_id", "responses"}
                or document["schema_version"] != 1 or type(document["schema_version"]) is not int
                or not isinstance(document["model_id"], str) or not 1 <= len(document["model_id"]) <= 200
                or not isinstance(document["responses"], dict) or not 1 <= len(document["responses"]) <= 64):
            raise Fault("fixture_invalid", "Use a schema-1 subject fixture with a model ID and bounded responses.")
        for formula, value in document["responses"].items():
            try:
                composition(formula)
            except ValueError:
                raise Fault("fixture_invalid", "Fixture formula is outside the installed grammar.") from None
            if not isinstance(value, str) or len(value.encode("utf-8")) > 4096:
                raise Fault("fixture_invalid", "Each fixture response must be text no larger than 4096 bytes.")
        self.identity = {"adapter_id": "fixture-replay-v1-" + digest(raw),
                         "model_id": document["model_id"], "synthetic": True}
        self._responses = document["responses"]

    def observe(self, *, source, case_input, config, timeout_seconds):
        formula = case_input["formula"]
        if formula not in self._responses:
            raise OSError("No configured fixture observation for this case.")
        return {"text": self._responses[formula], "model_id": self.identity["model_id"],
                "response_id": "fixture-" + digest(formula.encode("utf-8"))}
