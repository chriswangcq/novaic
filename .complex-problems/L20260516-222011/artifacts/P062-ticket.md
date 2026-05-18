# Ticket: audit and classify base64 leakage surfaces

## Problem Definition

Active code contains legitimate and illegitimate uses of base64/image markers. We need to classify them before implementing a guard so the guard is precise.

## Proposed Solution

Run targeted scans across runtime, Cortex, LLM Factory, device/shell capability tests, and docs for `/9j/`, `data:image`, `base64`, `_mcp_content`, `image_url`, `display`, and `shell_result`. Summarize which occurrences are legitimate structured payloads, which are tests/fixtures, and which public-text paths need guard coverage.

## Acceptance Criteria

- Scan covers active runtime/Cortex/Factory paths.
- Legitimate structured image payload locations are identified.
- Forbidden public-text leakage surfaces are identified or confirmed covered.
- Recommended guard placement is explicit.

## Verification Plan

Use `rg` and focused file inspection. No production code changes expected in this audit ticket.

## Risks

- A broad scan can be noisy. The output should classify high-risk active paths rather than list every occurrence.

## Assumptions

- Implementation of a new/strengthened guard is handled by sibling child `P063`.
