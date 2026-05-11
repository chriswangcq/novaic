# Production state check

## Result IDs

- R000

## Evidence

R000 cites production evidence from deploy status, queue session tables, queue saga/task tables, Cortex scope projection, and Cortex payload manifest.

## Criteria Map

- Identify whether this is a deploy/process issue: satisfied. All deployed services/workers were healthy.
- Identify whether the wake is still active: satisfied. `tq_session_state` is `no_active` and session events include `session_finalized`.
- Identify the exact stuck/failure point: satisfied. The failed task is `llm.call` inside `react_think`, with `Tool result not found` for a Cortex payload BlobRef.
- Preserve enough evidence for root-cause repair: satisfied. The manifest maps the BlobRef to the stable source step ref, which gives a precise code-level hypothesis.

## Execution Map

The inspection was bounded to read-only production queries and local code search. It did not modify production state.

## Stress Test

The conclusion is not based on one log line. It remains consistent if the UI monitor is stale: backend state says the session finalized, while the UI is displaying the failed wake card. It also remains consistent if deployment happened later: the captured failure is persisted in queue and Cortex state.

## Residual Risk

The production-state problem is solved. A separate root-cause/code-repair problem remains open because the system can still reproduce this class of failure until code is fixed and deployed.
