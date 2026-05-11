# Final CLI Blob contract verification pass

## Problem Definition

The CLI Blob contract work needs a final pass that compiles generated commands, runs focused tests, scans for remaining raw artifact stdout risks, and validates the ledger.

## Proposed Solution

Run a final verification suite across `novaic-cortex` and `novaic-agent-runtime`, inspect residual Blob URI namespace usage, and validate the solve-complex-problems ledger. Record any remaining gaps explicitly.

## Acceptance Criteria

- Generated `agentctl`, `cortex`, and `devicectl` scripts compile.
- Focused Cortex tests for shell capabilities, Blob payloads, tool-output projection, schemas, and payload events pass.
- Focused runtime tests for shell output and tool-output contracts pass.
- Residual scans show no active CLI raw artifact stdout path.
- Ledger validation succeeds.

## Verification Plan

- Compile generated capability scripts with `py_compile`.
- Run Cortex focused test suite.
- Run agent-runtime focused test suite.
- Run `rg` scans for stale namespace and raw artifact fields in shell capability paths.
- Run `ledger.py validate` and render/status if available.

## Risks

- Full repo test suite may include unrelated failures from other dirty worktree changes; focused contract tests are the primary acceptance gate.

## Assumptions

- This ticket is verification-only unless a directly related residual problem is discovered.
