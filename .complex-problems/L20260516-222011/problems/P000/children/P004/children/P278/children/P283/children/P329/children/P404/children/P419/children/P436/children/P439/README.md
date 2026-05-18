# Context endpoint ownership and migration

## Problem

The context projection endpoints may still be useful, but only with explicit ownership. `/v1/context/read`, `/v1/context/append`, and `/v1/context/batch` must either be current intentional APIs or removed/migrated from runtime paths.

## Success Criteria

- Each context endpoint has an explicit owner and purpose: notification injection, debug API, tests, or removed legacy.
- Runtime bridge helpers are renamed, narrowed, or deleted if their names imply stale LLM history ownership.
- Live runtime code does not use compatibility context projection as the authoritative LLM context source.
- Focused runtime/Cortex tests pass after any cleanup.
