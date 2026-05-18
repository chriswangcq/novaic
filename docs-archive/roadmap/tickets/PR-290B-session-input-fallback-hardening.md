# PR-290B — Session Input Fallback Hardening

Status: Closed

## Goal

Remove or classify input query/consumption fallbacks that can hide input loss.

## Closure Notes

- Removed fallback-to-empty behavior from unconsumed input event queries.
- Removed swallowed input-consumption write failures.
- These failures now propagate so dispatch/session restart cannot report success
  while losing input accounting.
- Verified with targeted input/wake/restart/recovery tests: 14 passed.
