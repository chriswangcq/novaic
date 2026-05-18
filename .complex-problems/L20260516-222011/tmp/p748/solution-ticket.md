# Run focused media-boundary tests

## Summary

Run focused tests that protect shell artifact output, context/history projection, display multimodal projection, Device route behavior, and VMuse resource hygiene.

## Problem Definition

The final media boundary must be executable. Scans are insufficient without tests for shell, projection, display, Device, and resource sync behavior.

## Proposed Solution

Run the already-identified focused test groups with explicit `PYTHONPATH` where required. Record pass/fail evidence exactly.

## Acceptance Criteria

- Shell/Blob artifact contract tests pass.
- Runtime/Cortex projection/history/display tests pass.
- Device focused route/import tests pass.
- VMuse resource hygiene passes.
- Any failure is either fixed or recorded as a blocker.

## Verification Plan

- Run focused pytest groups.
- Run Device route import/path assertion.
- Record results in the ledger.
