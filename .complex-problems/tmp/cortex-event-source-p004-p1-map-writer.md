# Phase 3.1: Map write paths and introduce explicit ContextEvent writer

## Problem

Before changing live writes, Cortex needs a small boundary adapter that knows how to append ContextEvents with explicit clock/id dependencies, and a verified map of all direct source-of-truth write paths that must be cut over.

## Success Criteria

- Current write paths for root/wake init, notification append, context append/batch, steps write, skill begin/end, scope archive, and legacy projection files are mapped.
- A ContextEvent writer boundary exists and uses explicit clock/id providers.
- The writer is testable without hidden time/id/env inputs.
- No endpoint behavior is changed before the map and writer boundary are verified.
