# Phase 2A Scope Transition Callsite And Semantics Audit

## Problem

Before changing hot lifecycle code, identify every scope transition writer/reader, the record shape expected by tests/API, and how it maps to `OperationalSqliteStore.scope_events`. This prevents changing the wrong layer or losing query semantics.

## Success Criteria

- List transition writers and readers with file/function pointers.
- Define the SQLite event payload shape for scope transitions.
- Identify which existing tests need updates.
- State whether NDJSON can be removed in Phase 2 or must be retained temporarily as projection/debug.
