# Diagnose smoke wake shell timeout and im_reply cap

## Problem Definition

The dispatch repair v4 smoke wake reached Runtime, but the UI shows repeated shell timeouts and `im_reply cap reached (12/10)`. We need to determine why the already-created wake did not complete cleanly and whether the cause is Cortex stack/finalize logic, tool execution timeout behavior, im_reply cap behavior, or a stuck saga/session state.

## Proposed Solution

Inspect production durable state and source code in a pointer-oriented way:

- Query Queue tasks, saga state/events/outbox, session events, and session state for scope `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0` and message `18c14d716c0a`.
- Inspect Cortex scope files for steps, context, meta, stack state, and tool result payloads.
- Inspect Runtime handlers for shell execution, tool cap enforcement, im_reply cap logic, and finalize/stack decision logic.
- Correlate evidence into a causal chain and identify the first bad state transition.

## Acceptance Criteria

- Concrete cause is identified with production evidence.
- Distinguish shell timeout symptom from im_reply cap and stack/finalize behavior.
- Determine whether code should be changed, and where.
- Record the actual result and evidence in the ledger.

## Verification Plan

- Use read-only SSH/SQLite/file reads against production.
- Use local source inspection for exact code paths.
- If a fix is obvious and low-risk, implement and test in a follow-up ticket rather than mixing with diagnosis unless the ledger check demands it.

## Risks

- Production logs can be large; queries must be bounded.
- Some runtime state may have moved to Cortex archive/active paths; inspect both stable paths and DB references.
- The smoke wake might still be active; avoid mutating production state during diagnosis.

## Assumptions

- Scope `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0` belongs to the smoke v4 message.
- Read-only production inspection is allowed for diagnosis.
