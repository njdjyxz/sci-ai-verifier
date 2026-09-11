# Scientific Skill Verifier

Version **0.6.0** is the personal/local first version on `main`. Its public action
is **verify this skill**. Claude Code plans the verification; fresh Claude Code
sessions execute the submitted text skill. Python preserves source snapshots,
validates workflow steps, qualifies reference comparisons and writes reports.

[Set up and run the local version](LOCAL-INSTALL.md).

```powershell
python scripts/verify.py doctor
python scripts/verify.py verify "D:/path/to/my-skill"
```

The local MCP entry point, `serve-local`, exposes one tool: `verify_skill`.
Subscription-token and API-key authentication are configurable. No credentials
are written to verifier artifacts. This uses Claude's hosted models; local means
local orchestration, execution boundaries and evidence storage.

An empty local catalog triggers agent-driven discovery. Public reference bytes,
exact quotes, versions, license notes, test inputs and comparison controls are
pinned before subject execution. Qualified local configurations can be reused
offline. Reports distinguish reference comparison outcomes from scientific grades:
new local methods remain scientifically provisional, with **no invented grade**.

The first local scope is text-only skills with exact/numeric reference comparisons.
Executable skills and evaluators, broader scientific grading, and GitHub catalog
contribution/release automation remain later work. Live CLI/model acceptance is
still required; synthetic tests establish implementation behavior only.

## Development

Python 3.11+; no third-party Python runtime dependencies.

```powershell
python -m unittest discover -s tests -q
python scripts/run_local_fixture.py
```

Read the [development plan](DEVELOPMENT-PLAN.md), [local contract](skills/scientific-verifier/references/local-contract.md),
and [plan audit](reviews/LOCAL-V1-AUDIT.md) for scope and remaining work.

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
