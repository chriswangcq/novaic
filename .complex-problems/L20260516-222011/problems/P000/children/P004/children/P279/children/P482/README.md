# Finalize and session compatibility branch cleanup

## Problem

Finalize, session-ended, attach, and recovery paths are especially sensitive after the FSM migration. P279 needs old compatibility/fallback branches in these paths reviewed, and high-confidence stale branches removed or converted to explicit generation/FSM behavior.

## Success Criteria

- Finalize/session-ended/attach/recovery paths are scanned for legacy, compat, fallback, missing-generation, stale-generation, and direct mutation language.
- Retained branches are classified as active required path, guard/test fixture, or adapter boundary.
- High-confidence stale compatibility branches are removed or tightened.
- Ambiguous branches become child follow-up problems rather than speculative edits.
- Focused finalize/session runtime tests pass after any source change.
