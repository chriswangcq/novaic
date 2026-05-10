# Projection scope/fold result

## Summary

Completed P015 by closing stack/LIFO behavior and fold/stale behavior. The pure projector now handles skill open/close lifecycle, fold rendering, structural blank scopes, nested folds, and stale sibling suppression.

## Done

- P18 / R010:
  - skill open stack frames;
  - nested stack order;
  - valid close pop;
  - non-LIFO close rejection.
- P019 / R013:
  - closed-scope fold rendering;
  - blank structural close behavior;
  - nested folds;
  - stale open sibling and descendant suppression.

## Verification

- P018 check `C011` succeeded.
- P019 check `C014` succeeded.
- Focused projection/substrate tests passed: 59 passed.

## Known Gaps

- Tool call/result placement remains open in P016.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`
