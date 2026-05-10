# Phase 3.3: Cut context append and batch writes to events

## Problem

`context.append` and `context.batch` currently write source context rows directly to legacy `context.jsonl`. They must append event facts first and leave any legacy file output as projection/debug only.

## Success Criteria

- `context.append` appends `ContextMessageAppended` events.
- `context.batch` appends one deterministic event per message or an explicitly modeled batch event if the event schema is extended.
- Tests verify event order, idempotency/retry behavior, and event payload shape.
- No old direct `context.jsonl` write remains as source-of-truth behavior.
