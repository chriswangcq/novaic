# P523 Wrapper Boundary Count Diagnosis

## Finding

The raw `require_outbox=True` occurrence count is stale. Current code has one after-transaction required-outbox path and explicit in-transaction `if not outbox_ids` guards for wake start and attach.

## Source Evidence

- `session_repo.py` has one `require_outbox=True` call for `_record_session_transition_after_transaction`.
- Wake start in-current-transaction path checks `if not outbox_ids` and raises `required session transition outbox effect was not recorded`.
- Attach path also checks `if not outbox_ids` after `_record_session_transition_in_current_transaction`.

## Decision

Update the test to assert the current ownership shape: one after-transaction wrapper flag plus at least two explicit required outbox runtime guards.
