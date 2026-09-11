# sci-ai-verifier
## Principles

- Keep it simple, stupid.
- Entities should not be multiplied unnecessarily.
- 八荣八耻

    以瞎猜接口为耻，以认真查询为荣。
    以模糊执行为耻，以寻求确认为荣。
    以臆想业务为耻，以人类确认为荣。
    以创造接口为耻，以复用现有为荣。
    以跳过验证为耻，以主动测试为荣。
    以破坏架构为耻，以遵循规范为荣。
    以假装理解为耻，以诚实无知为荣。
    以盲目修改为耻，以谨慎重构为荣。

## This repository

On 2026-09-11 the user requested branch `codex/general-skill-demo` and a quick demo for arbitrary safe skills in Claude Chat. Version 0.5.0 defaults to `demo`, with local or inline submissions, fixed examples, same-chat observations and reports. It bypasses scientific catalog/provider prerequisites without inventing independent scientific grades. Its governing contract is `skills/scientific-verifier/references/demo-contract.md`. Existing scientific and checkpoint profiles remain explicit and compatible. Retain truthful provenance, secret exclusions and immutable evidence; do not silently represent same-chat judgments as independent verification.

Stage 1 is the reviewed Markdown specification. Version 0.4.0 of the Claude Desktop MCP runtime under `src/sci_ai_verifier/` preserves Stage 2/3 and adds the bounded `verification` profile in `skills/scientific-verifier/references/verification-contract.md`. It implements plans, fixed resources, bundles, audit, configurable subject observations and reports for the C-only chemical-mass pilot. The user chose fixtures for now; no live provider is enabled. Candidate entries under `examples/catalog/` remain provisional, reviewed registries remain empty, and synthetic catalog approvals are test data only. Update contracts before behavior; keep policy reviewable in Markdown.

The authoritative documents, in dependency order:

1. `skills/scientific-verifier/references/workflow.md` — the state machine. The state x tool matrix in it governs tool legality; prose sections describe transitions within a state.
2. `skills/scientific-verifier/references/tool-contracts.md` — one section per approved tool.
3. `skills/scientific-verifier/references/runtime-contract.md` — what the host process must do (tool array stability, refusals, parallel tool use).
4. `skills/scientific-verifier/references/artifact-contracts.md`, `resource-policy.md`, `evidence-rubric.md`.

If a change touches tool legality, edit the matrix in `workflow.md` and the tool's section in `tool-contracts.md` in the same commit. They are the two halves of one contract and drift between them is the most expensive error in this repo.

## Rules specific to this project

- `tmp/legacy_fixed_workflow/` is a preserved Python-controlled implementation kept for reference only. Do not restore it, import from it, or let it become a competing workflow controller. Migrating a single deterministic behavior out of it is fine once the new contract covers that behavior.
- Registries under `registry/` hold **reviewed** entries only and are changed by humans in commits. Runs write provisional entries to `.verifier/registry/`, which is gitignored. Never wire a runtime write path to `registry/`.
- Everything is content-addressed. `.gitattributes` pins LF endings; do not add a file or tool that reintroduces platform-dependent bytes.
- Grade and status are independent axes. A change that lets operational success produce a scientific `pass`, or that lets an evidence grade imply a verdict, is a bug regardless of how the tests read.
