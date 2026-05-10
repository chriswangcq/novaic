# Ticket: Cut Over Tests And Remove Old Shell Branches

## Problem Definition

After the boundary refactor, the code must stop teaching old lazy-RO command-gating behavior. Tests and residue audits should make the new active path unambiguous.

## Proposed Solution

Update tests to assert full logical view behavior and provider capabilities, then audit code for old symbols and misleading docs. Remove or replace any stale references that would lead a future agent back to command-string RO gating.

## Acceptance Criteria

- Old lazy-RO test is replaced with no-command-gating tests.
- Provider capability and RW convention env vars are tested.
- Old command-gating function names are absent.
- Active path has no `include_ro = ... command ...` style semantic branch.
- Focused sandbox tests pass.

## Verification Plan

- `pytest -q tests/test_incremental_sync.py tests/test_sandbox_sync.py`.
- `rg` for old command-gating symbols.
- Compile `sandbox.py`.

## Risks

- Stable path tests still rely on outer-command adapter because true mount is unavailable; tests must identify that as provider behavior, not final FUSE semantics.

## Assumptions

- `Sandbox.exec` public API remains stable.
