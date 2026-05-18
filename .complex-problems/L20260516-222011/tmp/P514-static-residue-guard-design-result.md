# P514 Static Residue Guard Design Result

## Summary

Completed the static residue guard design for P281/P512. The guard scope, terms, scan command, and classification taxonomy are saved for final residue classification.

## Done

- Defined production scan scope: `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, and `novaic-agent-runtime/queue_service/fsm`.
- Defined test scan scope: `novaic-agent-runtime/tests`.
- Defined guard terms for active-session remnants, direct side-effect bypasses, imperative session branching, finalize/recovery ownership, and compatibility/backward paths.
- Saved a preview artifact using the corrected existing path set.

## Verification

- Guard design: `.complex-problems/L20260516-222011/tmp/p514/static-residue-guard-design.md`
- Preview artifact: `.complex-problems/L20260516-222011/tmp/p514/static-residue-guard-preview.txt`
- Corrected path issue: replaced nonexistent `novaic-agent-runtime/generic_fsm` with `novaic-agent-runtime/queue_service/fsm`.

## Known Gaps

- P514 does not classify final hits; P512 owns running and classifying the full scan.
