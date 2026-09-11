# Skill Verifier Demo

Version **0.5.0**, on branch `codex/general-skill-demo`, can demonstrate a random safe skill in your existing Claude Desktop Chat. It accepts a specifically selected local skill or attached/pasted instructions, fixes useful example tests, records actual outputs and produces a report. **No chemical scope, reviewed catalog, separate subject runner or API key is required for this demo.**

[Install the demo and test your skill](desktop/DEMO-INSTALL.md).

## Quick start

1. Install `dist/scientific-verifier-0.5.0.mcpb` and enable **Skill Verifier Demo**.
2. Replace the uploaded verifier skill with `dist/scientific-verifier-skill-0.5.0.zip`.
3. Start a new Chat and say **Verify this skill: <full local path>**, or attach its instructions and say **Verify this attached skill**.

Keep the existing Python interpreter and result-folder settings. Updating the checkout or only one package does not update both installed components. Old runs retain their original profile; start a new run to try the demo.

The report includes example inputs, outputs, expectations met or failed, untested cases and limitations. Claude generates and qualitatively reviews examples in the same Chat. Python preserves the fixed plan and raw outputs and applies explicit exact/contains/JSON checks. Reports label this **same-chat demo**, with no independent scientific grade. Unavailable external programs, accounts, devices or actions must be marked not tested.

## Build and validate

Python 3.11+ is required, with no third-party runtime dependencies.

```powershell
python -m unittest discover -s tests -q
python scripts/build_desktop.py
```

The builder creates the MCPB, skill ZIP, install guides, configuration example and checksums under `dist/`. It does not install or publish them. The automated suite includes an extracted-package general-skill flow; live Claude app behavior is a separate acceptance check.

## Profiles

| Profile | Behavior |
|---|---|
| `demo` (desktop/CLI default) | General safe-skill examples and a same-chat report; no catalog/provider required |
| `verification` | Bounded neutral CHNOPS scientific workflow: plans, locked references, bundles, audit, configured observations, C-only independent comparison and reporting |
| `stage3` | Preserved claim routing/catalog checkpoint |
| `stage2` | Preserved extraction checkpoint |

The strict chemical workflow is implemented and fixture-tested; scientific catalog approval and a live subject adapter remain pending. Run `python scripts/run_fixture_demo.py` for its reproducible synthetic example, with `--variant wrong` or `--variant invalid` to inspect failure paths. Synthetic approvals never enter the reviewed registries. See [the chemical pilot](reviews/CHEMICAL-MASS-PILOT.md) and [completion record](reviews/PROJECT-COMPLETION.md).

## Records and boundaries

Records live under `<result folder>/.verifier/runs/<run-id>/`. Open `report-card.md` first; `report-card.json` retains exact provenance and detailed evidence. Plans, outputs and reports are content-addressed, journaled and recoverable. A lost response should trigger context recovery, not replacement of an example. Cancellation preserves completed examples and records the remaining ones as untested.

The demo allows the exact local path selected by the user, including outside the usual submission directory. It retains link/junction rejection, credential exclusions, snapshot identity and finite size/request bounds. Pasted text is recorded as caller-supplied text; original attachment bytes and model identity are not independently attested. `verification_complete` means report accounting finished, not that a skill passed scientific validation.

## Repository map

| Path | Purpose |
|---|---|
| `skills/scientific-verifier/` | Uploaded skill and profile/workflow/tool/artifact contracts |
| `src/sci_ai_verifier/` | Demo, scientific runtime, snapshots, routing, execution and storage |
| `registry/`, `catalog/` | Reviewed registry source and distributable catalogs; currently empty |
| `examples/catalog/` | Provisional scientific proposals |
| `examples/submissions/` | Extraction fixtures |
| `examples/chemical-mass-fixture/` | Synthetic chemical subject, with answers separate from submitted instructions |
| `desktop/`, `scripts/` | Install guides, packaging and reproducible chemical fixture demo |
| `tests/`, `reviews/` | Automated checks and precisely scoped acceptance records |
| `tmp/legacy_fixed_workflow/` | Preserved historical code; never imported by the active runtime |

The [demo contract](skills/scientific-verifier/references/demo-contract.md) and its [workflow matrix](skills/scientific-verifier/references/workflow.md#general-demo-profile) define this branch's broader demonstration. The stricter scientific contracts remain explicit and do not silently confer their grades on demo observations.
