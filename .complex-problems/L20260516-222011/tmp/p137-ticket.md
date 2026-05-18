# Map active skill stack injection ordering and media interaction

## Problem Definition

Active skill stack messages are injected as late system messages into LLM context. Because current-round display perception depends on message ordering and current tool-result selection, this injection path must be mapped separately from tool-result projection to ensure stack messages do not accidentally demote current display media to historical text-only context or duplicate stale stack instructions.

## Proposed Solution

Audit the active stack source, projection, and final context assembly path from stored/projected stack state into provider-ready LLM messages. Map the ordering relative to assistant tool calls, tool result messages, display projections, and provider multimodal conversion. Run focused tests that cover current display media plus active stack injection. If the path is broad or reveals stale duplicate injection, split into child problems for source mapping, ordering/media tests, and cleanup.

## Acceptance Criteria

- The code path that produces the `[Active skill stack ...]` system message is identified.
- The final ordering relative to tool messages and display/media expansion is documented.
- Tests or existing fixtures prove current-round display media remains current display perception even when active stack is appended after tool results.
- Any stale or duplicate injection path is either removed directly or split into a follow-up/child problem.

## Verification Plan

Run targeted `rg`/source inspection for active stack injection text and context assembly. Execute focused runtime/Cortex tests for context preparation, display media projection, and active skill stack injection. Add or tighten tests if ordering is not explicitly covered.

## Risks

- Active stack injection may be spread across runtime prompt assembly and Cortex projection, requiring split children rather than one bounded execution.
- Some order-dependent tests may be brittle unless they assert semantic placement rather than exact large-message snapshots.

## Assumptions

- The display/media projection fixes already completed in P136 remain the base contract.
- This ticket should not change provider multimodal conversion unless the stack ordering audit proves it is still part of the failure path.
