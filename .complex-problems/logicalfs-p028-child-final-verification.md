# Full Cutover Verification And Residue Scan

## Problem

After migrating tests, the suite and scans must prove there is no unconnected new code, hidden compatibility branch, or stale active test path. This belongs under P028 because successful test migration must be verified as a whole.

## Success Criteria

- Full Cortex test suite passes.
- LogicalFS and sandbox-service targeted suites still pass.
- Residue scans show no old direct live constructor patterns in Cortex source/tests.
- Shell/sandbox RO/RW wiring tests pass.
- Any remaining old store modules are classified for P024 cleanup rather than silently accepted.
