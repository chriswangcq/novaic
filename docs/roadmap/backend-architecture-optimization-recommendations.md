# Backend Architecture Optimization Recommendations

| Field | Value |
|---|---|
| **Status** | Settled baseline; implementation tickets through PR-146 closed as of 2026-05-01 |
| **Created** | 2026-04-28 |
| **Scope** | Backend business and architecture logic after the agent-root / wake-scope Cortex path stabilized. |
| **Primary Goal** | Keep Cortex simple, make Agent Runtime predictable, and remove legacy compatibility paths that distort the mental model. |

## Executive Summary

The current backend direction is broadly correct. The main path is now understandable:

```text
Business receives message
  -> message_outbox / DispatchSubscriber
  -> Queue Saga
  -> Agent Runtime creates agent-root + wake scope
  -> Cortex renders scope tree / active context
  -> LLM calls tools
  -> LLM closes current wake with skill_end(report=...)
  -> report becomes that scope's summary.md
  -> wake_finalize performs runtime cleanup
```

The remaining problems are not that Cortex is inherently complicated. The core Cortex responsibility should stay small:

1. Maintain a LIFO scope tree.
2. Persist scope content and summaries.
3. Assemble LLM context from that tree.

Most remaining backend risk lives around Cortex: Runtime compatibility residue, message delivery recovery, Business service breadth, and the fact that LLM behavior is still part of the state machine.

The recommended direction is not to add another memory layer. It is to make the current single path stricter, observable, and easier to delete around.

## Current Mental Model

### Service Responsibilities

| Area | Current Role | Desired Boundary |
|---|---|---|
| Cortex | Scope tree, scope content, DFS context assembly, active stack checks. | No user profile inference, no automatic memory, no business task system, no guessed summary. |
| Agent Runtime | Runs wake sagas, calls LLM, dispatches tools, closes wake lifecycle. | Owns lifecycle control and retries, but should not invent cognitive memory. |
| Business | Owns agent/subagent/message/model/task entities, action hooks, dispatch subscriber, internal APIs. | Central business API is acceptable, but internal modules need sharper boundaries. |
| Queue Service | Durable saga/task execution and recovery. | Remain infrastructure; no business semantics beyond execution state. |
| Gateway | Auth, Blob proxy, app websocket, signaling. | Stay thin. No agent business logic. |
| Device | Device registry and hardware/VM command routing. | Stay infrastructure. Business decides when to call it. |
| Entangled | Entity storage and realtime sync. | Business should remain the only normal direct Entangled HTTP consumer. |

### Current Continuity Rule

The desired rule is:

> The LLM closes a scope with `skill_end(report=...)`; that exact `report` is the closed scope's `summary.md`.

There should be no competing continuity paths such as automatic wake summaries, chat-reply-derived memory, inferred user profile, or hidden Recall snippets.

## Design Principles

### 1. One Concept, One Owner

If a concept has two owners, it will drift.

Examples:

- Scope summaries belong to Cortex scope closure, not Business message history.
- Message delivery belongs to Business/Queue/Runtime, not Cortex memory.
- User-facing replies belong to `chat_reply`, not raw assistant content.
- Subagent task results should belong to an explicit result/report channel, not implicit wake cleanup.

### 2. No Inferred Long-Term Memory

The system should not infer durable facts from `chat_reply`, raw conversation text, or generic wake closure.

If a fact must survive, it should either:

- appear in an LLM-written scope summary, or
- go through a separate explicit product feature later.

For now, user profile and automatic memory are intentionally out of scope.

### 3. Liveness and Continuity Are Different

Runtime must always be able to escape a stuck wake. That is liveness.

But forced cleanup should not pretend to be a good cognitive summary. That is continuity.

When the LLM fails to close a scope properly, the system should prefer:

- clear metrics and logs,
- a visible failure reason,
- bounded retries,
- structural cleanup,

rather than silently creating a fake summary.

### 4. Recovery Logic Must Be Observable

The system already has meaningful recovery machinery: message outbox, claimed/consumed lifecycle, orphan detection, stuck-claimed detection, health worker, scheduler, queue recovery.

That is acceptable only if production debugging can answer:

- Which message woke the agent?
- Which scope consumed the message?
- Which LLM call saw which scope tree?
- Did the LLM reply?
- Did the LLM close the wake?
- If not, which fallback finalized it?

### 5. Delete Compatibility Paths Aggressively

The project is still moving fast. Backward compatibility for abandoned local data or dead services is often more dangerous than deletion.

Stale paths should be removed when they:

- expose old commands,
- appear in system prompts,
- participate in hot-path cleanup,
- keep old schema fields alive,
- or mislead future maintainers about the architecture.

## Priority Optimization Areas

### P0. Scope Closure Contract Hardening

**Problem**

The wake scope is now a real work container, but successful continuity still depends on the model calling `skill_end(report=...)`. Runtime can retry, but after retry/round caps it must force-finalize.

**Business Impact**

If the LLM replies but does not close the wake, the user may see a correct response while future wakes lose the important continuity summary. This is exactly the class of bug that caused "I told you my name, why did you forget?" confusion.

**Recommended Direction**

- Keep the single summary path: `skill_end(report=...)`.
- Treat forced finalize as an exceptional lifecycle escape, not as a memory path.
- Make model non-compliance highly visible in logs and metrics.
- Make LLM prompt/tool descriptions sharper: reply first, then close current stack-top scope with a concise report when the turn is done.
- Add snapshot tests for representative LLM calls.

**Acceptance Signals**

- Normal user-message wake produces exactly one LLM `chat_reply` and one `skill_end`.
- Next wake sees the previous wake as a folded scope summary.
- No raw assistant content is treated as user-visible unless sent through `chat_reply`.
- Forced finalize increments a dedicated metric and records reason, but does not invent a fake user-memory summary.

### P1. Clarify Structural Finalize vs Summary Closure

**Problem**

There are two operations that can close scope state:

- LLM-visible `skill_end(report=...)`: semantic close, writes `summary.md`.
- Runtime `wake_finalize`: lifecycle cleanup, should not invent summary.

The architecture is sound, but names/comments must keep this distinction obvious.

**Business Impact**

If developers mix these concepts, they may reintroduce automatic "wake summary" or silently persist chat-derived memory.

**Recommended Direction**

- Document "semantic close" vs "structural finalize".
- Keep `wake_finalize` report empty unless there is a conscious product decision to add a separate failure marker file.
- Do not name forced cleanup output `summary.md`.
- Tool descriptions should tell the LLM it owns the summary when it closes the current wake.

**Acceptance Signals**

- Code comments and docs never say wake finalize creates durable summaries.
- Operational logs can distinguish `closed_by=llm_skill_end` from `closed_by=runtime_force_finalize`.
- Folded summaries shown in LLM context originate from `skill_end(report=...)`.

### P1. Retire IM Replay from Cognitive Continuity

**Problem**

Runtime had IM replay logic through `wake_replay_pending`. Even if originally framed as message-delivery reliability, it was a second context path next to Cortex scope summaries.

**Business Impact**

If replay is treated as memory, old messages may be used to patch continuity bugs instead of fixing scope summaries. That leads to duplicated context, stale turns, or the illusion that Cortex has multiple memory paths.

**Recommended Direction**

- Retire the Runtime replay path entirely. PR-113 performs this cleanup.
- Keep current wake delivery on `scope.meta.input_message_ids` by-id assembly.
- Keep cross-wake continuity on agent-root scope tree only.
- Add guardrails proving `WAKE_IM_REPLAY`, `<CHAT_HISTORY>`, and `wake_replay_pending` do not exist in Runtime hot code.

**Acceptance Signals**

- Context snapshots show only current wake inputs plus folded scope summaries.
- "User told agent a name, then asked later" smoke test passes through folded summaries, not replayed chat history.
- Runtime hot code has no replay env switch, budget helper, or replay marker.

### P1. Improve Summary Quality Without Adding Another Memory Layer

**Problem**

`summary.md` is free text written by the LLM. That is flexible, but quality can vary.

**Business Impact**

The agent may remember too little, too much, or the wrong thing. Since user profile is intentionally disabled for now, summary quality is the practical limit of continuity.

**Recommended Direction**

Do not add automatic memory. Instead, improve the LLM-visible contract:

- Good summary examples in `skill_end` description.
- Explicit instruction to include durable user preferences/facts learned in the turn.
- Compact examples for simple chat, task completion, failed work, and subagent delegation.
- Snapshot tests that assert key facts appear in the resulting folded summary.

**Acceptance Signals**

- Simple preference turns produce summaries like `User asked to be called 大哥.`
- Smoke tests can verify this fact appears in the next LLM context.
- Summary text stays concise and future-self oriented.

### P1. Business Service Boundary Tightening

**Problem**

Business currently owns many domains: agent, subagent, messages, task records, model lookup, skill matching, device orchestration, action hooks, entity proxying, and dispatch subscriber behavior.

**Business Impact**

Business is intentionally central, but too many responsibilities make changes risky. A message-delivery fix can accidentally affect agent state, model lookup, or device orchestration.

**Recommended Direction**

Keep Business as the external service boundary, but split internal modules by domain contract:

- `messages`: chat messages, outbox, lifecycle transitions.
- `agents`: agent/subagent state and ownership.
- `dispatch`: assembler/subscriber handoff.
- `models`: model config lookup.
- `devices`: device orchestration facade.
- `entity_proxy`: generic Entangled CRUD boundary.

Do not split services yet unless deployment pain requires it. First split concepts and tests.

**Acceptance Signals**

- New business logic has a clear domain module owner.
- Entity CRUD proxy remains generic and boring.
- Agent wake flow tests do not need to import unrelated Business modules.

### P2. Subagent Result Contract

**Problem**

Sub-subagents that complete without explicitly sending a result back to the parent leave the parent with completion state but little substance.

**Business Impact**

Delegated tasks can appear done while the parent has no actionable result. This is bad for complex multi-agent work.

**Recommended Direction**

- Use the unified IM channel as the result path: child agents send outcomes to the parent with `subagent_send(target_subagent_id="<parent>", message="...")`.
- Strengthen tool descriptions for child agents: if delegated work has an outcome, send an explicit parent-directed IM.
- Consider making missing parent-directed IM visible as `completed_without_result`.
- Do not infer child result from chat text or scope summary unless explicitly designed.

**Acceptance Signals**

- Parent can distinguish "child completed with result" from "child completed without result".
- Child-agent smoke tests verify the parent sees results only through explicit parent-directed IM.

### P2. Message Recovery Complexity Management

**Problem**

Message delivery now includes outbox rows, lifecycle transitions, subscriber process, queue sessions, pending triggers, health recovery, stuck-claimed scans, and orphan scans.

This is robust but hard to reason about.

**Business Impact**

Edge bugs here manifest as duplicate replies, missed messages, ghost sessions, stale "read" states, or multiple wake attempts.

**Recommended Direction**

- Maintain a single message lifecycle diagram as the source of truth.
- Add one "trace a message id" operational command or endpoint.
- Make `message_id -> scope_id -> saga_id -> llm_request_id -> tool_call_ids` traceable.
- Keep health/scheduler as recovery-only, not primary dispatch.

**Acceptance Signals**

- Given a user message id, logs can answer whether it was pending, claimed, consumed, orphaned, or recovered.
- Smoke tests cover duplicate message delivery and pending-trigger buffering.

### P2. Retired Schema Fields Cleanup

**Problem**

`historical_summary`, `handoff_notes`, and similar retired fields remain in schemas for migration tolerance.

**Business Impact**

They are not breaking runtime today, but they keep old concepts discoverable and invite reuse.

**Recommended Direction**

- If historical data can be discarded, delete the columns from authoritative schema.
- If a column must remain temporarily, mark it with a removal ticket and forbid live reads/writes.
- Add grep/CI guardrails for old field names outside migration/retired docs.

**Acceptance Signals**

- No active code path reads or writes retired continuity fields.
- New developers do not see old summary channels in primary schema definitions.

## LLM Call Contract Backlog

This section was merged from the older standalone LLM-call backlog note so backend architecture and LLM-call contract work have one roadmap entry point.

These are not immediate bugs. They are contract improvements that make Cortex, Agent Runtime, and model calls easier to reason about, test, and evolve.

### C1. Prompt/Tool Contract Linter

Build a preflight check that compares LLM-visible prompt text against the actual `tools[]` names for the same request.

Desired outcome: generated LLM calls cannot silently contain phantom tool names, stale quick-reference snippets, or role-inappropriate tool instructions.

### C2. Dynamic Tool Quick Reference

Generate the "工具速查" section from the same registry that builds `tools[]`, rather than maintaining a hand-written prompt list.

Desired outcome: adding, removing, or renaming a tool updates the prompt reference automatically.

### C3. Role-Aware Tool Bundles

Split tool exposure by agent role and wake type:

- main user-facing agent
- child subagent
- system wake
- simple chat turn
- implementation/debug turn

Desired outcome: the model sees only the tools that make sense for its current role and task.

### C4. Context Block Budget Policy

Define a budget and priority order for folded scope summaries, current IM messages, active scope stack, and system instructions.

Desired outcome: context growth is predictable, and short prior turns do not get duplicated across blocks.

### C5. Wake-Scope Closure Summary Quality

Keep the current contract: the model closes the current wake scope with `skill_end(report=...)`, and that exact report becomes the scope's `summary.md`.

Desired outcome: summaries are useful by default without reintroducing automatic memory, chat-reply-derived memory, or a separate root-scope finalizer path.

### C6. Clean IM Body and Attachment Rendering

Standardize how `content.text`, empty attachments, non-empty attachments, and future rich-message fields render after the IM header.

Desired outcome: the model reads the user's actual utterance first, with attachment data represented intentionally.

### C7. Shell Policy Tiers

Give `shell` a small, explicit policy model:

- read-only inspection
- local edits/tests
- server mutation
- destructive data operation
- external/network side effect

Desired outcome: the model can reason about command risk without needing a giant procedural rulebook.

### C8. Request Parameter Normalizer

Normalize provider payloads before dispatch so unset optional fields are omitted and provider-specific defaults remain centralized.

Desired outcome: cleaner snapshots and fewer provider compatibility surprises.

### C9. LLM Call Snapshot Tests

Add golden snapshots for representative turns:

- first greeting
- "what can you do?"
- shell-enabled debugging turn
- child subagent report
- system wake with prior folded summaries

Desired outcome: prompt drift becomes visible in review.

### C10. LLM-Call Observability

Log compact metadata for every LLM request:

- tool names
- context block names and token estimates
- model id
- provider
- optional parameter keys actually sent
- whether folded scope history was present

Desired outcome: production debugging can answer "what did the model actually see?" without dumping full prompt content into logs.

## Current Known Imperfections (2026-04-30)

These are not new architecture directions. They are the current rough edges observed after the device status and mDNS fixes, recorded here so they do not disappear into chat history.

### I1. VmControl Cargo.lock Is Stale

**Observation**

`cargo check --locked` in `novaic-app/src-tauri/vmcontrol` currently fails because `Cargo.lock` does not match the current dependency graph. `cargo check --offline` passes after Cargo locally resolves the graph, but that also produces unrelated lockfile churn.

**Why It Matters**

Build determinism is weaker than it should be. A later developer may accidentally mix dependency refresh noise into an unrelated bug fix, or CI may fail if it requires locked builds.

**Recommended Direction**

- Refresh `vmcontrol/Cargo.lock` in a dedicated dependency-hygiene change.
- Do not mix the lock refresh with feature or bug-fix commits.
- After the refresh, make `cargo check --locked` the normal verification command for VmControl.

**Acceptance Signals**

- `cargo check --locked` passes in `novaic-app/src-tauri/vmcontrol`.
- The lockfile diff is reviewed as dependency maintenance, not hidden inside product logic changes.

### I2. WebRTC mDNS Policy Needs Runtime Smoke Closure

**Observation**

VmControl now explicitly disables `webrtc-rs` mDNS ICE handling. This removes the macOS `0.0.0.0:5353 -> No route to host` error path and matches the current STUN/TURN-first architecture.

**Why It Matters**

This is the right product behavior today, but it is still a conscious policy tradeoff: pure LAN `.local` host-candidate discovery is not part of the supported connection path. The fix has compile-level verification, but ICE behavior is runtime-sensitive, so it still needs an end-to-end WebRTC smoke across Host Desktop, Linux VM, and Android before the issue is fully closed.

**Recommended Direction**

- Keep mDNS disabled while Gateway-provided STUN/TURN is the authoritative WebRTC path.
- If LAN-only direct discovery becomes a product requirement later, design it explicitly instead of relying on `webrtc-rs` defaults.
- Keep logging focused on actual WebRTC connection failure, not multicast resolver noise.
- Run a small manual or scripted smoke for each WebRTC source type:
  - Host Desktop stream opens and receives frames.
  - Linux VM stream opens after VM start.
  - Android stream opens after emulator/device start.
- Check logs during the smoke for mDNS noise and ICE failure transitions.

**Acceptance Signals**

- Host Desktop / Linux VM / Android WebRTC sessions connect through the STUN/TURN path.
- Each stream reaches WebRTC `connected`.
- No repeated mDNS send errors appear during connection setup.
- The frontend device monitor reports work in user-facing terms, not low-level debug payloads.

### I3. Device Status Polling Has Multiple Owners

**Observation**

The Host Desktop false `Error` badge was fixed by changing polling failure behavior and by making `PcClientDeviceList` start polling for the devices it renders. This is correct for the bug, but status polling still has more than one UI owner.

**Why It Matters**

Multiple components can refresh the same `DeviceStatusStore`. That is safe enough now because updates are keyed by `(device_id, pc_client_id)`, but it is not the cleanest long-term shape.

**Recommended Direction**

- Keep the current bug fix.
- Later consolidate device status polling ownership so visible device lists subscribe to one clear polling coordinator.
- Preserve the invariant that probe failures do not overwrite a known entity state with `error`.

**Acceptance Signals**

- Device status refresh has one obvious owner or coordinator.
- A transient `get_status` failure does not display a persistent red `Error` for a running Host Desktop.
- Unit tests keep the failure-normalization invariant locked.

### I4. Current Fixes Need Commit/Deployment Closure

**Observation**

At the time this note was written, the workspace contains local fixes for:

- Host Desktop false `Error` status.
- VmControl WebRTC mDNS noise.

**Why It Matters**

The code is locally fixed, but an uncommitted local fix is not a stable team artifact.

**Recommended Direction**

- Commit the two fixes as small, reviewable changes.
- Deploy/restart the app/runtime component that owns VmControl before declaring the mDNS noise gone in the running product.

**Acceptance Signals**

- Git history contains explicit commits for both fixes.
- The running app no longer shows false Host Desktop `Error`.
- The running VmControl no longer emits repeated `webrtc_mdns::conn` errors during WebRTC setup.

## Recommended Roadmap

### Phase 1: Contract Hardening

Goal: make the current path measurable and unambiguous.

Tasks:

- Add LLM call snapshot tests for simple chat, preference capture, shell turn, child subagent, and no-tool retry.
- Add metrics/log fields for `closed_by`, `finalize_reason`, `stack_depth`, and whether `summary.md` came from LLM `skill_end`.
- Tighten `skill_end` tool description around current wake closure.
- Ensure folded summaries in next wake are ordered after the system prompt in a consistent, documented context order.

### Phase 2: Finalize Semantics Cleanup

Goal: separate normal semantic closure from exceptional lifecycle cleanup.

Tasks:

- Document `skill_end(report)` as the only normal summary path.
- Document `wake_finalize` as structural cleanup.
- Add alerting for force-finalize events.
- Decide whether forced finalize should write a non-summary failure artifact. Default recommendation: no fake `summary.md`.

### Phase 3: Message Delivery Traceability

Goal: make message wake behavior debuggable end-to-end.

Tasks:

- Add or standardize a message trace endpoint/CLI.
- Trace `message_id`, `scope_id`, `saga_id`, `llm_request_id`, and `tool_call_id`.
- Keep IM replay named as delivery replay.
- Add regression smoke: "tell name -> later ask name" must pass through folded scope summary.

### Phase 4: Business Internal Modularization

Goal: reduce Business blast radius without splitting deployment.

Tasks:

- Group Business internals by domain.
- Move domain tests next to domain behavior.
- Keep generic Entity proxy separate from agent/message orchestration.
- Add dependency direction rules: domain modules may call entity proxy, but entity proxy must not know domain semantics.

### Phase 5: Subagent Result Reliability

Goal: make delegated work outcomes reliable.

Tasks:

- Improve child-agent prompt/tool descriptions for parent-directed `subagent_send`.
- Add parent-visible `completed_without_result` distinction if useful.
- Test child completion with and without explicit parent-directed IM.

### Phase 6: Schema Debt Deletion

Goal: remove old continuity concepts from the database model.

Tasks:

- Delete retired summary columns when data reset is acceptable.
- Add grep guardrails for old field names.
- Update schema docs and startup checks.

## Suggested Tests and Smoke Checks

### Unit Tests

- Cortex scope LIFO:
  - open child scope;
  - close top scope;
  - reject closing non-top scope;
  - reject closing agent root.
- Cortex folded summary:
  - `skill_end(report="X")` persists `summary.md`;
  - DFS renders closed scope as summary;
  - active scope content remains expanded.
- Runtime no-tool behavior:
  - no tool call with non-empty stack retries;
  - after retry cap, force-finalize is logged as exceptional.
- Runtime reply + close behavior:
  - `chat_reply` alone does not finalize while wake stack is non-empty;
  - `chat_reply` followed by `skill_end` finalizes normally.
- LLM context order:
  - system prompt appears before folded scope history;
  - active scope stack appears near the end;
  - tool result ids are preserved.

### Smoke Tests

- `叫大哥` -> next wake `我叫啥` should answer from folded summary.
- `PR smoke: 请简短回复收到` should produce one visible reply and one concise scope summary.
- Child subagent delegation should produce explicit parent-directed `subagent_send` when result is expected.
- Simulated LLM no-tool turn should not create fake memory.
- Simulated force-finalize should not write a normal summary.

### Operational Checks

- `rg "Wake summary|historical_summary|handoff_notes"` should only find retired docs or explicitly quarantined code.
- A single message id should be traceable from Business message row to Runtime scope and LLM request.
- Dashboards should expose force-finalize count and stack-nonempty retry count.

## Non-Goals

- Do not reintroduce Recall.
- Do not infer memory from `chat_reply`.
- Do not use user profile as a workaround for scope-summary quality.
- Do not create an automatic summary service behind Cortex.
- Do not split Business into multiple deployable services before internal boundaries are stable.
- Do not make Cortex responsible for business task management.

## Settled Decisions — 2026-05-01

1. Forced finalize should not create a durable memory artifact.
   - Decision: use logs/metrics and lifecycle status only. Do not create `finalize.json` or any file that can be confused with `summary.md`.
2. Child subagents should communicate results through IM, not a hidden completion/report channel.
   - Decision: do not hard-require a parent-directed result at lifecycle completion. If a result matters, the child must send it with the IM path. Missing result is a lifecycle/monitoring signal, not a second message channel.
3. Retired schema fields should be deleted from active contracts when the current deployment can tolerate it.
   - Decision: no compatibility branch by default. If a field cannot be physically dropped in the same PR, leave an explicit removal ticket and a grep guardrail.
4. Business should not be physically split yet.
   - Decision: keep Business as one deployable service for now; split internal domain contracts and tests before considering service decomposition.

## Bottom Line

The backend does not need a new memory architecture. It needs discipline around the one architecture now chosen:

```text
scope tree + explicit LLM-written summaries + reliable message delivery
```

The biggest win is to delete old compatibility surfaces and make exceptional lifecycle cleanup impossible to confuse with cognitive continuity.
