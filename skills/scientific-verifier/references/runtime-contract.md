# Runtime Contract

`workflow.md` defines *what* the verifier does. This file defines what the **host process** must do so that definition holds when the verifier agent is a large language model rather than a subroutine. Nothing here changes a scientific rule; everything here is an obligation on the runner.

Sections 1 through 5 are provider-neutral. Section 6 records the Claude-specific settings the reference host uses, because the reviewed architecture assumes a Claude model in the agent role.

## 1. Declared legality versus authorization

Earlier drafts said the runner "exposes only the tools legal for the committed state." That conflated two different things, and the stricter reading is expensive to implement without breaking response caching.

The contract is:

- The runner **declares** the legal tools for the committed state in every result and at every bootstrap. The declaration is authoritative for the agent: it must request only a declared tool.
- The runner **enforces** legality in the dispatcher. Every request is revalidated against committed state and prerequisites before any side effect. A request for a tool that is not legal in the committed state is rejected under section 3 below.
- The set of tool *definitions* published to the model may be larger than the legal set, and should be stable across a run. Tool visibility is not authorization and never was; `tool-contracts.md` already states this.

The security property is unchanged. It rests on dispatcher revalidation, not on hiding definitions. A host that prefers to publish only the legal subset is still conformant, but it pays the cost described in section 6.

## 2. One transition per tool call

Every tool result commits at most one state transition. The runner must guarantee that the model cannot request two workflow tools in a single assistant turn, because two concurrent requests against one committed state have no defined ordering and the second would be validated against state the first has already changed.

If the host cannot disable concurrent tool requests, it must serialize them: dispatch the first request, and reject every other request in the same turn under section 3 with `concurrent_request_rejected`. It must still return a result for every request the model made, so the conversation stays well formed.

## 3. Illegal and malformed requests

A request that names an undeclared tool, names a tool illegal in the committed state, or is rejected under section 2 returns `retryable` with committed state unchanged, as defined in `tool-contracts.md`.

These rejections consume a **separate** counter from the repair retries described in the common result protocol:

- `retries_remaining` counts repairs of a legal request whose *content* was wrong. Only the tool that returned `retryable` decrements it.
- `illegal_transitions_remaining` counts requests rejected before any tool ran. Both counters appear in the retryable envelope.

The two must not share a budget. A model that misroutes twice must not thereby exhaust the repair budget for the correct tool, and a model that loops on an illegal request must still hit a bound. When `illegal_transitions_remaining` reaches zero, the runner records a claim-scoped operational outcome with category `illegal_transition_limit` and continues independent claims, exactly as for other claim-local limits.

Misrouting is the expected failure mode of a language model, not an exceptional one. Both bounds should be generous enough that a single confused step is recoverable and small enough that a loop terminates.

## 4. Context assembly

The runner assembles the session as separately labeled blocks with explicit trust classes, in the order given in `workflow.md`. Two rules govern *how* it does so:

- **Stable material is assembled once.** The runner instructions, `SKILL.md`, and `workflow.md` do not change during a run. They are placed at the front of the context and are not rewritten, reordered, or re-templated between steps.
- **Stage-specific material is appended, not edited in.** When a state becomes relevant, the applicable `tool-contracts.md`, `artifact-contracts.md`, `evidence-rubric.md`, and `resource-policy.md` sections are appended to the conversation as new operator-authored blocks. The runner must not rewrite already-sent context to insert them.

Both rules exist so the stable prefix stays byte-identical across steps. A host that rewrites earlier context on each step is conformant but pays full price for the entire specification on every step of every claim.

The runner records the identity, version or digest, trust class, and authorizing state of every block it appends, as required by the run record.

## 5. Model-level termination

The agent may fail in ways that are not tool results: the model may decline to answer, may be cut off by an output limit, or may return no actionable request. The verifier processes untrusted third-party chemical and biological text as data, so a safety-classifier decline is a foreseeable event on this workload, not an edge case.

None of these are scientific outcomes and none map to `ok`, `retryable`, or `fatal`, because no tool ran. The runner:

1. Inspects the model's termination reason before reading its content.
2. Applies its configured mitigation once — a fallback model, a reduced-context retry, or a narrowed request.
3. If the step still cannot produce a request, records a claim-scoped operational outcome with category `agent_unavailable` and a stable subcode identifying the reason, and continues independent claims.
4. Escalates to run scope only when the condition prevents any claim from progressing.

An `agent_unavailable` outcome never becomes grade U and never becomes a scientific `fail`. A refusal to analyze a submitted skill is a fact about the run, not evidence about the claim.

## 6. Claude host settings

The reference host runs the verifier agent on Claude. These settings implement sections 1 through 5.

**Tool array stability (section 1).** Response caching is a prefix match, and the rendered request orders tools before the system prompt and messages. Because tools render first, changing the published tool array on a state transition invalidates the cached prefix *and* the whole conversation after it. Publish all workflow tools once, in a deterministic order, and enforce legality in the dispatcher. Where a smaller published surface is wanted, use deferred tool loading rather than swapping the array — noting that the search tool itself must not be deferred and at least one tool must remain non-deferred. Confirm the result by watching `usage.cache_read_input_tokens` across steps; a persistent zero means something in the prefix is still changing.

**Appended operator blocks (section 4).** Stage-specific reference sections are appended as `system`-role entries in the message array rather than by editing the top-level system prompt, which would invalidate the prefix. This channel is also the injection-safe way to deliver operator instructions after untrusted payload content has entered the conversation. It is available on Claude Opus 5, Opus 4.8, Fable 5, and Mythos 5, and not on Sonnet 5; hosts on other models must fall back to appending a labeled user-role block. Placement constraints: such an entry must follow a user turn, cannot be the first message, and must be either last or followed by an assistant turn.

**Single request per turn (section 2).** Parallel tool use is on by default and must be disabled. When it is left enabled, all tool results for a turn must be returned in one user message, which is incompatible with committing a transition per call.

**Input validation.** Declarative harness configurations and other structured tool inputs are declared with strict schemas — `additionalProperties: false` plus an explicit `required` list — so the runner receives inputs that validate exactly and schema violations never reach the dispatcher's semantic checks.

**Termination (section 5).** The host checks the response's stop reason before its content, and enables server-side refusal fallbacks so a classifier decline is routed rather than surfaced as a dead step.

**Limits.** The runner's step, cost, wall-clock, and execution limits are enforced by the runner and are not delegated to the model. A model-facing task budget may be set in addition, as pacing guidance; it is advisory and does not satisfy the enforcement requirement in `workflow.md`.

**Long runs.** Server-side compaction or tool-result clearing may be enabled to bound context growth. Neither is permitted to become the record: every committed artifact is persisted by the runner and reread from storage, never recovered from the transcript. This is consistent with the run record's existing rule that the transcript stores what audit requires and never persists private model reasoning.

**Agent tool surface.** The verifier agent is given the approved workflow tools and nothing else. A general-purpose coding harness that ships file-read, shell, search, or fetch tools must have them disabled; with any of them enabled the trust boundary in `SKILL.md` is void, because the agent could read registries, run artifacts, expected answers, and raw payloads directly instead of through the tools that bound them.

**Subject model.** The model running the verifier agent is recorded separately from the model running the submitted skill. They are different roles with different records, and neither may be inferred from the other. See the subject-runner rules in `workflow.md` and `artifact-contracts.md`.
