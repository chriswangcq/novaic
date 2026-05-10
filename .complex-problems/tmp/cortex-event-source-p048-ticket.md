# Verify runtime lifecycle bypass removal

## Problem Definition

After removing runtime lifecycle helpers and migrating tests, the repository needs a final audit proving no direct runtime structural lifecycle bypass or compatibility shim remains.

## Proposed Solution

- Run repo-wide static scans for:
  - runtime method definitions `def scope_create` / `def scope_end`,
  - runtime method call patterns `.scope_create(` / `.scope_end(`,
  - obsolete runtime lifecycle metric names `scopes_created` / `scopes_archived`.
- Confirm remaining `scope_create` / `scope_end` definitions are only event-wired API handlers.
- Run the full Cortex suite.
- Record any residual as a follow-up rather than hand-waving.

## Acceptance Criteria

- No runtime façade lifecycle helper definitions remain.
- No `.scope_create(` or `.scope_end(` call sites remain under active code/tests.
- Obsolete runtime lifecycle metric fields are gone.
- Full Cortex suite passes.

## Verification Plan

- `rg -n "def scope_(create|end)|\\.scope_create\\(|\\.scope_end\\(" novaic_cortex tests`
- `rg -n "scopes_created|scopes_archived" novaic_cortex tests`
- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`

## Risks

- API function definitions named `scope_create` and `scope_end` are expected and must be classified as event-wired, not runtime bypasses.
- Service-level Prometheus scope metrics are expected and distinct from runtime `CortexMetrics`.

## Assumptions

- This ticket performs verification and minimal cleanup only if a clear residue is found.
