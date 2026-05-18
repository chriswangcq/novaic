# LogicalFS Materialization Residue Audit

## Problem

The codebase must distinguish intended LogicalFS provider materialization from legacy Cortex Workspace/direct local materialization. Any active Cortex-local materialization path would violate the service-boundary model.

## Success Criteria

- Scans materialization terms across Cortex, LogicalFS, sandbox service/core, and runtime where relevant.
- Classifies remaining `materialize` hits as intended lower-layer provider behavior, test naming, docs, or active legacy Cortex fallback.
- Removes or creates a follow-up for any active Cortex/direct workspace materialization residue.
