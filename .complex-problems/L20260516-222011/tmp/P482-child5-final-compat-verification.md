# Final finalize/session compatibility verification

## Problem

After inventory and targeted cleanup, P482 needs a final skeptical verification pass that no actionable finalize/session compatibility residue remains. This belongs under P482 because deletion work can leave tests green while old inactive paths still confuse future AI/code maintenance.

## Success Criteria

- Final guard search artifact is saved and compared against the initial inventory.
- Remaining hits are classified with exact file references and no unclassified production residue.
- Focused finalize/session/attach/recovery tests pass together.
- Any remaining gap becomes a follow-up problem instead of being hidden in the parent result.
