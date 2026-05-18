# Final imperative dispatch guard classification

## Problem

P483 needs a fresh, saved guard sweep after all previous cleanup children. Without a final classification artifact, the parent cannot prove whether remaining direct dispatch, fallback, compatibility, or finalize/session hits are production residue or intentional guard/test references.

## Success Criteria

- Saved raw guard output covers direct saga creation, direct queue publish, legacy/fallback/compat dispatch terms, active-session pointer usage, attach generation bypasses, and finalize/session-ended compatibility terms.
- Every production hit is classified with a concrete file/path reference.
- Test/docs guard hits are separated from production hits.
- Any production hit that cannot be confidently classified is recorded as a follow-up candidate for the next child.
- No production code is changed in this inventory/classification child.
