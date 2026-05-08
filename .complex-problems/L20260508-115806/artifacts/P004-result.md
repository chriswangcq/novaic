# P004 Result - Docs Status Consistency Lint

## Summary

Docs status drift is fixed and guarded. The known PR-338 stale `Status: Doing` / `P007 in progress` wording was corrected, and a CI lint now checks roadmap ticket status against the architecture plan markers.

## Done

- Updated `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md` from `Status: Doing` to `Status: Closed`.
- Updated PR-338 current closure state from `P007 in progress` to `P007 closed`.
- Added `scripts/ci/lint_docs_status_consistency.py`.
- Wired the new lint into `.github/workflows/lint.yml`.

## Verification

- `python3 scripts/ci/lint_docs_status_consistency.py` -> pass.
- `./scripts/ci/lint_current_docs_residue.sh` -> pass.
- `python3 scripts/ci/lint_roadmap_ticket_archaeology.py` -> pass.
- `rg -n "Status: Doing|P007 in progress" docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md docs/architecture/generic-worker-substrate-plan.md` -> no matches.

## Known Gaps

- none for P004.

## Artifacts

- `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md`
- `scripts/ci/lint_docs_status_consistency.py`
- `.github/workflows/lint.yml`
