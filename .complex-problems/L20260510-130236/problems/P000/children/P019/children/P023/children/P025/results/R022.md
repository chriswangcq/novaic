# Cortex LogicalFS Authority Factory Result

## Summary

Added a Cortex-side factory for creating LogicalFS workspace authorities from an object store and explicit agent id. The helper maps `agent_id` to `agents/{agent_id}` and returns `StoreBackedLogicalFileAuthority` without importing or using `CortexLogicalFileAuthority`.

## Done

- Added `novaic-cortex/novaic_cortex/workspace_authority.py`.
- Added `validate_agent_id`, `agent_owner_prefix`, and `build_workspace_file_authority`.
- Added `novaic-cortex/tests/test_workspace_authority.py`.

## Verification

- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q tests/test_workspace_authority.py`
  - Result: `7 passed in 0.15s`.
- `rg -n "CortexLogicalFileAuthority" novaic_cortex/workspace_authority.py tests/test_workspace_authority.py || true`
  - Result: no hits.

## Known Gaps

- `Workspace.__init__` still uses the old direct constructor; P026 closes that.
- Registry/runtime are not yet wired through the helper; P027 closes that.
- Tests still mostly use the old `Workspace(MemoryStore(), ...)` and `Cortex(MemoryStore(), ...)` paths; P028 closes that.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace_authority.py`
- `novaic-cortex/tests/test_workspace_authority.py`
