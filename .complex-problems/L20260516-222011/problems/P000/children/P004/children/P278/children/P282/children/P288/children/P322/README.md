# Audit active session read paths

## Problem

Map active session read/list APIs and confirm they derive from session_state SSOT instead of legacy active-session pointers or caches.

## Success Criteria

- Read/list methods and callers are listed with file references.
- Source of truth for each active session read is classified.
- Any read path using stale pointer/cache state is flagged.
