# Update session outbox boundary source guards

## Problem

`test_pr281_session_outbox_wrapper_boundary.py` still asserts the older single wake outbox source shape. The current implementation uses a generic wrapper shape for outbox effect lists, so the test should guard the intended boundary without preserving stale source assumptions.

## Success Criteria

- The boundary test still rejects repository append/publish helper ownership and attach eager publish wrappers.
- The boundary test asserts the current generic outbox wrapper shape used by session transitions.
- The test remains strict enough to catch accidental reintroduction of repository-owned outbox publish wrappers.
