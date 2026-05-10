# Refactor Workspace Constructor To LogicalFS Authority

## Problem Definition

`Workspace.__init__` currently accepts a `CortexStore` and creates `CortexLogicalFileAuthority`. This keeps live file authority inside Cortex and prevents `Workspace` from being a semantic client of LogicalFS.

## Proposed Solution

Change `Workspace` to accept a LogicalFS authority object directly. Replace direct imports of `CortexStore`, `CortexLogicalFileAuthority`, and `logical_to_store_key` with the generic LogicalFS authority interface and Cortex-side validation helper. Update Workspace tests through a small test helper that builds a LogicalFS authority from `MemoryStore`.

## Acceptance Criteria

- `workspace.py` no longer imports `CortexStore`, `CortexLogicalFileAuthority`, or `logical_to_store_key`.
- `Workspace.__init__` stores a passed LogicalFS authority object.
- `Workspace.list_dir` maps LogicalFS entries into `FileEntry`.
- `Workspace.initialize` writes default layout through explicit logical directories.
- Targeted Workspace tests pass after using an explicit helper.

## Verification Plan

- Update Workspace code and targeted tests.
- Run Workspace-related tests.
- Run scans for old authority/store imports in `workspace.py`.

## Risks

- Existing tests may still call the old constructor and fail until migrated.
- Runtime/registry will still need P027 cutover after this constructor change.

## Assumptions

- The LogicalFS authority object supports the methods added in P021.
