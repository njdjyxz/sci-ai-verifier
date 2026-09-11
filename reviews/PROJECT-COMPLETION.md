# Completion record for the first chemical-mass delivery

**2026-09-11 update:** The user's demo request supersedes the chemical-only default. Branch `codex/general-skill-demo` adds version 0.5.0: arbitrary safe local/inline skill text, fixed examples, same-chat observations and a complete report without catalogs or credentials. See [the demo guide](../desktop/DEMO-INSTALL.md). It is explicitly a same-chat demo, not an independent scientific evaluation. The stricter chemical implementation and its remaining scientific acceptance boundaries are described below.

The public request remains **verify this skill**. The user selected chemical formula/mass calculations and then chose **configurable execution with test fixtures for now**. Version 0.4.0 implements that bounded workflow through reporting. A live test is not a prerequisite for finishing these local modules.

| Work item | Current state | Evidence or remaining boundary |
|---|---|---|
| Routing/catalog | Implemented | Exact release/resource pins, compatibility checks, deterministic selection, local proposals and fixture transport tests |
| Evaluator implementation | Implemented for the narrow neutral CHNOPS pilot | Installed parser/oracle, seven pinned cases, fixed tolerance and C-only comparison policy; broader chemistry unsupported |
| Scientific catalog review | Review package prepared; approval pending | [Chemical pilot](CHEMICAL-MASS-PILOT.md) and provisional examples; reviewed registries remain empty |
| Planning/resources | Implemented | Immutable plan revisions; exact resource search/locks; downstream authority invalidation |
| Bundle/registration/audit | Implemented | Target-to-registered flow, validated cases, run-local promotion, advisory audit proposal and authoritative checks |
| Controlled subject interface | Implemented and fixture-tested | Explicit operator adapter, bounded inputs/calls/output, answer separation, raw receipts and no replay of uncertain attempts; no live provider or hard sandbox |
| Results/reporting | Implemented | Separate verdict/grade, per-trial scoring, mixed/empty/operational reports, cancellation and recovery, JSON plus Markdown |
| Local/package acceptance | Automated evidence recorded separately | [Combined validation](demo-validation-2026-09-11.json); scripted approvals/results do not establish live skill performance |
| Live app acceptance | Pending for 0.4.0 | [Installation/acceptance guide](../desktop/VERIFICATION-INSTALL.md); old 0.2.0 evidence is preserved |

The default package accounts for all claims in a report even when no reviewed capability exists. `verification_complete` means the workflow has finished its accounting; it never means scientific success. A configured fixture can exercise the full execution path without credentials. No whole-skill grade is invented.

Before a production scientific release, independently review/promote the pilot catalog, select and validate a live subject adapter, and inspect a short-prompt run in Claude Desktop. Retain the earlier instruction-conflict conversation check, unavailable exact planner identity, and untested actual Python 3.11/independent MCP client as acceptance limitations. Those are external evidence gaps, not unimplemented planning/reporting modules.

The general specification still describes future capabilities beyond this first policy: wider formulas/elements, average mass, A/B evidence designs, arbitrary external resource acquisition and independent D assessment. This version reports unsupported capabilities operationally. It does not claim those features are implemented or that fixtures finish their scientific validation.
