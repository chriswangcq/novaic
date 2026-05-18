# PR-335 Worker Residue Guards

Status: Closed
Phase: 6
Owner: Codex

## Goal

Prevent future reintroduction of bespoke worker lifecycle loops and hidden
dependency reads.

## Scope

- Add static tests or grep guards for migrated worker paths.
- Guard against handlers directly mutating lifecycle state tables.
- Document allowed exceptions if any remain.

## Deletion Target

- Stale comments/examples that teach old worker loops.
- Temporary migration names after cutover.

## Acceptance

- Tests fail if migrated workers reintroduce manual lifecycle loops.
- Residual exceptions are documented with owner/removal condition or removed.

## Verification

- Residue guard tests.
- Full runtime test suite.

## Closure Notes

Added residue guard tests that fail if migrated workers reintroduce bespoke
`while self._running` loops, saga thread bookkeeping, or old `_claim_*`
lifecycle methods. Also guards that sync worker entrypoints use the shared
process runner.

Follow-up cleanup tightened the same guard against physical residue:
retired standalone worker entrypoints (`main_task.py`, `main_saga.py`), module
`start_worker` helpers, worker-side `gateway_url` compatibility plumbing,
obsolete app-script `watchdog` mode, and stale packaging hidden imports.

Verification:

```bash
pytest -q tests/test_pr335_worker_residue_guards.py
```
