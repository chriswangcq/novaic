# Rewrite Workspace and Authority Root Scratch Fixtures

## Problem Definition

`test_workspace.py`, `test_workspace_limits.py`, and `test_workspace_authority.py` still use `/rw/scratch` as a generic writable test path. That keeps root scratch visible as a preferred fixture even after the default layout was removed.

## Proposed Solution

Replace generic `/rw/scratch` fixture paths with neutral `/rw/tmp` or `/rw/public` paths while preserving each test's exact invariant. For tree-listing tests, avoid relying on an initialized `.keep` under scratch unless the test explicitly creates that directory.

## Acceptance Criteria

- The listed workspace/authority tests no longer use root `/rw/scratch`.
- Missing path, binary read/write, tree listing, append/read, and key mapping behavior remain covered.
- Focused tests pass.

## Verification Plan

Run post-change scans for `/rw/scratch` in the touched files and run `tests/test_workspace.py`, `tests/test_workspace_limits.py`, and `tests/test_workspace_authority.py` focused tests.

## Risks

- `read_tree_bytes` expectations may change if the old initialized `.keep` disappears.
- Key mapping tests should keep proving RW mapping without implying scratch canonicality.

## Assumptions

- `/rw/tmp` is acceptable as a neutral arbitrary writable Workspace path for non-shell tests.
