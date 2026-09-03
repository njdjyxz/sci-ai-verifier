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

Stage 1 is a **Markdown specification with no active Python package**. `src/sci_ai_verifier/` is named by the tool contracts but does not exist. Do not create it, or any other runnable module, without first updating the reviewed contracts — the whole point of this stage is that the architecture can still change cheaply.

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
