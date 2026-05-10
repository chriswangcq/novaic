# Phase 5D.2a Scope And Active Stack Guard Coverage

## Problem

Review and, if needed, tighten guard tests proving scope lookup uniqueness and active stack authority use SQLite projections instead of file walks or root metadata side indexes.

This belongs under P062 because scope/stack authority is a distinct high-risk removed path.

## Success Criteria

- Identify tests covering duplicate scope ID rejection through `scope_projection`.
- Identify tests covering active stack read/write/finalize through SQLite projection.
- Identify tests or static guards preventing reintroduction of `register_scope_id`, `get_scope_id_index`, `meta.scope_ids`, or `_walk_scope_tree` as runtime authority.
- Run the relevant tests or add missing guards.
