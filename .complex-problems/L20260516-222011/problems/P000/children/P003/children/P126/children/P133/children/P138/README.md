# ContextEvent append-only store map

## Problem

`ContextEventStore` defines where the event stream lives and how events are appended/read. Its invariants and explicit dependency boundaries must be verified before trusting it as the context source of truth.

## Success Criteria

- Store path, read behavior, append idempotency, sequence assignment, and explicit clock/id provider requirements are documented with source pointers.
- Store tests are identified and run.
- Any hidden input or stale fallback in the store layer is fixed or split into a follow-up.
