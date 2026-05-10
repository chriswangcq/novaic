# Migrate tests off Cortex runtime lifecycle helpers

## Problem Definition

After removing `Cortex.scope_create` and `Cortex.scope_end`, existing tests still call those methods. These tests either need to use event-wired API lifecycle handlers or be rewritten as guard/obsolete behavior tests. The migration must not reintroduce compatibility shims or preserve runtime lifecycle bypasses.

## Proposed Solution

- Inventory all `.scope_create(` and `.scope_end(` usages under `tests/`.
- Split migration by test family:
  - archive/summary lifecycle invariants,
  - hooks/metrics tests that were coupled to runtime lifecycle helpers,
  - miscellaneous chaos/engine/compaction tests.
- For tests that still validate scope lifecycle behavior, create scopes and close them through `novaic_cortex.api.scope_create` / `scope_end` request handlers.
- For tests that only existed to validate obsolete runtime helper behavior, convert them to runtime façade guard tests or remove obsolete assertions.
- Run each migrated test family, then leave full-suite verification to the sibling static/full-verification problem.

## Acceptance Criteria

- No test calls `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Tests that still exercise lifecycle archival use event-wired API handlers.
- Hook/metric tests no longer depend on removed runtime lifecycle hooks.
- Focused migrated test files pass.

## Verification Plan

- Static scan:
  - `rg -n "\\.scope_create\\(|\\.scope_end\\(" tests`
- Run focused migrated files:
  - `tests/test_archive_invariants.py`
  - `tests/test_hooks_metrics.py`
  - `tests/test_hooks_limits.py`
  - `tests/test_wave4_metrics.py`
  - `tests/test_engine_wiring.py`
  - `tests/test_compaction_meta.py`
  - `tests/test_cortex_chaos.py`
  - `tests/test_pr74_scope_summary_contract.py`

## Risks

- Hook tests may be asserting behavior of obsolete lifecycle hooks rather than live agent-facing behavior; migration must avoid inventing fake coverage.
- API lifecycle helpers may require tenant/user/agent request setup instead of the old runtime convenience object.

## Assumptions

- It is acceptable to split this ticket further because the call sites span independent test families.
- Full-suite final verification belongs to P048 after P047 clears focused migrated tests.
