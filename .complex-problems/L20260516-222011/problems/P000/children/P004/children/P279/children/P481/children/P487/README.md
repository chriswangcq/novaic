# Direct side-effect bypass final verification

## Problem

After P481 call-site classification and boundary decisions, a final verification pass must prove no unclassified or dangerous direct side-effect bypass remains.

## Success Criteria

- Final guard artifacts are saved.
- Production side-effect call sites are either classified required boundaries or removed.
- Test/docs fixture hits are separated from production hits.
- Focused side-effect/session outbox tests pass.
- Any remaining ambiguous call site becomes a follow-up problem before P481 success.
