# Audit Runtime Local Shell Fallback Residue

## Problem Definition

The runtime and Cortex shell path should fail closed if sandboxd/LogicalFS wiring is unavailable. Hidden fallback to local subprocess execution or local filesystem semantics would recreate the old unstable behavior.

## Proposed Solution

Scan runtime, Cortex, sandbox service, and SDK code for fallback/local execution terms around shell/sandbox/subprocess execution. Inspect active contexts and classify hits as fail-closed error handling, test coverage, service implementation internals, or risky hidden fallback.

## Acceptance Criteria

- Scan output is recorded.
- Active fallback/local execution hits are classified.
- No hidden local shell fallback remains in Cortex/runtime shell execution path.
- Any risky active fallback is removed or becomes a follow-up.

## Verification Plan

Run targeted `rg` scans for fallback/local/subprocess/sandbox executor terms. Inspect `novaic-cortex/novaic_cortex/sandbox.py`, runtime shell handling, sandbox SDK/service execution code, and tests. Run affected tests if code changes are needed.

## Risks

- Sandbox service itself must execute processes, so subprocess usage can be intended there.
- Tests may define fake local executors; distinguish test doubles from production fallback.

## Assumptions

- Cortex shell execution should require sandboxd through `sandbox_sdk`; no configured executor means explicit failure.
