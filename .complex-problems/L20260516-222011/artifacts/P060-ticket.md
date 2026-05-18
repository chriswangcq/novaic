# Ticket: audit Cortex shell step projection

## Problem Definition

Runtime shell output is bounded, but Cortex step/history projection may still rehydrate durable shell payloads into LLM history. The Cortex side must preserve terminal semantics and avoid full stdout re-inline.

## Proposed Solution

Inspect Cortex step result projection and context event projection code for shell/tool output handling. Verify shell durable payloads are represented as bounded `tool-output.v1` text in history and raw payloads are only available through explicit payload/file lookup.

## Acceptance Criteria

- Cortex history projection does not inline `durable_payload.raw.stdout` into normal LLM messages.
- Shell step payloads are projected as bounded terminal text or pointers.
- Focused Cortex tests cover tool output projection and step result projection around shell/tool payloads.

## Verification Plan

Run focused `rg` scans for `shell_result`, `durable_payload`, `raw`, `tool-output.v1`, and step projection code in Cortex. Run adjacent Cortex projection tests.

## Risks

- Display/image durable payloads intentionally need special projection. Shell payloads should not accidentally share that media projection path.

## Assumptions

- Runtime already ensures public shell `llm_content` is bounded; Cortex should consume that bounded projection for history.
