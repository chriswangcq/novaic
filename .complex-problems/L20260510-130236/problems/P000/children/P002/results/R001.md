# Cortex LogicalFS authority cutover result

## Summary

Implemented the in-process live file authority cutover for Cortex Workspace.
`Workspace` no longer directly manipulates `_store`; live `RO` / `RW`
normalization, store-key mapping, read/write/list/delete, append, move-tree, and
default layout initialization now live in `CortexLogicalFileAuthority`.
Runtime/API code that reached into `store` or `ws._store` was redirected through
Workspace system methods. A legacy empty skill-name compatibility behavior was
removed.

## Done

- Added `novaic-cortex/novaic_cortex/workspace_files.py`.
  - `logical_to_store_key()` owns path normalization and object-key mapping.
  - `CortexLogicalFileAuthority` owns file operations above `CortexStore`.
- Refactored `novaic-cortex/novaic_cortex/workspace.py`.
  - `Workspace` now constructs `self._files`.
  - System writes, public reads/writes, tree listing, directory listing,
    archive moves, context writes, active scope listing, and initialization go
    through `self._files`.
  - `_key` remains exported as a compatibility alias for path-validation tests,
    but its implementation lives in `workspace_files.py`.
- Refactored `novaic-cortex/novaic_cortex/runtime.py`.
  - `Cortex` can now be built around an existing `Workspace`.
  - Builtin tool schema seeding and skill installation use Workspace system file
    paths instead of direct store writes.
  - Empty skill names are rejected instead of creating `skills//`.
- Refactored `novaic-cortex/novaic_cortex/api.py`.
  - `_build_cortex()` no longer uses `ws._store`.
  - Admin scope-index rewrite uses `ws._sys_write()` instead of direct store
    access.
- Updated `novaic-cortex/tests/test_skill_install_limits.py` to assert the new
  non-empty skill-name contract.

## Verification

- Targeted Cortex tests passed:
  - `PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q tests/test_workspace.py tests/test_paths_adversarial.py tests/test_runtime.py tests/test_sandboxd_wiring.py tests/test_sandbox_requires_mount_namespace.py tests/test_skill_lifecycle.py tests/test_skill_install_limits.py`
  - Result: `43 passed`.
- Full Cortex test suite passed:
  - `PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q`
  - Result: `345 passed`.
- Residue scan for direct Workspace/API/runtime store access now only finds
  `_store` inside the new `workspace_files.py` authority plus test setup code
  and the transitional `BlobCortexStore` adapter.

## Known Gaps

- `BlobCortexStore` still exists as the transitional persistence adapter under
  the authority. P004 must add guardrails so it cannot be used as a live
  `RO` / `RW` authority outside the intended boundary.
- Registry comments and docs still mention `BlobCortexStore` as production
  backend; P004/P005 should update them to reflect the authority boundary.
- This is an in-process authority cutover. No separate LogicalFS HTTP service
  was introduced in this ticket.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace_files.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/runtime.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_skill_install_limits.py`
