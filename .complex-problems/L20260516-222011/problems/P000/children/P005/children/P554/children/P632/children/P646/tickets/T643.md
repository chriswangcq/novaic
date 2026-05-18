# Audit Materialization Residue

## Problem Definition

`materialize` may mean intended LogicalFS provider behavior, but it may also indicate legacy Cortex Workspace/direct local filesystem fallback. We need to ensure active Cortex code no longer owns local materialization semantics outside the LogicalFS/sandbox boundary.

## Proposed Solution

Run targeted scans for `materialize`, `materialized`, and related method names across Cortex, LogicalFS, sandbox, and runtime packages. Inspect line context for active hits and classify them. Remove clearly stale Cortex Workspace/direct materialization residue if found; otherwise document intended lower-layer provider usage.

## Acceptance Criteria

- Scan output is recorded.
- Active materialization hits are classified by layer.
- No active Cortex Workspace/direct local materialization fallback remains unclassified.
- Any risky active residue is removed or converted into a follow-up.

## Verification Plan

Use `rg` and focused line-context reads. If code changes are needed, run the affected focused tests. If only classification is needed, record the classification artifact.

## Risks

- Over-removing LogicalFS provider materialization would break the intended sandbox mount implementation.
- Historical docs may mention old behavior; docs should be classified separately from runtime code.

## Assumptions

- LogicalFS provider materialization is allowed as lower-layer implementation detail.
- Cortex Workspace direct materialization is not allowed as an active path.
