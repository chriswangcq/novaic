# Session-ended delivery aggregate verification

## Problem Definition

P336 child fixes must be verified as one integrated session-ended delivery contract. The goal is to catch partial migration failures where individual functions are fixed but an old path still accepts malformed generation or valid delivery breaks.

## Proposed Solution

1. Run aggregate source guards across P336 delivery files and tests.
2. Run focused tests for:
   - wake-finalize payload builder.
   - session-ended handler/client/route.
   - repository finalize ownership.
   - inbox restart after valid session-ended.
   - legacy contract guard.
3. Record exact residual risks and whether they block P336 parent success.

## Acceptance Criteria

- Valid positive-generation session-ended delivery is still covered and passing.
- Missing/zero generation is rejected before accepted delivery.
- Direct delivery code has no fallback from missing generation to zero.
- Test suite evidence covers P341/P342/P343 as an integrated contract.
- Residual upstream react defaults are documented for P337/P339 and do not block P336.

## Verification Plan

- `python3 -m py_compile` for changed runtime modules.
- Focused pytest suite:
  - `tests/test_pr254_finalize_ownership.py`
  - `tests/test_pr255_legacy_compat_cleanup.py`
  - `tests/test_pr243_inbox_restart_cutover.py`
  - `tests/test_pr241_pending_inbox_projection.py`
  - `tests/test_pr251_wake_creation_outbox_cutover.py`
  - `tests/test_runtime_explicit_contracts.py`
- Source guards from P345/P346/P347.

## Risks

- Aggregate verification may reveal upstream react defaults are too risky to defer; if so, record not-success/follow-up rather than calling P336 done.

## Assumptions

- P344 is verification only unless a small missing guard is discovered.
