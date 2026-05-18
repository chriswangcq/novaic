# Final imperative dispatch residue cleanup

## Problem

The final guard classification may uncover high-confidence stale production residue or ambiguous dispatch/session compatibility branches. P483 needs a dedicated cleanup child so any source changes are scoped, testable, and not mixed into the inventory step.

## Success Criteria

- High-confidence stale production residue from the final classification is removed or tightened.
- Required adapter/outbox/FSM boundaries are retained and documented instead of deleted.
- Ambiguous production hits are split into follow-up problems if they cannot be safely fixed directly.
- Focused tests covering any changed source path pass.
- A diff artifact records exactly what changed, or explicitly states no source cleanup was needed after classification.
