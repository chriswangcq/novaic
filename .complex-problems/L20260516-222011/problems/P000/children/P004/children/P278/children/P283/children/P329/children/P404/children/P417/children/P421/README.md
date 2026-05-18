# ContextEvent store and writer contract audit

## Problem

ContextEvent append boundaries must be deterministic and explicit. Store/writer code may still hide implicit dependencies or compatibility behavior in idempotency, payload construction, or append defaults.

## Success Criteria

- Inspect `context_event_store.py`, `context_event_writer.py`, and `context_events.py`.
- Confirm append contracts use explicit clock/id providers and explicit event payloads.
- Remove or patch any hidden default that weakens event identity, event type, idempotency, or actor semantics.
- Add focused tests if behavior changes.
- Run store/writer/model tests.
