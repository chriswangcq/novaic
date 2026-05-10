# Old data reset and no-compat behavior

## Problem

Define and implement explicit no-compat behavior for legacy-only roots or missing ContextEvent logs. Old data may be deleted/reset; the system must not silently fall back to legacy DFS files.

## Success Criteria

- Missing/empty event logs in active prepare/status paths have explicit behavior.
- Legacy-only materialized roots do not silently produce LLM context through DFS.
- Tests cover reset/no-compat behavior.
