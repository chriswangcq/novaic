# Runtime cleanup final verification

## Problem

After runtime session-authority, generic Queue infrastructure, task contracts, and worker counter children are complete, a final runtime verification pass must prove no unclassified runtime compatibility residue remains.

## Success Criteria

- Rerun runtime-specific narrow and widened guards after all runtime cleanup children are complete.
- Rerun focused runtime tests relevant to any changed boundaries.
- Produce a final runtime matrix classifying every remaining hit.
- Confirm no attach/finalize/session-ended runtime path accepts missing/stale generation silently.
- Create a follow-up if any dangerous or unclassified runtime hit remains.
