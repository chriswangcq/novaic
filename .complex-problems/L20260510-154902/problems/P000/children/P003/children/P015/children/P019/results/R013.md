# Projection fold/stale result

## Summary

Completed P019 by closing fold rendering and stale sibling suppression child problems. The projector now folds closed skills, supports blank structural scopes, and suppresses stale open siblings.

## Done

- P020 / R011:
  - implemented scope-local buffers;
  - implemented non-empty fold rendering;
  - implemented blank structural close behavior;
  - tested nested structural folds.
- P021 / R012:
  - implemented stale open sibling suppression;
  - removed stale descendants from stack;
  - tested stale message invisibility and normal nested preservation.

## Verification

- P020 check `C012` succeeded.
- P021 check `C013` succeeded.
- Focused projection/substrate tests passed: 59 passed.

## Known Gaps

- Tool call/result placement remains open in P016.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`
