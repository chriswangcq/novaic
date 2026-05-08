# P003 Result - Cortex registry 显式依赖边界收口

## Done
- `WorkspaceRegistry.__init__()` now requires explicit `payload_blob_policy` and `clock`.
- Moved environment/time defaults into `build_workspace_registry()`, the production construction boundary.
- Updated `main_cortex.py` to use `build_workspace_registry()`.
- Added `tests/test_workspace_registry_dependencies.py` to guard constructor explicitness.

## Verification
- `python3 -m py_compile novaic_cortex/registry.py novaic_cortex/main_cortex.py tests/test_workspace_registry_dependencies.py`
- `pytest -q tests/test_workspace_registry_dependencies.py tests/test_workspace.py tests/test_workspace_limits.py tests/test_workspace_materialize.py tests/test_workspace_paths.py`

All targeted checks passed: 24 tests.

## Artifacts
- `novaic-cortex/novaic_cortex/registry.py`
- `novaic-cortex/novaic_cortex/main_cortex.py`
- `novaic-cortex/tests/test_workspace_registry_dependencies.py`

## Remaining Gaps
- `Workspace` itself still keeps default `clock or time.time`; that predates this ticket and is outside the registry-specific gap.
