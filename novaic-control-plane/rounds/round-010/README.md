# Round 010

## Objective
Upgrade from "format-compliant remote URLs" to "remote-operable proof":
- require real remote reachability evidence (`REACHABLE`, not all `SKIP_REMOTE`),
- require clean-clone replay paths without local sibling-repo assumptions.

## Team entrypoints
- Dispatch: `10-dispatch/`
- Reports: `20-reports/`
- Round feedback: `30-round-feedback/round-feedback.md`
- Redispatch: `40-redispatch/redispatch-plan.md`
- Close: `90-close/round-retro.md`

## Hard rule
- Parser-readable fields are source-of-truth.
- No evidence => cannot mark DONE.
