# Rerun hidden input focused tests from correct runtime cwd ticket

## Problem Definition

The previous P474 verification failed because tests with relative source paths were invoked from the repository root. This follow-up must rerun the exact focused verification from `novaic-agent-runtime`.

## Proposed Solution

Run pytest from `novaic-agent-runtime` for the same focused test files using paths relative to that directory. Re-run the hidden-input guards from the repository root and save all outputs under `.complex-problems/L20260516-222011/tmp/p478/`.

## Acceptance Criteria

- Focused pytest rerun exits `0`.
- Guard output remains clean for runtime env reads, decision-adapter direct `ServiceConfig` reads, and old focused-test monkeypatch patterns.
- Logs are saved and cited.

## Verification Plan

Inspect pytest exit/log and guard artifact.

## Risks

- If tests still fail from the correct cwd, that indicates a real code/test issue and should be recorded honestly.

## Assumptions

- No code changes are needed for this follow-up.
