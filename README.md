# Scientific Skill Verifier

A personal, local verifier for scientific agent skills. You give it a skill folder; it splits
the skill into claims, designs tasks for each claim, runs the skill on those tasks in fresh
Claude Code sessions inside a disposable container, checks every output in Python against
values it planted or quoted from references it retrieved itself, has an independent Claude
session critique the evidence, and writes a report with an **evidence grade** (A to D, or U)
and a separate **status** (pass, fail, inconclusive). It runs on your own computer with your
own Claude subscription; "local" means the orchestration, settings and evidence stay on your
disk, while the model calls go to Claude.

Version **0.8.0**. One public action, **verify this skill**, exposed as the MCP tool
`verify_skill` by `serve-local` and as `python scripts/verify.py verify <path>` on the command
line. Claude Code owns the planning loop and the test sessions; Python owns the deterministic
tools, bounded processes and saved evidence; no third-party Python packages are required.

## Start here

- [INSTALL.md](INSTALL.md): step-by-step setup on Windows or macOS, including how to supply
  your own sign-in token. Nothing in this repository carries a credential.
- [LOCAL-CONFIG.md](LOCAL-CONFIG.md): container images, packages a skill declares, datasets,
  read-only app adapters, how the grade is decided, and catalog contributions.
- [DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md): what the project is, how it works, what has been
  verified live, the open questions and the roadmap. Written for the next person or agent who
  picks the project up. The dated log of every development session is in
  [DEVELOPMENT-LOG-ARCHIVE.md](DEVELOPMENT-LOG-ARCHIVE.md).
- [CLAUDE.md](CLAUDE.md): the working rules for agents that change this repository.

After setup, in the Claude desktop app's Code tab, say:

> Use scientific-verifier-local to verify this skill: `<full path to a skill folder>`

## What a grade means

The grade is an indicator of evidence strength, never an endorsement, and no human enters one.
**A**: the skill's outputs were checked by Python against values planted from, or quoted out of,
an independent source the verifier retrieved, with enough distinct tasks and repeated trials.
**B**: a weaker design, such as judged written answers for a text-only skill or fewer independent
tasks. **C**: a reproducible comparison with weaker traceability. **D**: no execution; a fresh
session judged cited sources. **U**: no acceptable source was found. The planner proposes the
grade its design supports, Python refuses any proposal its own recorded facts cannot carry, and
a critique session that never saw the planning can only lower it. Status is independent: a
unanimous fail carries the same grade as a unanimous pass, and an operational failure (a refused
or timed-out session, a package that would not install) is reported as such, never as a verdict.

## Status

Live acceptance is partial. Since 2026-09-16 the verifier has completed more than forty live
runs on real skills, and in October 2026 a thirty-skill sweep of third-party biology and
chemistry skills (eight known-good, ten with a known upstream fix as the key, six aggregator
copies, six unknown) found real defects in fourteen skills with no false alarm on the controls,
missed every keyed error by omission or abstention rather than by a wrong verdict, and lost five
skills to packages that would not build in the sandbox. The details, and what they mean for
the roadmap, are in [DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md). Fixtures remain synthetic,
reviewed registries remain empty, and nothing in the automated suite establishes scientific
acceptance.

## How the repository is organised

| Path | Purpose |
| --- | --- |
| `skills/scientific-verifier/` | The planner's skill: `SKILL.md` and the contracts under `references/`. `workflow.md` owns tool legality, `tool-contracts.md` owns each tool, `local-contract.md` owns the local profile's enforceable behaviour, `local-tasks.md` owns claims and task tests, `evidence-rubric.md` owns the grade standards |
| `src/sci_ai_verifier/` | The Python runtime: MCP transport, deterministic tools, container sandbox, Claude Code process control, evidence storage, grading and reports |
| `scripts/` | `verify.py` (CLI and `serve-local`), `configure_local.py`, `report_html.py`, `local_catalog.py`, `record_critique.py`, `build_local.py` |
| `tests/` | The automated suite (`python -m unittest discover -s tests -q`) and recorded live replies under `tests/recorded/` |
| `images/rdkit/` | A reviewed container image with RDKit, pandas and SciPy |
| `examples/` | Synthetic fixtures for the suite and `scripts/run_local_fixture.py` |
| `registry/`, `catalog/` | Reviewed catalog data (empty) and the historical catalog manifest; local runs write candidates under `.verifier/`, never here |
| `.verifier/` | Created at runtime, ignored by Git: settings, runs, attempts, reports, candidates |

## Historical profiles

The earlier Stage 2, Stage 3, chemical verification and same-chat demo workflows are kept so
that runs saved under them stay readable: `python scripts/verify.py serve --profile <stage2|stage3|verification|demo>`.
They are not the product and receive no new work; the Claude Desktop Chat extension that once
exposed them was retired on 2026-10-25. Retiring the profile code itself is on the roadmap.
