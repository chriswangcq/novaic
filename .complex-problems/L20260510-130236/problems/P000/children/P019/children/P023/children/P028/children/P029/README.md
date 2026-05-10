# Migrate Remaining Workspace Constructor Tests

## Problem

Tests outside `test_workspace.py` still create `Workspace(MemoryStore(), ...)` directly. This either fails after constructor cutover or encourages restoring a compatibility constructor. This belongs under P028 because test migration must enforce the new authority boundary.

## Success Criteria

- All live Workspace construction tests use explicit LogicalFS-backed helpers.
- No `Workspace(MemoryStore(), ...)` or `Workspace(store, ...)` live-constructor pattern remains outside object-store-only tests.
- Targeted Workspace/API/sandbox tests using direct Workspace construction pass.
