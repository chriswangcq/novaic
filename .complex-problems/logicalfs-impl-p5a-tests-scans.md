# Final Tests And Residue Scans

## Problem

Run final targeted and feasible broader tests plus residue scans after all implementation and cleanup children have closed.

This child belongs under T015 because tests/scans should close independently from diff review and deployment reporting.

## Success Criteria

- Relevant Cortex, sandbox-service, Blob Service, common, and LogicalFS tests pass.
- A feasible broader suite passes, or any skipped broad check is explicitly justified.
- Residue scans for local fallback, live Blob bypass, and stale Blob Workspace wording are recorded.
