# Verify runtime current/history media projection boundary

## Problem Definition

Runtime must allow provider media only for current-round display perception. Historical display results, shell results, blob/artifact manifests, and other tools must remain bounded text/manifest.

## Proposed Solution

Inspect runtime projection selection and multimodal conversion helpers, then run targeted runtime tests that cover current display media, historical image suppression, non-display image suppression, and factory-client multimodal payload construction.

## Acceptance Criteria

- Current display can produce provider image content.
- Historical display/non-display tools do not produce provider image content.
- Shell/blob/payload outputs remain bounded text/manifest through runtime path.
- Targeted runtime tests pass.

## Verification Plan

Run runtime tests for no historical tool image injection and factory client multimodal payload construction. Use code evidence from `step_result_client.py`, `context.py`, `multimodal.py`, and `tool_handlers.py`.

## Risks

- A test can cover image extraction but miss shell/blob payload bounds; include tool handler evidence from shell output contract.

## Assumptions

- Cortex projection tests cover the formatted content side; this ticket focuses on runtime consumption and conversion.
