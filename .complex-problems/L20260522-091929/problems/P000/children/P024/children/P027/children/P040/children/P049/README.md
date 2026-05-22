# Build Entangled Offline Migration Command

## Problem

Entangled needs an offline SQLite-to-Postgres migration command that can safely read the SQLite source, create or replace a clean Postgres target schema, copy dynamic entity rows and support tables, preserve stream ordering via `entangled_rowid`, reset identities, and produce a redacted report. This belongs under `P040` because staging validation cannot be meaningful until the migration command exists.

## Success Criteria

- A migration command or module exists under `Entangled/packages/server-python/scripts/` or an equivalent package path.
- The command opens the SQLite source in read-only mode and refuses ambiguous destructive Postgres target cleanup without an explicit clean-target flag.
- The command registers or creates Postgres schemas using the Entangled schema/DDL path rather than hand-written table-only shortcuts.
- Dynamic entity tables copy SQLite `rowid` into Postgres `entangled_rowid` wherever that column exists.
- `entangled_sync_versions` and `subagent_state_transitions` are migrated with exact key/value and count/max-ID preservation.
- Postgres identity sequences for dynamic IDs and transition IDs are reset above migrated maximum values.
- The command emits a structured migration report with redacted connection information, source counts, target counts, sequence reset evidence, semantic checks, and skipped tables with reasons.
- Focused unit tests cover planning, rowid copy, support-table migration, sequence reset SQL, report redaction, and refusal of unsafe target cleanup.
