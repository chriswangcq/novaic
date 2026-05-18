# Direct session-ended delivery residue guard

## Problem Definition

After P341/P342, the direct session-ended delivery boundary should no longer contain generation-zero compatibility residue. This ticket verifies that boundary and removes any direct residue if found.

## Proposed Solution

Run targeted source guards over the direct delivery files:

- `task_queue/sagas/wake_finalize.py`
- `task_queue/handlers/session_handlers.py`
- `task_queue/client.py`
- `queue_service/routes.py`

Confirm there is no `session_generation or 0`, no handler `if generation is None`-only validation, no unguarded `generation: int` route schema, and no client path that calls `/api/queue/session-ended` before positive-generation validation.

## Acceptance Criteria

- Source guards pass for all direct delivery files.
- If any direct residue remains, remove it and re-run tests.
- Focused finalize tests still pass.

## Verification Plan

- Run targeted `rg` guards.
- Run `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr255_legacy_compat_cleanup.py`.

## Risks

- Guard regexes may be too broad; inspect matches before changing code.

## Assumptions

- Direct delivery files are exactly the files listed by P340.
