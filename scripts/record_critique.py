"""Re-record tests/recorded/critic-task-structured.jsonl under the live task-critique rubric.

Replays run 3f073fec claim 1's packet, with the live rubric in place of the recorded one, through
critique_tasks on the pinned model, exactly as a run would. Writes the raw stream and the packet only
after the stream parses, carries no credential bytes and has LF endings. Prints a summary; never the token.
"""
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(sys.argv[1])
sys.path.insert(0, str(REPO / "src"))
from sci_ai_verifier.claude_runner import ClaudeCode, run_process  # noqa: E402
from sci_ai_verifier.common import canonical, digest  # noqa: E402
from sci_ai_verifier.documentary import TASK_CRITIQUE_REF, TASK_CRITIQUE_RUBRIC, critique_tasks  # noqa: E402
from sci_ai_verifier.ingest import SECRET_BYTES  # noqa: E402

recorded = REPO / "tests" / "recorded"
packet = json.loads((recorded / "critic-task-packet.json").read_text(encoding="utf-8"))
packet["rubric"] = TASK_CRITIQUE_RUBRIC
assert digest(canonical(packet["rubric"])) == TASK_CRITIQUE_REF

token = os.environ["SCI_VERIFIER_OAUTH_TOKEN"]
os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = token
captured = {}


def recorder(command, **kwargs):
    code, raw, err = run_process(command, **kwargs)
    captured.update(code=code, raw=raw, err=err)
    return code, raw, err


adapter = ClaudeCode(executable=shutil.which("claude"), model="claude-opus-5", auth="subscription", process=recorder)
value = critique_tasks(adapter, packet)
raw = captured["raw"]
assert b"\r\n" not in raw and raw.endswith(b"\n"), "stream shape"
assert SECRET_BYTES.search(raw) is None and token.encode() not in raw, "credential bytes in the stream"
(recorded / "critic-task-structured.jsonl").write_bytes(raw)
(recorded / "critic-task-packet.json").write_bytes((json.dumps(packet, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print(json.dumps({"supported_grade": value["supported_grade"], "cost_usd": value["total_cost_usd"],
                  "session_attempts": value["session_attempts"], "models": value["observed_model_ids"],
                  "verdicts": [(item["case_id"], item["verdict"]) for item in value["case_verdicts"]],
                  "unsourced": [(item["rule"][:60], item["searched"], item["quoted"]) for item in value["unsourced_rules"]],
                  "objections": value["objections"], "required_revisions": value["required_revisions"],
                  "departures": value["departures"], "coverage_gaps": value["coverage_gaps"],
                  "stream_lines": raw.count(b"\n")}, ensure_ascii=False, indent=1))
