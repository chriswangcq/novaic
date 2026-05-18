# Audit end-to-end display screenshot regression

## Problem Definition

The real user flow is multi-hop: shell/device command creates a screenshot artifact, the agent calls `display` on that blob, and the next LLM request receives an image while the display tool result remains placeholder-only. P191 verifies that this integrated path has regression coverage.

## Proposed Solution

Inspect runtime shell artifact output tests, display wrapper tests, context/multimodal tests, runtime-to-factory request tests, and Factory provider/log tests added or verified by sibling problems. Add an integration-style regression if the chain has no single test or clearly documented coverage map from shell artifact to provider request.

## Acceptance Criteria

- End-to-end coverage map is documented from shell screenshot artifact through display and provider request.
- Tests prove shell screenshot output uses artifact/blob manifest, not raw base64 text.
- Tests prove display result becomes placeholder tool content plus provider-visible image content.
- Tests prove provider/factory request preserves image content.
- Focused regression tests pass.

## Verification Plan

Run focused tests across runtime shell output, display multimodal context assembly, runtime factory client, and factory provider/log routes. Add a targeted integration test if there is a missing hop.

## Risks

- A true device screenshot smoke may require live device infrastructure; this ticket can use deterministic unit/integration tests for the contract chain.
- The UI visual display of screenshots is separate from backend LLM request correctness.

## Assumptions

- P184 covers bounded shell text.
- P188-P190 cover projection, runtime assembly, and provider conversion.
