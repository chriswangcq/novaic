# Stale Cortex sandbox residue removed

## Summary

Removed the unused Cortex LogicalFS command-wrapping helpers and made the remaining direct runner default explicit as a library/test adapter. The active Cortex server path remains sandboxd-only through `main_cortex --sandboxd-url`.

## Done

- Removed `process_command` and `_mount_namespace_command` from `logical_fs.py`.
- Removed Cortex LogicalFS import of `build_bind_mount_command`.
- Added comments in `sandbox.py` and `api.py` naming the direct runner as library/test adapter only.
- Verified no command-wrapping residue remains in Cortex active source.

## Evidence

- `rg -n "build_bind_mount_command|process_command|_mount_namespace_command" novaic-cortex || true` -> no matches.
- `PYTHONPATH=novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` -> `3 passed in 0.22s`.

## Residual Risk

- `AsyncProcessRunner` remains by design in `novaic-common`; sandboxd uses it as the generic process substrate and tests can inject it explicitly.
