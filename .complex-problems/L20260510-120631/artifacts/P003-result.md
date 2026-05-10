# Result: Shell Execution Path Verified Through LogicalFS And Sandboxd

## Summary

Strengthened the active shell execution tests so they prove the current path is Cortex adapter -> LogicalFS view -> sandboxd SDK spec -> runner -> LogicalFS patch -> Workspace.

## Done

- Added a sandboxd wiring test where the fake runner inspects the mounted source root while the LogicalFS view is alive.
- The test verifies materialized RO content, RW content, and injected capability scripts exist under the mount source.
- The fake runner mutates RW files and `Sandbox.exec` persists those changes back to Workspace through the LogicalFS patch path.
- Verified no local subprocess fallback calls remain in `novaic_cortex.sandbox`.

## Verification

- `PYTHONPATH=novaic-logicalfs:novaic-sandbox-sdk:novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` passed: 4 tests.
- Full Cortex non-real-shell suite passed: 345 passed, 40 skipped.
- Fallback scan found no `create_subprocess`, `subprocess`, `Popen`, `os.system`, `wait_for`, command rewriting, or unshare execution path in active sandbox/logical_fs code.

## Residual Risk

- Real sandboxd live smoke still belongs to P004 deploy/verification.
- Real-shell tests are still skipped unless explicitly enabled; P003 only proves the active Python boundary and Workspace patch loop.
