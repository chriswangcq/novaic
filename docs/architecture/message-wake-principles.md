# Message Wake Principles

This is the current contract for message-driven agent wakeup. Historical
archaeology belongs in ticket history, not in this architecture contract.

## Minimal Model

1. Messages that can wake an agent are Environment IM events.
2. Business creates Environment notifications for wake-eligible IM events.
3. Business subscribes to those notifications and delegates request
   construction to `common.wake.DispatchAssembler`.
4. Runtime Queue Service owns session start/buffer/finish.
5. Cortex owns the LIFO scope tree and LLM context assembly.

## Wake-Eligible Message Types

Only these chat message types are wake-eligible:

- `USER_MESSAGE`
- `SUBAGENT_SEND`

Everything else is data or UI history unless a separate system scheduler or
operator action explicitly dispatches a wake.

## Dispatch Invariants

- Dispatch request construction has one canonical implementation:
  `common.wake.DispatchAssembler`.
- Business and Runtime must not hand-build Queue dispatch payloads.
- Message-triggered dispatch idempotency is derived from the message id.
- `subagent_id` is explicit for subagent-targeted messages; main-agent fallback
  is assembler-owned.
- Health/recovery workers are recovery and observability mechanisms, not the
  normal message-delivery path.

## Subagent Communication

Subagent communication is IM:

- Parent to child: `SUBAGENT_SEND`.
- Child to parent: `SUBAGENT_SEND`.
- Spawn initial task: create the child, then send the task as `SUBAGENT_SEND`.

There is no separate result/report/query/cancel tool family in the LLM-facing
contract. If a child has a result, it sends a parent-directed IM.

## Cortex Boundary

Cortex stays intentionally small:

1. Maintain the LIFO scope tree.
2. Assemble the LLM context.

Closed scopes are represented by their `summary.md`; active scopes stay
expanded. Cortex must not infer long-term memory from chat text, user profile,
or business task state.

## Operational Guardrails

- Current LLM tool bundles must expose only the canonical tool schema.
- Current message lifecycle contract must not include deleted wake message
  types.
- Current prompt contract must not reintroduce automatic wake summaries,
  profile-derived memory, or parallel summary paths.
- Current docs and runbooks must describe the IM path as the only subagent
  communication path.
