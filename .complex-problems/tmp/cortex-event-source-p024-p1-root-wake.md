# Phase 3.2.1: Emit root and wake lifecycle events

## Problem

Root and wake scope lifecycle writes must emit ContextEvents for initialization and archive/finalize facts. The current code still creates scope files directly as the only authoritative record.

## Success Criteria

- The root/wake creation path emits `RootInitialized` and `WakeStarted` events.
- Root/wake archive/finalize emits `WakeArchived` when a wake is archived.
- Tests verify event log contents for root/wake lifecycle operations.
- Idempotency keys are stable for retry paths.
- Existing scope file artifacts remain only as transitional debug/projection output.
