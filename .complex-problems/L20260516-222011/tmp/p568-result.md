# Cortex Stable Path Compatibility Residue Classification

## Summary

P568 classified Cortex stable-path compatibility residue after inspecting stable `/cortex` constants, LogicalFS capability flags, sandbox rejection guards, schema tests, and sandboxd wiring tests. The current production path is a true stable `/cortex` mount path with explicit rejection of leaked `novaic-cortex-sandbox-*` backing paths; no production fallback path adapter was found.

## Done

- Scanned Cortex source and tests for stable path, temp backing path, adapter, mount, and blob-reference terms.
- Inspected `novaic-cortex/novaic_cortex/logical_fs.py` stable constants and capabilities:
  - `STABLE_CORTEX_ROOT=/cortex`
  - `STABLE_CORTEX_RO=/cortex/ro`
  - `STABLE_CORTEX_RW=/cortex/rw`
  - `outer_command_path_adapter=False`
  - sandboxd bind mount plan at `/cortex`
- Inspected `novaic-cortex/novaic_cortex/sandbox.py` and confirmed `novaic-cortex-sandbox-*` commands are rejected before execution with stable path guidance.
- Inspected `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` and `novaic-cortex/tests/test_sandboxd_wiring.py`; tests assert no local fallback, no command path adapter, stable `/cortex` env, and stable mount wiring.
- Inspected `novaic-cortex/tests/test_tool_schemas_limits.py`; `novaic-cortex-sandbox-*` appears in the shell tool description as a warning, not as a supported compatibility path.

## Verification

- Evidence artifacts:
  - `.complex-problems/L20260516-222011/tmp/p568/path-compat-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p568/path-compat-slices.txt`
- No code changes were made for P568.

## Known Gaps

- None for stable-path compatibility residue. The scan found intended guardrails, not active old compatibility branches.
- Blob payload references appeared in the broad scan but belong to sibling P563/P564 classification, not P568.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p568/path-compat-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p568/path-compat-slices.txt`
