# Remove Gateway and Device server SQLite utilities

## Problem

Gateway and Device still contain SQLite backend defaults, gateway.db admin/migration scripts, and device local DB modules/comments. These paths make deleted gateway.db/device.db files look recoverable and supported.

## Success Criteria

- Gateway startup defaults to Postgres-only auth/config storage and rejects SQLite backend selection in current server runtime.
- Gateway SQLite migration/admin scripts are deleted from current executable paths or replaced with Postgres-only equivalents if still needed.
- Device local SQLite modules and comments that claim active SQLite ownership are deleted or rewritten to the Entangled/EntityStore current path.
- Focused Gateway/Device tests or imports pass after deletion.
