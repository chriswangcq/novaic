# Phase 5C.2 Current Cortex Docs Update

## Problem

Current Cortex docs still mention old runtime authority shapes such as `_walk_scope_tree` for uniqueness and `include_display` on step formatted reads. These docs must describe the current SQLite projection and explicit projection-mode contracts.

## Success Criteria

- Update current Cortex docs that describe scope lifecycle, internal API schemas, and state authority boundaries.
- Remove or rewrite `_walk_scope_tree` as runtime lookup/uniqueness authority; describe SQLite `scope_projection` and archive-only projection instead.
- Remove `include_display` from current `/v1/steps/read_formatted` schema docs; describe explicit `projection`.
- Preserve historical docs or mark them clearly historical when they are not current guidance.
- Static doc search no longer finds current-doc stale contract claims.
