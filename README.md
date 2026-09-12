# Scientific Skill Verifier

Version **0.6.0** is an incomplete local implementation on `main`. Its public action
is **verify this skill**. Claude Code plans the verification; fresh Claude Code
sessions execute the submitted text skill. Python preserves source snapshots,
validates workflow steps, qualifies reference comparisons and writes reports.

You can use the **Code tab in the Claude desktop app** for everyday verification.
The standalone Claude Code command-line program is also required: this version
starts its separate test sessions through that executable.

Start with the [Windows setup guide](LOCAL-INSTALL.md): numbered installation,
subscription sign-in, desktop connection, first verification, and troubleshooting.
After setup, ask: **Use scientific-verifier-local to verify this skill: <full path>**.

The local MCP entry point, `serve-local`, exposes one tool: `verify_skill`.
Subscription-token and API-key authentication are configurable. No credentials
are written to verifier artifacts. This uses Claude's hosted models; local means
local orchestration, execution boundaries and evidence storage.

An empty local catalog triggers agent-driven discovery. Public reference bytes,
exact quotes, versions, license notes, test inputs and comparison controls are
pinned before subject execution. Qualified local configurations can be reused
offline. Reports distinguish reference comparison outcomes from scientific grades:
new local methods remain scientifically provisional, with **no invented grade**.

The current build supports text-only skills with exact/numeric comparisons.
The complete local project must also support computational skills, data and tool
access, evaluator construction and qualification, audited repeated trials,
evidence-based grading, full workflow logs, and the shared evaluator lifecycle.
These are remaining project work, not exclusions from the local product goal.
Live CLI/desktop acceptance is still required; fixtures establish implementation
behavior only. The latest [development-plan entry](DEVELOPMENT-PLAN.md#codex-2026-09-11-1932-pdt)
defines the completion checklist and effort estimate.

## Development

Python 3.11+; no third-party Python runtime dependencies.

```powershell
python -m unittest discover -s tests -q
python scripts/run_local_fixture.py
```

Use the [development plan](DEVELOPMENT-PLAN.md) as the single completion roadmap.
The [local runtime contract](skills/scientific-verifier/references/local-contract.md)
describes what the currently shipped code can enforce; it is not the completion goal.

## Profiles and compatibility

| Entry/profile | Purpose |
| --- | --- |
| `verify` / `serve-local` | Personal local product; independent subject sessions and provisional reference comparisons |
| `serve --profile verification` | Historical bounded CHNOPS chemical workflow; explicitly configured subject adapter/catalog |
| `serve --profile stage2` / `stage3` | Extraction and routing checkpoints |
| `serve --profile demo` | Explicit historical same-chat demonstration; no independent scientific grade |

The retired demo branch's useful implementation is preserved in main's history.
Old saved runs retain their profiles and immutable evidence. The Desktop builder
remains available for compatibility. Reviewed `registry/` entries are separate
from run-generated local candidates. Legacy source in `tmp/legacy_fixed_workflow/`
is preserved and never imported by the active runtime.
