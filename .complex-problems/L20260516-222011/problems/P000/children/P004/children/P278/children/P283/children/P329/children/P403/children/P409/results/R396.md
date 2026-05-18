# Task contracts and handler residue cleanup result

## Summary

Completed the task contracts and handler residue cleanup through split children. React contracts, finalize/session handlers, Cortex handler/bridge, and final task-handler verification are all checked successful. No dangerous task-level session-generation fallback remains.

## Done

- `P412` / `R392` / `C418`: React contracts require explicit positive `session_generation`; round/retry/stack-depth defaults are loop counters.
- `P413` / `R393` / `C419`: finalize sagas and session handler require explicit positive generation, finalize reason, and remaining stack.
- `P414` / `R394` / `C420`: Cortex handler/bridge validates session generation and classifies round/counter metadata.
- `P415` / `R395` / `C421`: final task/handler guard mapped all remaining hits to child classifications and focused tests.

## Verification

- React contract focused tests: `16 passed`.
- Finalize/session handler focused tests: `48 passed`.
- Cortex handler/bridge runtime tests: `20 passed`; Cortex focused tests: `20 passed`.
- Final task/handler aggregate runtime tests: `57 passed`.
- Guard artifacts:
  - `.complex-problems/L20260516-222011/tmp/p412/react-contract-guard.txt`
  - `.complex-problems/L20260516-222011/tmp/p413/finalize-session-handler-guard.txt`
  - `.complex-problems/L20260516-222011/tmp/p414/cortex-handler-bridge-guard.txt`
  - `.complex-problems/L20260516-222011/tmp/p415/final-task-handler-guard.txt`

## Known Gaps

- None for P409's task contract/handler scope.

## Artifacts

- Child results/checks: `R392`/`C418`, `R393`/`C419`, `R394`/`C420`, `R395`/`C421`.
