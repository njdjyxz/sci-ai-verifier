# Scientific AI Verifier

Scientific AI Verifier extracts atomic scientific claims from submitted AI skills, then is intended to route, evaluate, and report those claims with reproducible evidence. **Stage 2 currently implements claim extraction only.** It does not run the submitted skill, evaluate scientific accuracy, assign evidence grades, or produce a scientific report card.

## Current stage

The reviewed Stage 1 specification describes the full future workflow. The active Stage 2 Python runtime implements three workflow tools and bootstrap controls for **Claude Desktop Chat**. The desktop app owns the conversation; Python owns exact validation, snapshots, state, and saved records. No Claude Code CLI or separate model API loop is required.

The installable deliverables are a custom skill ZIP and a local MCP desktop extension. Python 3.11+ is required, with no third-party runtime dependencies. See the [desktop installation guide](desktop/INSTALL.md), [Stage 2 contract and acceptance checklist](skills/scientific-verifier/references/stage2-contract.md), and [development plan](DEVELOPMENT-PLAN.md).

The packages are prepared for installation. Scripted tests do not establish that the Claude app loaded the skill, followed its instructions, or extracted scientifically appropriate claims. The live desktop acceptance step remains separate.

## Architecture

```text
Claude Desktop Chat + uploaded scientific-verifier skill
    -> start/resume a run through the local MCP extension
    -> receive pinned instructions, committed state, and authorized source path
    -> load_submitted_skill
    -> read_snapshot_file for relevant reference files
    -> commit_claim_manifest
    -> stage2_complete (scientific verification remains pending)
```

Every workflow request includes the current run ID and an opaque state token. Python checks schemas, legality, source authorization, snapshot integrity, exact source quotes, and independent retry budgets. Calls formed from the same token cannot both execute. Tool results are authoritative for the saved workflow.

Submitted source text stays untrusted data. The runtime never executes it or follows its links. It can read only within the operator's configured submission directory and writes run artifacts only below the configured data directory's `.verifier/`.

Claude Desktop controls its other tools, model selection, message context, and billing. A local extension cannot enforce all of those controls or attest the model's exact identity. The [desktop host profile](skills/scientific-verifier/references/stage2-contract.md#enforcement-and-app-limitations) makes those limits explicit. The prototype is not a fully isolated verifier host.

## Build and validate

From the repository root in PowerShell:

```powershell
python -m unittest discover -s tests -v
python scripts/build_desktop.py
```

The build creates these local outputs under `dist/`:

- `scientific-verifier-0.2.0.mcpb`: local Python tools and pinned specification files.
- `scientific-verifier-skill-0.2.0.zip`: the skill folder for upload to Claude.
- `claude_desktop_config.example.json`: a manual configuration alternative using this checkout.
- `checksums.json`: package SHA-256 digests.

Generated packages and run data are gitignored; source files and the reproducible builder are kept in Git. The desktop package test builds and launches the extracted extension over stdio without importing the checkout's runtime.

## Review order

1. [SKILL.md](skills/scientific-verifier/SKILL.md): agent responsibilities and bootstrap.
2. [Stage 2 contract](skills/scientific-verifier/references/stage2-contract.md): current implementation boundary, schemas, persistence, and acceptance cases.
3. [Workflow](skills/scientific-verifier/references/workflow.md): authoritative state/tool tables, including the explicit Stage 2 profile.
4. [Tool contracts](skills/scientific-verifier/references/tool-contracts.md): deterministic responsibilities.
5. [Runtime contract](skills/scientific-verifier/references/runtime-contract.md): full-host target and desktop exceptions.
6. [Artifact contracts](skills/scientific-verifier/references/artifact-contracts.md), [resource policy](skills/scientific-verifier/references/resource-policy.md), and [evidence rubric](skills/scientific-verifier/references/evidence-rubric.md).
7. [Review guide](reviews/REVIEW-GUIDE.md): background on the Stage 1 review and scientific workflow branches.

## Active repository structure

```text
CLAUDE.md, README.md, DEVELOPMENT-PLAN.md, pyproject.toml
skills/scientific-verifier/       Reviewed instructions and contracts
src/sci_ai_verifier/              Small deterministic Stage 2 runtime
  agent.py                       Bootstrap, pinned context, and recovery
  tools.py                       Tool schemas, legality, and dispatch
  storage.py                     Content-addressed objects and event journal
  ingest.py                      Source snapshots and exact file reads
  claims.py                      Structural claim and quote validation
  mcp.py, __main__.py             Local stdio transport and diagnostics
  common.py                      Shared deterministic primitives
desktop/                         Extension manifest, entry point, install guide
scripts/build_desktop.py         Reproducible MCPB and skill ZIP builder
tests/                           Deterministic and packaged-protocol acceptance
examples/submissions/            Reference, zero-claim, and conflict fixtures
registry/, evaluators/           Reviewed catalogs; later-stage use only
tmp/legacy_fixed_workflow/        Preserved earlier implementation
```

## Storage and scientific principles

Runs use `.verifier/runs/<run-id>/`. Immutable SHA-256 objects live in `.verifier/store/`. An atomic hash-linked event journal is the commit record; readable `run.json`, `source-snapshot.json`, and `claim-manifest.json` projections can be reconstructed. UTF-8 text is normalized to LF before hashing. Reads and resumption use the immutable snapshot, even if the original source changes.

The full workflow keeps scientific verdicts separate from evidence strength and operational failures. Grades A through C require independently scored evidence; D requires a completed independent documentary assessment; U never supports a scientific pass or fail. These later-stage rules are specified, not implemented by Stage 2.

Git's `registry/` contains reviewed entries only. Future runs write provisional metadata under `.verifier/registry/`; promotion requires a human-reviewed commit. Stage 2 touches neither layer. The preserved [legacy implementation](tmp/legacy_fixed_workflow/) remains reference material and is never imported by the active package.

## Next implementation stage

Complete the live Claude Desktop installation and bounded fixture acceptance, recording the app version, visible model label, actual tool results, and any unavailable exact model metadata. Assess extracted claim quality separately from Python's structural validation.

Stage 3 then adds claim-type routing, reviewed evaluator lookup, and an independently released GitHub catalog with compatibility checks, digest verification, pinned versions, and explicit offline behavior. Its [distribution contract](skills/scientific-verifier/references/stage2-contract.md#stage-3-dependency-independently-released-catalog) is defined; retrieval and publication are not implemented in Stage 2.
