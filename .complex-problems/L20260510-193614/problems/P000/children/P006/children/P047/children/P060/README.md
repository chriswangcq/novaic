# Phase 5C.4 Documentation Residue Final Static Gate

## Problem

After doc/comment edits, we need a final static audit to prove current docs/comments do not still advertise stale authority paths. Remaining hits must be classified as historical or intentional guard language.

## Success Criteria

- Run final static searches for stale current-contract terms.
- Record a classification table for all remaining hits.
- Current docs/comments have no unowned mentions of temp sandbox backing paths, in-process locks as authority, file-walk authority, `_walk_scope_tree`, `format_for_llm`, or `include_display` in step formatting.
- Any remaining matches are historical docs, schema migration internals, negative guard tests, or low-level `resolve_for_llm` behavior.
