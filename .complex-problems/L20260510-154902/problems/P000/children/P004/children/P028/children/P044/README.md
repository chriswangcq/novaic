# Phase 3.6.3: Add write-path event authority tests

## Problem

Individual endpoint tests verify event rows, but Phase 3 needs a consolidated authority test that proves root/wake, notifications, context append/batch, tool steps, and skill begin/end all leave ContextEvents as the write artifact.

## Success Criteria

- A focused test exercises the Phase 3 write path set and reads `context_events/events.jsonl`.
- The test asserts expected event types and key payload fields.
- The test does not rely on legacy `context.jsonl`, `steps/*.json`, or `summary.md` as authoritative evidence.
- Full Cortex suite passes.
