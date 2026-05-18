# Cortex compatibility final verification

## Problem

After Cortex inventory, lifecycle, archive/diagnostic, and API/bridge cleanup children are complete, a final pass must prove no unclassified live Cortex compatibility residue remains.

## Success Criteria

- Rerun Cortex-specific narrow and widened guards.
- Rerun focused Cortex tests for all changed boundaries.
- Produce a final matrix classifying every remaining Cortex hit.
- Confirm no live Cortex path accepts missing/stale generation or revives old active-state lookup.
- Create a follow-up if any dangerous or unclassified Cortex hit remains.
