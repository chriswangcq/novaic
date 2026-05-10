# Workspace Authority Constructor Result

## Summary

Refactored `Workspace` so its live file dependency is a passed LogicalFS authority object rather than a direct `CortexStore`. Added a test helper that builds a Workspace via `build_workspace_file_authority`.

## Done

- Updated `novaic-cortex/novaic_cortex/workspace.py`:
  - removed `CortexStore`, `CortexLogicalFileAuthority`, and `logical_to_store_key` imports;
  - constructor now accepts `file_authority`;
  - agent id validation uses `validate_agent_id`;
  - `list_dir` maps LogicalFS directory entries to Cortex `FileEntry`;
  - `list_active_scopes` uses authority `key` / `list_object_keys`;
  - `initialize` writes default logical directories via `initialize_layout`.
- Added `novaic-cortex/tests/workspace_test_utils.py` with `make_workspace_with_store`.
- Migrated `novaic-cortex/tests/test_workspace.py` to use the explicit authority-backed helper.

## Verification

- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q tests/test_workspace.py tests/test_workspace_authority.py`
  - Result: `16 passed in 0.09s`.
- `rg -n "CortexStore|CortexLogicalFileAuthority|logical_to_store_key|workspace_files" novaic-cortex/novaic_cortex/workspace.py || true`
  - Result: no hits.
- `rg -n "Workspace\\(MemoryStore|Workspace\\(store|CortexLogicalFileAuthority" novaic-cortex/tests/test_workspace.py novaic-cortex/tests/workspace_test_utils.py novaic-cortex/novaic_cortex/workspace.py || true`
  - Result: no hits.

## Known Gaps

- Runtime and registry still need to construct/pass the authority to Workspace; P027 covers that.
- Many non-Workspace tests still use old direct constructors; P028 covers the broader migration.
- `novaic-cortex/novaic_cortex/workspace_files.py` still exists until cleanup P024.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/workspace_test_utils.py`
- `novaic-cortex/tests/test_workspace.py`
