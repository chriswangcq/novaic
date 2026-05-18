# Verify Sandbox SDK Runtime Boundary Test Coverage

## Problem Definition

P625 must verify that tests cover the SDK/service boundary and runtime shell output contract after the shell/artifact refactor.

## Proposed Solution

Inventory and run focused tests across `novaic-sandbox-sdk`, Cortex sandboxd wiring, runtime shell output/tool path, and no historical image injection. Classify any missing coverage as acceptable or follow-up.

## Acceptance Criteria

- Exact test inventory and commands are recorded.
- Focused SDK tests run.
- Focused Cortex sandboxd wiring tests run.
- Focused runtime shell output/tool path/history tests run.
- Missing or failing coverage creates a follow-up.

## Verification Plan

Run the focused test subset used by recent boundary work and record exact outputs.

## Risks

- Some tests need specific working directory or PYTHONPATH.
- Full suite may be too broad; focused coverage must still map to boundary risk.

## Assumptions

- P623/P624 already classified SDK and runtime source paths.
