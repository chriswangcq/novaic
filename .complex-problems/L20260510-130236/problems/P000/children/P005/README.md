# Final verification, cleanup, and deployment readiness

## Problem

After implementation child problems close, run final verification and cleanup so
the branch is not left in a half-migrated state. This includes tests, residue
scans, ledger validation, and a clear deployment status.

## Success Criteria

- Targeted tests for LogicalFS, Cortex shell, sandboxd, Blob boundary, and guard
  scripts pass.
- Project-wide test command or nearest feasible suite passes, or any skipped
  check is explicit and non-blocking.
- Git diff review confirms business logic is smaller/clearer where relevant and
  no old fallback path remains active.
- Deployment scripts are ready and the final answer states whether deployment
  was run.
