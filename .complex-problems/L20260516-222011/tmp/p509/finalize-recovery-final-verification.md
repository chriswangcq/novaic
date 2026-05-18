# P509 Finalize Recovery Final Verification

## Guard Classification

The final guard still finds finalize/recovery vocabulary because these are live required paths:

- `wake_finalize.py` constructs `CORTEX_SCOPE_END` and `SESSION_ENDED` tasks with required `remaining_stack`.
- `session_handlers.py` and `cortex_handlers.py` validate `remaining_stack`.
- `session_repo.py` owns the session ledger transition for `session_ended`.
- `session_outbox.py` owns `RECOVERY_ARCHIVE_SCOPE -> CORTEX_SCOPE_END` publishing.
- `saga_repo.py` owns wake-finalize compensation and suspected-dead event recording.
- `session_recovery.py` owns pure recovery marker/archive effect shaping.
- `cortex_bridge.py` remains a generic bridge client; active task handlers supply strict fields.

No unclassified ownership bypass was found.

## Tests

`finalize-recovery-final-tests.log` reports `62 passed in 0.40s`.

## P280 Criteria Mapping

- Map finalize/recovery code paths: P507 map artifact.
- Confirm ownership or identify gaps: P507/P508 concluded ownership is explicit and no source remediation is needed.
- Add/fix tests if active gap appears: no active gap appeared; existing focused tests passed.
