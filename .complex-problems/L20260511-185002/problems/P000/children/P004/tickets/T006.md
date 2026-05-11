# Verify CLI Blob contract and remove residual old behavior

## Problem Definition

After fixing and auditing CLI command families, the repo still needs a residual pass to catch old contract examples, invalid Blob namespaces, or untested raw artifact stdout behavior.

## Proposed Solution

Run a global CLI/blob-contract scan, clean stale test fixtures or examples that encode invalid artifact namespaces, and run a final focused test suite across Cortex and runtime contract boundaries.

## Acceptance Criteria

- No active CLI command emits screenshot/file bytes inline.
- Tests and examples for runtime-generated artifacts use the contract-valid `runtime-artifact` namespace.
- Residual invalid Blob namespace usage is either cleaned or explicitly classified as non-CLI/non-contract test data.
- Final test suite covers shell capability generation, Blob artifact output, tool-output projection, and runtime shell output contract.
- Any remaining risk is recorded clearly.

## Verification Plan

- Search for `device-screenshot`, raw `screenshot` payload output, raw `data` file-pull output, and old artifact namespace examples.
- Patch residual tests/examples that contradict the new Blob contract.
- Run relevant Cortex and agent-runtime tests.
- Validate the solve-complex-problems ledger before final report.

## Risks

- Some old Blob URI strings may be intentional synthetic identifiers in lower-level storage tests; avoid changing unrelated semantics blindly.
- The final suite may expose unrelated dirty-worktree failures; record them separately if they are not caused by this change.

## Assumptions

- `runtime-artifact` is the canonical namespace for runtime-created CLI artifacts.
- `cortex-payload`, `user-file`, and `audio-input` remain valid for their own domains.
