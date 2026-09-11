# Development plan audit: personal/local version 1

Audited 2026-09-11 against the working development plan, repository contracts,
branch ancestry and implementation. The user's latest request retires the demo
branch and resumes development on main.

| Finding | Resolution in 0.6.0 |
| --- | --- |
| Main held Stage 2 plus roadmap; the demo branch also contained Stage 3 and scientific workflow work | Integrate its history and preserve the uncommitted skill-loading/authentication decisions before branch retirement |
| README, skill and project instructions made the same-chat demo the product default | Document `verify` / `serve-local` as the personal/local interface; keep demo explicitly for compatibility |
| The approved Claude Code subject runner was still only a plan | Implement native CLI processes, restricted tools, temporary recognized plugin, explicit successful Skill invocation receipt, model/session evidence and bounded process lifetime |
| Human-only registry wording contradicted approved automatic discovery | Permit local data-only proposals and mechanical qualification, with immutable reuse; reviewed global registries remain separate |
| A complete auto-discovery-to-GitHub roadmap mixed local usefulness with service/release infrastructure | Deliver local lookup/discovery/qualification/reuse now; reserve contribution PRs, merges and catalog releases for a subsequent increment |
| Agent-generated answers or controls could be mistaken for independent scientific proof | Fetch primary-reference bytes independently of the planner; check quote/value provenance and controls; retain semantic applicability as a planner assertion and leave scientific grades unassigned |
| Ordinary temp directories can inherit user/project Claude context | Isolate config outside subject cwd; create an empty repository boundary; exclude all CLAUDE.md/rules paths; disable hooks, auto memory and skill-shell interpolation; restrict tools and MCP |
| Interruption could change a fixed evidence sample if a call were retried | Persist requests before execution; recover existing receipts and terminate the claim without replay; preserve call-budget accounting |
| Old reports and versions must remain readable | Extend saved-run compatibility without migrating or rewriting old evidence; regression-test historical profile packages |

## Implemented boundary

This is a usable local engineering release for plain text skills and installed
exact/numeric reference comparisons. Claude Code owns the native planner/tool loop.
The external interface exposes one verification action; internal tools remain
state-bound and run-bound. Submission snapshots, source claims, references,
candidate controls, selections, observations and reports are content-addressed.

Choosing text-only execution and provisional reference comparisons is the bounded
implementation scope for this increment, not a claim that the full scientific
roadmap has been completed. Agent-authored executable methods, independent source
authority/applicability qualification, scientific grade eligibility, public
contribution/release automation and broader subject tools remain unfinished.

## Validation and live limits

Automated acceptance covers empty lookup/discovery, immutable reports, offline
candidate reuse, rejected references/methods, wrong answers, zero/mixed claims,
stale tokens, credential exclusions, explicit invocation failures, authentication
separation, real-process time/output bounds, interrupted trials, and real private
MCP subprocesses driven through the public launcher. The isolated unit-conversion
fixture produces a visibly synthetic report and cannot seed a live candidate pool.

The environment's initial check found Python 3.14 and no native Claude executable
in PATH. No live model was invoked and no authentication/usage availability was
claimed. Exact installation and model-backed acceptance remain separately
verifiable prerequisites. Python 3.11 execution and the earlier app-only
instruction-conflict activity audit remain unverified.

See [the local contract](../skills/scientific-verifier/references/local-contract.md)
and [installation instructions](../LOCAL-INSTALL.md). Current validation totals,
fixture paths and branch disposition are recorded in today's development entry
and `local-validation-2026-09-11.json` after the final checks.
