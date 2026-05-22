# Port Session State Locking And Transition Semantics To Postgres

## Problem

Session dispatch, attach, finalize, and restart decisions still depend on SQLite-era process serialization. Under Postgres, first dispatch of a missing session row, concurrent dispatches for the same `session_key`, and finalize-vs-attach races need an explicit session serialization boundary so inputs are durable and only one active session can be selected.

## Success Criteria

- First dispatch ensures `tq_session_state(session_key)` exists before decisions that inspect active session state.
- Postgres dispatch and finalize paths lock the relevant session state row, or use an equivalent compare/update pattern, before deciding start, attach, buffer, close, or restart.
- Attach revalidates `active_saga_id`, `active_scope_id`, and generation under the same session serialization boundary before consuming an input.
- Finalize leaves pending inputs unconsumed and restartable when an active session ends with queued input.
- Focused Postgres-path tests cover first-dispatch races, attach revalidation, finalize revalidation, and no-input-loss behavior.
- SQLite-specific synchronization remains isolated to the SQLite adapter or legacy test path, not the session business logic.
