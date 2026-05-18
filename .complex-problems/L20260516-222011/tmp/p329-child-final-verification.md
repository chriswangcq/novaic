# Compatibility residue final verification

## Problem

After runtime, Cortex, and test/migration cleanup, the project needs an aggregate verification pass proving missing/stale generation compatibility residue is gone or fully classified.

## Success Criteria

- Rerun the full source guard matrix after all cleanup children are complete.
- Rerun focused runtime and Cortex test suites relevant to attach/finalize/session-ended/recovery/archive behavior.
- Provide a final matrix classifying every remaining hit as safe validator/test/counter/projection/generic infrastructure or fixed residue.
- Confirm attach/finalize/session-ended paths no longer accept missing/stale generation silently.
- Create a follow-up child if any unclassified or dangerous compatibility residue remains.
