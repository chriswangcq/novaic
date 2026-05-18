# P521 Recovery Remaining Stack Diagnosis

## Finding

The production path intentionally records unknown remaining stack when a wake_finalize saga fails without explicit stack evidence.

## Source Evidence

- `queue_service/saga_repo.py::_explicit_or_unknown_remaining_stack` returns `{known: False, depth: 0, frames: []}` when context lacks a dict remaining_stack.
- `queue_service/saga_repo.py::_record_session_suspected_dead_event` persists that remaining_stack in the suspected-dead payload.
- `queue_service/session_recovery.py::build_recovery_archive_effect` copies recovery metadata remaining_stack to the archive effect.

## Decision

Update the test expectation from known true to known false; this aligns with explicit unknown diagnostics instead of fabricating a known empty stack.
