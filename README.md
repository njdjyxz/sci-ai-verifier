# Scientific Skill Verifier

Version **0.7.0** is the local implementation under acceptance on `main`. Its public action
is **verify this skill**. Claude Code plans the verification; fresh Claude Code
sessions execute the submitted skill. Python preserves source snapshots,
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

The build supports container-based scripts, binary inputs and generated artifacts;
bounded resources and configured read-only app adapters; generated Python
evaluators with controls; audited repeated trials; independently authorized
A/B/C grading and separate documentary assessment; observable workflow logs;
and pinned candidate import/export, reviewed releases and retirement, with opt-in
GitHub draft proposals. The public connection supports cancellation and progress.
Independent scientific review and app-specific adapters require real domain and
application input. See the [configuration reference](LOCAL-CONFIG.md).
Live CLI/desktop acceptance is still required; fixtures establish implementation
behavior only. The [complete roadmap](DEVELOPMENT-PLAN.md#codex-2026-09-11-1932-pdt)
defines the completion checklist and effort estimate; the [current log](DEVELOPMENT-PLAN.md#codex-2026-09-12)
records implementation and acceptance status.

## Development

Python 3.11+; no third-party Python runtime dependencies.

```powershell
python -m unittest discover -s tests -q
python scripts/run_local_fixture.py
```

Use the [development plan](DEVELOPMENT-PLAN.md) as the single completion roadmap.
The [local runtime contract](skills/scientific-verifier/references/local-contract.md)
describes what the currently shipped code can enforce; it is not the completion goal.

### Next implementation stage

Run the manual acceptance procedure in [LOCAL-INSTALL.md](LOCAL-INSTALL.md#your-manual-acceptance-tests)
using the actual CLI, desktop, container and personal skills. Record the observed
results before declaring live acceptance or scientific validity. The earlier
Stage 2/3 checkpoints are historical and are not the current completion boundary.

## Profiles and compatibility

| Entry/profile | Purpose |
| --- | --- |
| `verify` / `serve-local` | Local workflow, independent sessions, controlled execution and reviewed evidence policies |
| `serve --profile verification` | Historical bounded CHNOPS chemical workflow; explicitly configured subject adapter/catalog |
| `serve --profile stage2` / `stage3` | Extraction and routing checkpoints |
| `serve --profile demo` | Explicit historical same-chat demonstration; no independent scientific grade |

The retired demo branch's useful implementation is preserved in main's history.
Old saved runs retain their profiles and immutable evidence. The Desktop builder
remains available for compatibility. Reviewed `registry/` entries are separate
from run-generated local candidates. Legacy source in `tmp/legacy_fixed_workflow/`
is preserved and never imported by the active runtime.
