# Ticket: Inventory Active Stack Display Ordering Tests

## Problem Definition

The runtime appends active-stack/system messages after tool output. That must not cause the current-round `display` tool result immediately before the system message to be treated as history or text-only.

## Proposed Solution

Scan tests for active-stack/system-message ordering, latest tool-call inference, and display projection selection. Run focused tests that prove current display survives following system messages while old display messages use history projection.

## Acceptance Criteria

- Exact scans and focused test commands are recorded.
- Tests proving current display remains `display_perception` before following system messages are cited.
- Tests proving non-current display falls back to `history` are cited.
- Any missing or indirect coverage is recorded as a follow-up.

## Verification Plan

Run focused runtime tests in `test_no_historical_tool_image_injection.py` and `test_pr71_no_tool_retry_context_cleanup.py`.

## Risks

- The same tests may also cover current injection/history replay; the result must explain the ordering-specific assertion, not just reuse broad coverage.

## Assumptions

- Active stack is represented as a system message appended after the tool result in the LLM context.
