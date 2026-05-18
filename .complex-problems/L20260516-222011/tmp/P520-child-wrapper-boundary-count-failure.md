# Repair Session Repository Wrapper Boundary Count Failure

## Problem

`test_session_repository_no_longer_owns_outbox_append_publish_helpers` expects two `require_outbox=True` occurrences in `session_repo.py`, but current source has one.

## Success Criteria

- Determine whether the source or test expectation is stale.
- Apply minimal correct update.
- Rerun the failing test successfully.
