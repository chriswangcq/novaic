# Code repair check

## Summary

The code repair problem is solved at the implementation level: all three diagnosed code defects were patched and covered by focused regression tests.

## Evidence

- Runtime shell capability tests passed: `28 passed` for the selected runtime suite.
- Cortex shell/projection tests passed: `37 passed` for the selected Cortex suite.
- Child problem checks completed:
  - `P004` shell capability Cortex internal auth repair.
  - `P005` tool-result `step_ref` projection repair.
  - `P006` wake-finalize compensation context repair.

## Criteria Map

- `agentctl` Cortex internal calls no longer fail for missing `X-Internal-Key` -> satisfied by runtime env propagation and generated script header test.
- Projected tool messages carry top-level `step_ref` -> satisfied by context projection regression tests.
- Compensation finalize preserves root/path/session metadata -> satisfied by saga outbox and wake-finalize payload-builder tests.
- No fallback hides the bug -> satisfied because compensation only copies present keys and tests assert explicit preservation.

## Execution Map

- `T002` / `R004` -> parent repair result aggregating `R001`, `R002`, and `R003`.

## Stress Test

- The same live failure chain now breaks at all three prior failure points:
  - shell `agentctl im read` can authenticate to Cortex;
  - the next `react_think` sees `step_ref`;
  - if a saga still fails, compensation has the context needed to finalize correctly.

## Residual Risk

- Production still needs deployment and smoke/recovery verification because the existing DB row is already stale active state.

## Result IDs

- R004

## Blocking Gaps

- none for code repair. Deployment and live recovery remain in P003.
