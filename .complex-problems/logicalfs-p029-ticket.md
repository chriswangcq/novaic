# Migrate Remaining Workspace Tests

## Problem Definition

Remaining Cortex tests still instantiate `Workspace` with direct stores. They need to use the explicit LogicalFS-backed helper so tests do not preserve the old constructor.

## Proposed Solution

Search for direct Workspace constructor patterns in tests, migrate them to `make_workspace_with_store`, and run targeted tests that cover those files.

## Acceptance Criteria

- No direct live `Workspace(MemoryStore(), ...)` or `Workspace(store, ...)` constructor usage remains in migrated tests.
- Affected tests pass.
- Object-store-only tests remain untouched.

## Verification Plan

- Run `rg` for direct Workspace constructor patterns.
- Patch affected tests.
- Run targeted pytest files and residue scan.

## Risks

- Some fake registry tests instantiate Workspace inside helper classes; update them without changing test meaning.

## Assumptions

- `tests/workspace_test_utils.py` is the approved helper for live Workspace construction.
