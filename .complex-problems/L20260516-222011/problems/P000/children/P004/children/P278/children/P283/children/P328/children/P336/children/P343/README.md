# Session-ended compatibility residue cleanup

## Problem

Legacy compatibility tests or code paths may still allow finalize/session-ended generation to be missing or zero. Those residues should be removed rather than supported because stale finalize must fail closed.

## Success Criteria

- Search finalize/session-ended delivery code and tests for `session_generation or 0`, `generation=0`, `Missing generation compatibility`, and equivalent fallback patterns.
- Remove or rewrite stale compatibility tests that bless zero generation.
- Keep any broader react-think/react-actions contract cleanup explicitly delegated to P337/P339 if outside the delivery boundary.
- Record a source-guard command that can be reused in the parent check.
