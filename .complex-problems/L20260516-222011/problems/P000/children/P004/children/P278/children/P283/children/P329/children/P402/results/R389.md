# Compatibility residue guard inventory result

## Summary

Completed a read-only compatibility-residue inventory for `P402`. The guard pass found no project migration-like files outside `.venv`, but it did surface runtime, Cortex, and test hits that need downstream classification/cleanup. No implementation files were changed.

## Done

- Ran a narrow live-default guard across runtime queue/task code and Cortex code.
- Ran an active lookup / active mutation / archive-restart guard across runtime and Cortex code.
- Ran a tests/fixtures compatibility guard across runtime and Cortex tests.
- Ran a migration-like file search twice; the first found only `.venv` dependency files, and the corrected no-venv search found zero project migration-like files.
- Saved guard outputs under `.complex-problems/L20260516-222011/tmp/p402-guards/`.

## Verification

- Guard output line counts:
  - `narrow-live-defaults.txt`: 38 lines.
  - `active-lookup-mutation.txt`: 220 lines.
  - `tests-compatibility.txt`: 68 lines.
  - `migration-files-no-venv.txt`: 0 lines.
- The largest runtime hit clusters are `session_repo.py`, `queue_db.py`, `saga_repo.py`, React contracts, session outbox, Cortex/session handlers, and task/health counters.
- The largest Cortex hit clusters are `api.py`, `active_stack_projection.py`, context event writer/projection, shell capabilities, and observability counters.
- Test hit clusters are mostly existing explicit-contract / legacy-removal / source-guard tests, but they still need a cleanup child to classify which tests are guard coverage versus stale compatibility encoding.

## Known Gaps

- Runtime hits are not fully classified in this inventory child. They are delegated to `P403`.
- Cortex hits are not fully classified in this inventory child. They are delegated to `P404`.
- Test/fixture compatibility hits are not fully classified in this inventory child. They are delegated to `P405`.
- Final aggregate source/test verification is delegated to `P406`.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p402-guards/narrow-live-defaults.txt`
- `.complex-problems/L20260516-222011/tmp/p402-guards/active-lookup-mutation.txt`
- `.complex-problems/L20260516-222011/tmp/p402-guards/tests-compatibility.txt`
- `.complex-problems/L20260516-222011/tmp/p402-guards/migration-files.txt`
- `.complex-problems/L20260516-222011/tmp/p402-guards/migration-files-no-venv.txt`
- `.complex-problems/L20260516-222011/tmp/p402-guards/migration-compatibility.txt`
