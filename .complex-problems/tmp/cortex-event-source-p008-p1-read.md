# Phase 1.2.1: ContextEvent store path and read replay

## Problem

Implement the read side of the ContextEvent store: deterministic stream path ownership, empty read behavior, JSONL parsing, persisted row validation, and ordered replay of `ContextEvent` objects. This belongs under P008 because append/read storage must reject corrupt persisted state before later projections trust it.

## Success Criteria

- A `ContextEventStore` or equivalent module defines the event-log path for a root stream.
- Reading a missing event log returns an empty list.
- Reading a valid JSONL log returns ordered validated `ContextEvent` objects.
- Reading malformed JSON or invalid event envelopes raises a clear store/schema error.
- Tests cover empty read, valid ordered read, malformed JSON, invalid event row, and path construction.
