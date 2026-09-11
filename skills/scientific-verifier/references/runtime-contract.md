# Runtime Contract

`workflow.md` defines *what* the verifier does. This file defines what the **host process** must do so that definition holds when the verifier agent is a large language model rather than a subroutine. Nothing here changes a scientific rule; everything here is an obligation on the runner.

Sections 1 through 5 describe the full host target. The implemented desktop profiles use the explicit [Stage 2 host guarantees](stage2-contract.md), extended for routing by [Stage 3](stage3-contract.md) and for bounded execution/reporting by the [verification profile](verification-contract.md). They retain the narrower observable/enforceable desktop guarantees. Section 6 describes that integration instead of the superseded direct model API host.

The 0.5.0 [general demo profile](demo-contract.md) is a separately labeled same-chat demonstration, not full-host scientific conformance. Its source/plan/observation records are deterministic, while example generation and qualitative review occur in Claude Chat. The stable surface now has five host controls and eighteen workflow tools, with profile-specific legality.

## 1. Declared legality versus authorization

Earlier drafts said the runner "exposes only the tools legal for the committed state." That conflated two different things, and the stricter reading is expensive to implement without breaking response caching.

The contract is:

- The runner **declares** the legal tools for the committed state in every result and at every bootstrap. The declaration is authoritative for the agent: it must request only a declared tool.
- The runner **enforces** legality in the dispatcher. Every request is revalidated against committed state and prerequisites before any side effect. A request for a tool that is not legal in the committed state is rejected under section 3 below.
- The set of tool *definitions* published to the model may be larger than the legal set, and should be stable across a run. Tool visibility is not authorization and never was; `tool-contracts.md` already states this.

The security property is unchanged. It rests on dispatcher revalidation, not on hiding definitions. A host that prefers to publish only the legal subset is still conformant, but it pays the cost described in section 6.

## 2. One transition per tool call

Every tool result commits at most one scoped transition. Bulk claim-type assignment moves the manifest's claims together to the same next state; subsequent capability lookup and scientific work target one claim per call. The runner must guarantee that the model cannot request two workflow tools in a single assistant turn, because two concurrent requests against one committed state have no defined ordering and the second would be validated against state the first has already changed.

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

Use `verifier_instruction` only for reviewed operator instructions and `committed_metadata` for validated structured state/identity. Source snapshot bytes, registry prose, documentary evidence, and other free text are `untrusted_payload`, supplied separately through data/tool-result channels rather than embedded in system/operator blocks. A digest verifies identity, not instructional authority. On resumption preserve these separate trust labels; never promote a retrieved payload into an operator instruction because it was previously read.

## 5. Model-level termination

The agent may fail in ways that are not tool results: the model may decline to answer, may be cut off by an output limit, or may return no actionable request. The verifier processes untrusted third-party chemical and biological text as data, so a safety-classifier decline is a foreseeable event on this workload, not an edge case.

None of these are scientific outcomes and none map to `ok`, `retryable`, or `fatal`, because no tool ran. The runner:

1. Inspects the model's termination reason before reading its content.
2. Applies its configured mitigation once — a fallback model, a reduced-context retry, or a narrowed request.
3. If the step still cannot produce a request, records a claim-scoped operational outcome with category `agent_unavailable` and a stable subcode identifying the reason, and continues independent claims.
4. Escalates to run scope only when the condition prevents any claim from progressing.

An `agent_unavailable` outcome never becomes grade U and never becomes a scientific `fail`. A refusal to analyze a submitted skill is a fact about the run, not evidence about the claim.

## 6. Implemented Claude Desktop host

The approved integration target is Claude Desktop Chat, using an uploaded skill ZIP and a local MCP extension. The app owns planner model calls and the conversation. Python exposes five host controls and eighteen workflow tools, with profile-specific legality. The verification profile includes a host-injected subject interface and explicit replay fixtures; it does not maintain a planner model loop or implement a live provider. Replay observations are always synthetic. In-process adapter callbacks are not an isolation boundary; future live adapters must enforce their own deadlines and confinement.

The [Stage 2 contract](stage2-contract.md) records the exact enforced boundaries and exceptions to the full host target above: state-token serialization instead of assistant-turn inspection, immutable supplied context instead of guaranteed privileged message placement, bounded local tool requests instead of model billing control, and explicit recovery/cancellation instead of observing private model stop reasons. Other app tools cannot be disabled by this MCP server. Exact model and response identifiers remain null when the desktop client does not expose them.

Earlier API-specific claims about model availability, system-role message insertion, refusal fallback settings, and cache behavior have been removed. They are neither needed nor asserted for the desktop prototype. A future fully restricted host must satisfy sections 1 through 5 before claiming full-host conformance.

## Local runtime boundary

The personal/local profile follows [local-contract.md](local-contract.md). Claude Code supplies the planner/tool loop. The Python launcher starts that native loop and an internal run-bound MCP server; it does not implement a competing model loop. Fresh restricted subject processes receive an explicit recognized skill invocation. Subscription-token and API-key modes use isolated configuration and separate credential environments. Historical Desktop host limitations below apply only to their original profiles.
