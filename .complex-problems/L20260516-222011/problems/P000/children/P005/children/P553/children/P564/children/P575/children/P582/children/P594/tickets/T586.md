# Ticket: Inventory Historical Display Replay Tests

## Problem Definition

Historical `display` tool results must be safe to replay in future LLM calls. They should use the `history` projection and must not fetch BlobRefs or create provider image content.

## Proposed Solution

Scan runtime tests for history projection and image-ref replay behavior, inspect exact test slices, and run a focused test subset that would fail if historical display results are resolved as images.

## Acceptance Criteria

- Exact scan commands and focused test commands are recorded.
- Tests proving old display messages use `history` projection are cited.
- Tests proving historical `image_ref` remains `image_ref`/text-only and does not fetch Blob bytes are cited.
- Any missing coverage is captured as a follow-up.

## Verification Plan

Run focused runtime tests around `expand_messages_for_llm` history behavior and mixed history/current display ordering.

## Risks

- Some tests may prove no Blob fetch but not full LLM transport shape; record directness carefully.

## Assumptions

- Current-round display injection is already covered by P593; this ticket is only about historical replay safety.
