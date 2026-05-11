# Live diagnosis check

## Summary

The diagnosis ticket successfully identified a concrete, code-backed failure chain for the production stall. It does not claim the system is fixed; it proves why the current agent loop got stuck and defines the repair targets for subsequent tickets.

## Evidence

- Queue DB showed a stale active session for the main agent after the loop failed.
- Saga/task rows showed `react_think` failed on `Tool message missing step_ref`, followed by a failed compensation `wake_finalize`.
- Runtime logs showed the initiating shell tool error: `agentctl` received `HTTP 401` from Cortex `/v1/meta/read` because `X-Internal-Key` was missing.
- Cortex logs showed `/v1/scope/end` treating the wake scope as a root scope and raising `FileNotFoundError`.
- Local code inspection found matching defects in shell capability auth, context projection, and saga compensation context propagation.

## Criteria Map

- Identify why the loop stalls -> satisfied by the chained cause: internal-auth shell failure, missing projected `step_ref`, failed compensation finalize, session stuck active.
- Identify where it fails in code -> satisfied by the four named modules and functions.
- Avoid surface-only diagnosis -> satisfied because the result explains both the trigger and the failed recovery path.

## Execution Map

- `T001` / `R000` -> inspected live process status, queue DB, worker logs, Cortex logs, and local source paths; recorded the concrete failure chain and repair targets.

## Stress Test

- Could it be only a slow worker? No: services were alive, workers were polling, and DB contained failed sagas plus stale active session state.
- Could it be only shell timeout? No: the first observed shell failure was a deterministic 401 from Cortex internal auth, and the later stall required the separate `step_ref` and finalize-context bugs.
- Could code repair alone clear the existing stuck row? Not guaranteed; the result records that live recovery/cleanup must be handled in the deploy/verify phase.

## Residual Risk

The diagnosis relies on previously captured production evidence and local source inspection. It is sufficient for repair design, but the production row remains stuck until the code fix is deployed and recovery/smoke tests prove the session can end or recover.

## Result IDs

- R000

## Blocking Gaps

- none for diagnosis. Implementation and production recovery remain open under sibling problems.
