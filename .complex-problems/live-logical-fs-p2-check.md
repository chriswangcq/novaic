# Check: Boundary Exists And Is Active

## Summary

P002 is successful: the public `Sandbox.exec` path now routes through named LogicalFS, process-runner, and orchestrator components, while preserving the public API for later cleanup and tests.

## Criteria Map

- New components present and active: satisfied by R001.
- Process runner has no store/RO/RW authority: satisfied by `SandboxExec` role in R001.
- LogicalFS owns RW persistence and full view materialization: satisfied by `LocalMirrorLogicalFS` role in R001.
- Public `Sandbox.exec` delegates to orchestrator: satisfied by R001.
- Provider limitation explicit: satisfied by `LogicalFSCapabilities`.
- RW convention env vars exist: satisfied by R001.

## Execution Map

- Result IDs checked: R001.
- Evidence: py_compile passed; focused tests ran with only one known stale test failure assigned to P003.

## Stress Test

The check distinguishes component-boundary success from full migration success. It does not hide the old test failure; it explicitly assigns that cleanup to P003.

## Residual Risk

- The local mirror provider still uses an outer-command path adapter because the host lacks true mount support.
- Cleanup and verification tickets must still remove old behavior tests and prove no old active path remains.
