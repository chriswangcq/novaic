# Tool shell boundary Phase 0 implementation

## Problem

Start construction of the unified tool shell boundary migration with Phase 0: baseline freeze, tool surface inventory, and guardrails. The goal is to prevent future phases from adding new shell-capability code while leaving old harness-level tools invisible or unclassified.

Current target from the construction plan:

- Final harness tools: `shell`, `display`, `skill_begin`, `skill_end`, `sleep`.
- Existing direct environment/interface tools must be explicitly classified for migration/removal, not left as ambiguous runtime executors.
- Phase 0 should not delete runtime functionality yet; it should create executable inventory/guard tests and clear target classifications.

## Success Criteria

- Add a code-level inventory/classification of current Runtime tool executors.
- Add tests proving every current `_EXECUTORS` key is classified.
- Add tests documenting final harness primitives and tools that must migrate behind shell.
- Add a guard that catches accidental new direct harness tools without classification.
- Do not remove existing tool functionality in Phase 0.
- Keep changes scoped and compatible with existing dirty worktree changes.
