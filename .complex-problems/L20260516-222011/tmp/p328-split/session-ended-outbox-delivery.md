# Session-ended outbox delivery generation contract

## Problem

Session-ended/finalize side effects crossing the outbox boundary must carry enough explicit generation identity for downstream workers. Missing generation should fail closed rather than causing downstream handlers to infer from current active state.

## Success Criteria

- Map session-ended/finalize outbox effect builders, payload schemas, and delivery handlers.
- Verify payloads include expected saga/scope/generation and finalize reason where required.
- Ensure missing expected generation or scope is rejected before publish/delivery.
- Add tests proving outbox delivery preserves generation identity and rejects malformed finalize/session-ended effects.
- Remove stale compat behavior that silently fills missing generation from current state.

## Belongs Under

This is the durable side-effect boundary for T324/P328; it prevents stale finalize events from becoming ambiguous worker tasks.
