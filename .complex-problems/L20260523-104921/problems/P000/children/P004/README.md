# Remove Cortex and Entangled server SQLite fallback paths

## Problem

Cortex operational state and Entangled entity engine still expose SQLite as default or selectable server persistence. Migration scripts and comments also teach old SQLite operational stores as current.

## Success Criteria

- Cortex runtime entry point defaults to Postgres operational store and does not accept SQLite as a production fallback.
- Entangled runtime entry point defaults to Postgres and no longer launches from SQLite db-path in current startup examples.
- Old Cortex/Entangled SQLite migration CLIs are retired from current executable paths when no longer needed.
- Remaining SQLite code, if any, is limited to non-production tests or explicitly recorded as a follow-up with reason.
