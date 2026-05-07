# PR-321 Physical Projection Residue Guard

Status: Closed
Owner: Codex
Phase: 8

## Goal

Make the physical task/saga projection deletion sticky, so future edits cannot
quietly reintroduce lifecycle columns or lifecycle writes on `tq_tasks` and
`tq_sagas`.

## Scope

- Add schema-level guards for the exact allowed projection-table columns.
- Add static source guards against projection lifecycle writes.
- Update Phase 8 ledger and ticket closure notes.

## Deletion Scope

- Remove obsolete quarantine wording that says lifecycle columns remain as
  compatibility projections.
- Remove old tests that assume projection lifecycle columns exist.

## Acceptance Criteria

- Tests fail if removed lifecycle columns reappear in schema.
- Tests fail if TaskQueue or SagaRepository write lifecycle fields to
  `tq_tasks` / `tq_sagas`.
- File 1 and all Phase 8 tickets are closed with verification notes.

## Verification

- Phase 8 targeted tests: `45 passed`.
- Full `novaic-agent-runtime`: `451 passed`.
- `novaic-business`: `176 passed`.
- `novaic-common` with runtime contracts: `140 passed`.
- `python -m compileall -q queue_service`.
- `git diff --check`.

## Closure Notes

- Added `tests/test_pr321_physical_projection_residue_guard.py` to assert exact
  physical column sets for `tq_tasks` and `tq_sagas`.
- Updated PR-307, PR-312, PR-315, and PR-318 guards so the accepted future state
  is physical deletion, not quarantined lifecycle projection compatibility.
- Updated PR-316 and PR-317 candidate cutover tests so they assert removed
  lifecycle columns are absent rather than mutating them.
