# Try a random safe skill in Claude Desktop

Use **version 0.5.0** from branch `codex/general-skill-demo`. It removes the chemical-only scope, reviewed-catalog requirement and external-runner setup from the general demo. It works with your existing Claude Chat and needs no API key.

## Install both updated files

1. Install `dist/scientific-verifier-0.5.0.mcpb` as the desktop extension, replacing the old Scientific Verifier extension. Its display name is **Skill Verifier Demo**. Keep your existing Python interpreter and result-folder settings. Enable the extension.
2. Replace the old uploaded verifier skill with `dist/scientific-verifier-skill-0.5.0.zip`, and enable it.
3. Start a **new Chat**. The old 0.2.0 extension or an old saved run will keep its old extraction-only behavior; updating just one file is insufficient.

These packages are local builds. No app settings have been changed automatically. If necessary, use the installation screens described in [the original guide](INSTALL.md).

## Test your skill

For a local skill, paste its full path:

```text
Verify this skill: D:\path\to\your-skill
```

The directory must contain `SKILL.md`. You may also point directly to a text file. The demo accepts the exact path you select even outside the usual submission directory; it continues to reject links/junctions and exclude credentials. Do not submit a whole unrelated workspace or files containing private data.

Alternatively, attach or paste the skill's instructions, then say:

```text
Verify this attached skill. Run a few useful examples and give me the final demo report.
```

Claude should start the demo, read the skill, identify its stated behaviors, fix example inputs and expectations, generate the actual outputs, record the observations and write the final report. You do not need a chemical formula, catalog, subject runner or separate API account. Ordinary text skills—formatting, rewriting, translation, summarization, calculations or structured output—are suitable first demos.

The extension returns paths to `report-card.md` and `report-card.json` under your result folder. The report shows inputs, outputs, met/failed expectations, untested cases and limitations. If an example needs an unavailable account, app, external program or device, Claude must mark it **not tested**, rather than claim it ran.

## What this demo establishes

Claude generates and reviews the examples in the same Chat. Python preserves the plan and outputs and checks explicit text/JSON criteria. The report labels this **same-chat demo**, with no independent scientific grade. It can demonstrate behavior and reveal obvious failures; it is not an independent validation of arbitrary scientific claims or external actions.

## If the old behavior appears

If Claude stops after extracting claims, says it needs an approved chemistry catalog, or cannot find `commit_demo_plan`, the new extension/skill is not active together. Enable version 0.5.0, disable duplicate verifier server entries and start a new Chat. Do not resume an old run to test the new profile.

If a response is interrupted, ask:

```text
Resume verifier run <run-id> and continue to its final report.
```

Completed examples are immutable. Recovery restores their recorded outputs instead of repeating or replacing them. You can also ask Claude to cancel the run and report the examples completed so far.

## Local build and checks

```powershell
python -m unittest discover -s tests -q
python scripts/build_desktop.py
```

Earlier extraction/routing profiles and the stricter chemical fixture workflow remain available through explicit launch profiles. Their scientific restrictions have not been silently converted into demo grades. Live app acceptance of 0.5.0 is still the test you will perform; the automated package checks do not substitute for it.
