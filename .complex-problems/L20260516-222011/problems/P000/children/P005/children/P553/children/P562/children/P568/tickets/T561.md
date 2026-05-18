# Classify Cortex Stable Path Compatibility Residue

## Problem Definition

P568 must classify Cortex stable-path and temp-path compatibility residue, including `/tmp/novaic-cortex-sandbox-*`, `/cortex/ro`, `/cortex/rw`, command path adapters, and guardrails against leaked backing paths.

## Proposed Solution

Run targeted scans over Cortex code/tests for temp backing path markers, stable path constants, compatibility adapters, and path abuse tests. Read relevant slices and classify hits.

## Acceptance Criteria

- Scan commands and outputs are recorded.
- Stable path constants are classified as intended or risky.
- Ephemeral path rejection is classified.
- Any compatibility branch or adapter needing deletion is passed to P554.

## Verification Plan

Use `rg` scans for `novaic-cortex-sandbox`, `/cortex/ro`, `/cortex/rw`, `STABLE_CORTEX`, `path_adapter`, `adapter`, and related tests.

## Risks

- Stable path constants are expected in the final design and must not be mistaken for residue.
- Guardrails may mention old bad paths intentionally.

## Assumptions

- `/cortex/ro` and `/cortex/rw` are the intended stable shell paths.
