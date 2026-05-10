# Verify sandboxd extraction end to end

## Problem Definition

The extraction is only reliable if common contracts, sandboxd service behavior, Cortex active-path wiring, deployment wiring, and residue cleanup all pass verification together.

## Proposed Solution

Run the focused test suites and syntax/source checks from child tickets, run a live local sandboxd HTTP smoke for non-mounted execution, and record any environment-limited gaps explicitly. If remote deployment is executed, include fresh-smoke evidence.

## Acceptance Criteria

- Common sandbox tests pass.
- Sandboxd service tests pass.
- Cortex sandboxd wiring tests pass.
- Shell/deploy syntax and fresh-smoke lint pass.
- Live sandboxd health/execute smoke passes locally.
- Residue scans show no old active Cortex command-wrapping path.
- Any unexecuted remote deployment/smoke is called out as residual risk, not hidden.

## Verification Plan

- Run focused pytest commands.
- Start sandboxd locally, call health and execute, then stop it.
- Run source scans and script syntax checks.

## Risks

- Local macOS cannot prove the Linux mount namespace execution path through live Cortex; unit/integration tests isolate that contract, and remote deployment smoke is the stronger proof when run.

## Assumptions

- Deploying to production is a separate operational action unless explicitly requested in this run.
