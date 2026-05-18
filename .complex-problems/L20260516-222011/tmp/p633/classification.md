# Workspace Materialize Reference Classification

## Scan Commands

Recorded in `.complex-problems/L20260516-222011/tmp/p633/materialize-scan.txt`:

- `rg -n "Workspace\.materialize|def materialize|\.materialize\(|materialize\(" novaic-cortex || true`
- `rg -n "materialize" novaic-cortex || true`

## Stale Workspace API Hits

- `novaic-cortex/novaic_cortex/workspace.py:838-852`
  - Classification: removable stale Workspace API.
  - Reason: `Workspace.materialize()` writes external bytes directly to global `/rw/scratch/{filename}`. It is exactly the direct materialization/root scratch contract called out by P562/P553.

## Test-Only Stale Contract Hits

- `novaic-cortex/tests/test_workspace_materialize.py:1-40`
  - Classification: test-only dependency on stale API.
  - Reason: tests assert `/rw/scratch/image.png`, argument rejection, and filename validation for `ws.materialize()`. These protect the old contract rather than current LogicalFS/sandboxd behavior.

## Intended LogicalFS Materialization Hits

- `novaic-cortex/novaic_cortex/logical_fs.py:320`
  - Classification: intended LogicalFS substrate materialization.
  - Reason: `self._provider.materialize(...)` materializes a bounded LogicalFS snapshot for sandboxd process execution. This belongs to the intended `Workspace -> LogicalFS -> sandboxd` boundary and should not be deleted for P634.

## Unrelated / Terminology Hits

- `workspace.py` context projection docstrings/methods around `read_context`, `append_context_projection`, and `append_context_batch_projection` use "materialized context projection" terminology.
  - Classification: unrelated to `Workspace.materialize()` file-byte API; do not edit for P634 unless separately addressed by context projection work.
- `api.py` comments/docstrings around context projection and active stack use "materialized" terminology.
  - Classification: unrelated documentation/diagnostic projection wording; not part of P634.
- Tests named `test_sandbox_materializes_*` and context append materialization tests.
  - Classification: intended current behavior tests for LogicalFS/context projections, not stale `Workspace.materialize()` API.

## P634 Implementation Targets

- Remove `Workspace.materialize()` from `novaic-cortex/novaic_cortex/workspace.py`.
- Delete or rewrite `novaic-cortex/tests/test_workspace_materialize.py`; likely delete if no current behavior remains to preserve.
- Keep `novaic-cortex/novaic_cortex/logical_fs.py` provider materialization untouched.
- Do not edit context projection methods/docstrings as part of P634.
