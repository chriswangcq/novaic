# Audit Blob Workspace Boundary Tests and Guardrails

## Problem

Even if code/docs are clean, tests may not guard the desired boundary: Blob is file/artifact storage, Workspace/LogicalFS own live Cortex semantics.

## Success Criteria

- Identify existing tests or CI scans that prevent Blob-as-workspace authority regressions.
- Add or spawn follow-up for a targeted guardrail if the boundary is untested.
- Run focused tests/CI scans for any added guardrail.
