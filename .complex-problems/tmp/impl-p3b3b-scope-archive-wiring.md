# Phase 3B3B Scope Archive Finalize Wiring

## Problem

The scope archive/finalize path currently emits wake archived context data with a hard-coded empty remaining stack and does not route through a durable operational finalize helper. This means archive semantics can still lose live child-stack information or clear state without an explicit finalize event.

## Success Criteria

- Wire root/wake archive or finalize call sites through the Phase 3B3A active-stack finalize helper.
- Archive captures the actual current stack snapshot before clearing projection.
- Archive records explicit finalize reason and deterministic generation/idempotency key.
- Context wake archived event receives the same remaining stack snapshot where semantically relevant.
- Existing archive response behavior stays compatible.
