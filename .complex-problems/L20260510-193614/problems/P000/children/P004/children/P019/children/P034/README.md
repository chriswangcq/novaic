# Phase 3C5 Runtime Read Cutover Verification Gate

## Problem

After status, begin, and end read paths are cut to SQLite, Phase 3C needs a strict gate proving live runtime control reads no longer depend on file-walk authority and that remaining file-walk usage is explicitly deferred to P020 quarantine.

## Success Criteria

- Targeted status/begin/end cutover tests pass.
- Fresh Workspace/registry tests prove runtime reads use persisted SQLite projection.
- Static search shows `context_status`, `skill_begin`, and `skill_end` no longer call `_collect_active_stack` or `resolve_active_scope_path` for control authority.
- Remaining file-walk stack usage is listed and assigned to P020 or non-runtime trace/debug surfaces.
- Full Cortex tests pass.
