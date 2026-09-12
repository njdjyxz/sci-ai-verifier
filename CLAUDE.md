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

The goal is the complete personal/local scientific verifier, using the user's
installed Claude Code CLI, desktop Code tab and subscription. The latest
`DEVELOPMENT-PLAN.md` entry is the single completion roadmap. Computational
skills, data and tool access, evaluator construction/qualification, audited
sampling and grading, complete workflow logs, shared catalog contribution and
release handling, and real local acceptance belong to that goal. The development
log distinguishes implemented behavior from pending live and scientific acceptance.
Do not redefine completion as a text-only, chemical-only or demonstration release.
A hosted multiuser/API product is a separate future deployment project.

Version 0.7.0 implements the local workflow and awaits manual live acceptance. Its enforceable behavior is
documented in `skills/scientific-verifier/references/local-contract.md`.
`verify` and `serve-local` provide one public action; Claude Code owns the planner
loop and fresh subject sessions. Python owns deterministic tools, bounded
processes and saved evidence. Local candidates qualify mechanically; scientific
status and grade require the exact independently authorized review and policy.
Never fabricate a review, infer scientific acceptance from fixtures, or silently
expand configured resource/app permissions.

The earlier Stage 2/3, chemical verification and same-chat demo code is preserved
for compatibility. Demo is explicit, not the product default. Existing fixtures
remain synthetic. Reviewed registries remain empty. Update contracts before
behavior and keep policy reviewable in Markdown. Live Claude Code acceptance is
separate from automated fixture tests and must not be claimed without evidence.

The authoritative documents, in dependency order:

1. `skills/scientific-verifier/references/workflow.md` — the state machine. The state x tool matrix in it governs tool legality; prose sections describe transitions within a state.
2. `skills/scientific-verifier/references/tool-contracts.md` — one section per approved tool.
3. `skills/scientific-verifier/references/runtime-contract.md` — what the host process must do (tool array stability, refusals, parallel tool use).
4. `skills/scientific-verifier/references/artifact-contracts.md`, `resource-policy.md`, `evidence-rubric.md`.

If a change touches tool legality, edit the matrix in `workflow.md` and the tool's section in `tool-contracts.md` in the same commit. They are the two halves of one contract and drift between them is the most expensive error in this repo.

## Rules specific to this project

- `tmp/legacy_fixed_workflow/` is a preserved Python-controlled implementation kept for reference only. Do not restore it, import from it, or let it become a competing workflow controller. Migrating a single deterministic behavior out of it is fine once the new contract covers that behavior.
- Registries under `registry/` hold **reviewed** entries only. Local runs autonomously write mechanically qualified candidates to `.verifier/candidates/` and historical provisional records to `.verifier/registry/`. No local tool writes to `registry/`. Future authorized contribution automation may propose reviewed changes through the qualification/release policy; agent authorship alone grants no scientific approval.
- Everything is content-addressed. `.gitattributes` pins LF endings; do not add a file or tool that reintroduces platform-dependent bytes.
- Grade and status are independent axes. A change that lets operational success produce a scientific `pass`, or that lets an evidence grade imply a verdict, is a bug regardless of how the tests read.
