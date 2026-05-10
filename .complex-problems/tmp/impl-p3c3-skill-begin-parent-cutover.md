# Phase 3C3 Skill Begin Parent Selection SQLite Cutover

## Problem

`skill_begin` still chooses the parent scope by resolving the active path from file-walk state. It must choose the parent/top scope from SQLite active-stack projection so new child scopes attach under the operational control-plane authority.

## Success Criteria

- Successful `skill_begin` determines parent path from SQLite active-stack projection.
- Empty projection attaches the first child under the root path.
- Non-empty projection attaches the child under the top frame `scope_path`.
- Error branches preserve existing response shape.
- Tests prove begin parent selection still works after constructing a fresh Workspace/registry against the same operational SQLite database.
