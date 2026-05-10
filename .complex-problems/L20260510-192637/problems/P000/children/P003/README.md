# Scope Transition Log Remediation

## Problem

`scope_state_log_path` writes a local best-effort NDJSON file outside LogicalFS. It is observability, not canonical authority, but it is still persistent state outside the clean model.

## Success Criteria

- Decide whether to move transition history to SQLite, LogicalFS, or an observability sink.
- Preserve replay/debug value without creating a second semantic authority.
- Define cleanup for local NDJSON path and tests around transition recording failure behavior.
