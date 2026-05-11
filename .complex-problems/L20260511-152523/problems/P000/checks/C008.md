# Agent loop stall repair root check

## Summary

The root problem is solved. The production stall was traced to a concrete three-part failure chain, all three code defects were fixed, and production is deployed with the affected session no longer active.

## Evidence

- Diagnosis found exact production failures in queue DB, worker logs, and Cortex logs.
- Code changes repaired:
  - shell capability Cortex internal auth;
  - top-level `step_ref` projection;
  - wake-finalize compensation context preservation.
- Tests passed:
  - runtime focused suite: `28 passed`;
  - Cortex focused suite: `37 passed`.
- Production deploy passed:
  - all backend services and workers healthy.
- Production verification passed:
  - main agent session state is `no_active`;
  - direct shell smoke succeeded with `exit_code=0`;
  - recent logs are clean for the old signatures.

## Criteria Map

- Find clear cause of the long hang -> satisfied by `R000`.
- Fix code, not only symptoms -> satisfied by `R004`.
- Deploy and verify production -> satisfied by `R007`.
- Avoid half-connected new logic -> satisfied by direct production smoke through deployed shell/Cortex path.

## Execution Map

- `P001` / `R000`: live production diagnosis.
- `P002` / `R004`: implementation repair across runtime and Cortex.
- `P003` / `R007`: deployment and live verification.

## Stress Test

- If internal auth were still broken, smoke would fail with 401.
- If context projection were still broken, the old `Tool message missing step_ref` signature would recur on recent logs.
- If compensation finalize were still narrowing context, recent logs/session state would show root-scope finalize failure or stale active session.

## Residual Risk

- Full LLM-provider reply path was not forced. This is acceptable for this incident because the observed stall occurred before provider execution and the repaired pre-provider path is now directly verified.

## Result IDs

- R008

## Blocking Gaps

- none
