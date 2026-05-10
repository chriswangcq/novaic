# File-Walk Helper Deletion And Guard Rails

## Problem

After the individual runtime paths are cut over, `_collect_active_stack(...)` and ambiguous `resolve_active_scope_path(...)` references must not remain as quiet legacy authority. Residual helper code creates maintenance risk: future changes may accidentally call the old path again.

This belongs under Phase 3D because it is the final quarantine/deletion gate for the file-walk stack authority residue.

## Success Criteria

- `_collect_active_stack(...)` is deleted, or renamed to an explicit repair/debug-only helper with no live API references.
- Static guards fail if `_collect_active_stack` appears in live `context_status`, `skill_begin`, `skill_end`, `scope_end`, `scope_write_assistant`, or `steps_write` authority paths.
- Remaining `resolve_active_scope_path(...)` usage, if any, is documented and tested as non-stack repair/debug behavior; otherwise it is removed from `api.py`.
- Old tests that assert file-walk active-stack authority are rewritten or deleted.
- Targeted tests and the full Cortex test suite pass.
