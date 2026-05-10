# Verify Stack Write Projection Completeness

## Problem Definition

Phase 3B added active-stack write helpers, begin/end writes, and finalize writes. Before Phase 3C cuts runtime reads over to SQLite, we need a strict write-only verification pass proving the write projection is complete and that no read path has been prematurely moved or left in a misleading half-state.

## Proposed Solution

Run a focused audit and verification pass:

- Run targeted tests covering active-stack helper, begin/end lifecycle writes, finalize writes, and operational-store persistence.
- Run static search for active-stack write helper call sites in live lifecycle paths.
- Run static search to confirm runtime read paths still use existing file-walk authority in this phase, so P019/P020 remain the explicit read-cutover owners.
- Run full Cortex tests.
- Record any remaining gap as Phase 3C/D scope, not hidden P025 success.

## Acceptance Criteria

- Targeted helper/begin-end/finalize/operational-store tests pass.
- Full Cortex tests pass.
- Static search shows live successful lifecycle write paths call active-stack projection/finalize helpers.
- Static search confirms runtime reads have not been cut over prematurely.
- Known gaps are explicitly limited to P019/P020 read cutover and file-walk quarantine.

## Verification Plan

- Use `rg` over `novaic-cortex/novaic_cortex/api.py` and active stack modules.
- Run targeted pytest files.
- Run full `novaic-cortex/tests`.

## Risks

- Static search can miss dynamic call paths; pair it with targeted behavior tests.
- P025 should not accidentally perform read cutover work; that belongs to later Phase 3C/3D tickets.

## Assumptions

- P022/P023/P024 are already closed and their tests remain in the suite.
