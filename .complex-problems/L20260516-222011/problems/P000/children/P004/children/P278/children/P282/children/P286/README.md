# Problem: Session schema table inventory

## Problem

Inspect Queue Service schema definitions and migrations for session-related tables and indexes so the state ownership audit starts from actual persisted structures.

## Success Criteria

- List every session-related table/index found with file references.
- Explain each table's intended role from schema and nearby code names.
- Identify whether `tq_active_sessions` exists as a table, view, or absent artifact.
