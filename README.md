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
offline. Reports distinguish reference comparison outcomes from scientific grades.

The evidence grade is an indicator of how gold-standard the evidence is, not an
endorsement: A means the skill was compared against answers Python itself retrieved
from an independent source, D means the conclusion rests on AI judgment over cited
sources. The verifier seeks the strongest design the claim allows, proposes the
grade it supports, and a fresh session that never saw the planning critiques that
proposal and can only lower it. No human sign-off assigns a grade, and **no grade is
invented**.

The build supports container-based scripts, binary inputs and generated artifacts;
bounded resources and configured read-only app adapters; generated Python
evaluators with controls; audited repeated trials; negotiated A/B/C grading and
separate documentary assessment; observable workflow logs; and pinned candidate
import/export, prepared releases and retirement, with opt-in GitHub draft
proposals the agent can revise after review. The public connection supports
cancellation and progress. App-specific adapters require real application input.
See the [configuration reference](LOCAL-CONFIG.md).
Live CLI/desktop acceptance is still required; fixtures establish implementation
behavior only. The [complete roadmap](DEVELOPMENT-PLAN.md#codex-2026-09-11-1932-pdt)
defines the completion checklist and effort estimate; the
[current log](DEVELOPMENT-PLAN.md#claude-2026-09-15) records implementation and
acceptance status.

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

One live run has completed the whole local path (glycoengineering, 2026-09-16: five
claims, four settled at evidence grade A, 66 of 66 trials scored, one operational
limitation). It exercised the A-grade branch only.

Continue the manual acceptance procedure in [LOCAL-INSTALL.md](LOCAL-INSTALL.md#your-manual-acceptance-tests)
using the actual CLI, desktop, container and personal skills, with more skills chosen to
force the B, C and documentary paths. Record the observed results before declaring live
acceptance or scientific validity. The earlier Stage 2/3 checkpoints are historical and
are not the current completion boundary.

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
from run-generated local candidates. The previously preserved copies under `tmp/`
and `reviews/`, and the superseded `evaluators/chemical_mass/` helper, were removed
on 2026-09-15; they remain in Git history.
