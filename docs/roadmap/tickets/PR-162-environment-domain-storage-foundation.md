# PR-162 — Environment Domain and Storage Foundation

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-business`, docs |
| Depends on | PR-161, `agent-perception-action-architecture.md` |
| Theme | Agent subject / environment foundation |

## Goal

Build a complete, testable Environment foundation before wiring it into the live agent loop.

Environment owns external event envelopes, IM messages, notification lifecycle, sender/channel/thread identity, and resource references. It must not own domain truth, prompt assembly, Cortex folding, user profile inference, or tool execution.

## Required Process

1. Analyze current state in the relevant repos and write the findings into this ticket.
2. Create small tickets for separately testable implementation slices.
3. Implement one small ticket at a time.
4. For each small ticket: unit tests, smoke test, deploy plan/result, Git commit/merge evidence.
5. Confirm this big ticket is closed; if not closed, create/execute another small ticket before moving to PR-163.

## Planned Small Tickets

- [x] [PR-162A — Environment contract and invariant test matrix](PR-162A-environment-contract-invariants.md) — deployed in `novaic-common` commit `aa35585`.
- [x] [PR-162B — Environment persistence repository and migrations](PR-162B-environment-persistence-repository.md) — repository boundary deployed in `novaic-business` commit `045d86f`.
- [x] [PR-162C — Environment domain service and lifecycle state machine](PR-162C-environment-domain-service.md) — domain service deployed in `novaic-business` commit `b3e31f8`.

## Current-State Analysis

Completed 2026-05-02.

Current live pieces already approximate an Environment, but the ownership is implicit and spread across modules:

- Historical state at ticket creation: `chat_messages` still carried
  `lifecycle`, `claimed_by_scope`, and `lifecycle_updated_at`, and Entangled
  outbox rows were still part of the wake path.
- Current state after PR-168E and PR-229: `chat_messages` is a chat projection,
  `message_outbox` is gone from the wake path, message type shape lives in
  `novaic-common/common/contracts/chat_message.json`, and Environment
  notifications own Agent-loop lifecycle.
- `DispatchSubscriber` owns outbox draining, retry/backoff, stale-claim protection, and same-sender IM aggregation. It does not write Cortex scope input directly; it sends `message_ids` to Queue metadata.
- Runtime `session.init` receives `message_ids`, creates/uses the wake scope, and writes those ids into Cortex scope meta.
- Historical note: before PR-165, Runtime `context.read` read
  `scope.meta.input_message_ids`, fetched `chat_messages` rows from Business,
  rendered IM headers into LLM-visible prompt text, and appended the rendered
  result to Cortex context. PR-165 removed this raw-message prompt path; live
  prompt assembly now receives Environment notification ids and requires
  explicit `im_read` observation.
- Subagent communication is already represented as `SUBAGENT_SEND` message rows with metadata such as sender/target subagent id, plus the same outbox wake path.
- There is no `environment` module, no Environment contract, no Environment repository, and no explicit Environment service boundary. The closest existing contract is message lifecycle, which mixes IM/message lifecycle with wake dispatch semantics.

Conclusion: PR-162 should not rename or switch live hot paths immediately. It should first introduce an explicit Environment contract and testable foundation, then wrap or migrate existing `chat_messages`/outbox behavior behind that boundary in small steps.

## Boundary Invariants

- Environment notification is not memory.
- Environment message body is not automatically LLM context.
- Environment resource refs point to payloads owned by their source domain.
- Cortex records the agent work trajectory; Environment records the outside-world event surface.
- No fallback legacy path may coexist once this foundation is adopted.

## Done Criteria

- [x] Shared contract exists and is guarded by tests.
- [x] Persistence model exists and is covered by repository tests.
- [x] Domain service supports create/read/claim/complete/fail lifecycle semantics.
- [x] No runtime prompt behavior is changed by this foundation ticket alone.
- [x] Deployment and Git evidence are recorded in the small tickets.

## Closure

Closed 2026-05-02. PR-162 establishes a tested Environment foundation without changing the live agent loop. PR-163 can now wire Runtime/LLM tools to this service boundary.
