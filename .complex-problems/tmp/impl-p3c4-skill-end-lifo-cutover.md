# Phase 3C4 Skill End LIFO SQLite Cutover

## Problem

`skill_end` still validates stack-empty and mismatch cases by resolving active scope from file-walk state. It must validate current top scope from SQLite active-stack projection and preserve structured error semantics.

## Success Criteria

- `skill_end` empty-stack detection reads SQLite active-stack projection.
- `skill_end` mismatch detection compares requested id with SQLite top scope id.
- Successful `skill_end` uses SQLite top frame path as the child path to close.
- Existing error fields (`error_code`, `requested_scope_id`, `actual_stack_top`, `stack`, `stack_depth`) remain compatible.
- Tests cover stack-empty, wrong-scope close, and successful close.
