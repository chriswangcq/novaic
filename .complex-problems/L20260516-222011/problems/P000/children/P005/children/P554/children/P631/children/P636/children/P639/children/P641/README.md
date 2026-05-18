# Workspace and Authority RW Fixture Rewrite

## Problem

Workspace and authority tests use `/rw/scratch` as generic writable paths. These should be neutral current paths while preserving write/read/tree/key-mapping invariants.

## Success Criteria

- Updates `test_workspace.py`, `test_workspace_limits.py`, and `test_workspace_authority.py` root scratch fixtures.
- Preserves missing path, binary IO, tree listing, append/read, and key mapping assertions.
- Runs focused tests for touched files.
