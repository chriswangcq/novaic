# Imperative dispatch cleanup final verification

## Problem

After P279 inventory and cleanup children close, the parent needs a final verification pass to prove no dangerous imperative dispatch or compatibility residue remains in production paths.

## Success Criteria

- Final guard artifacts are saved after all cleanup children finish.
- Production source has no unclassified direct saga creation, direct queue publish, stale fallback dispatch, or unsafe finalize/session compatibility residue.
- Test/docs guard fixtures are separated from production hits.
- Focused runtime/session tests pass.
- Any remaining ambiguous production hit is converted into a follow-up problem before parent success.
