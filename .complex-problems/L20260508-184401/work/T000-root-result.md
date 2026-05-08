# Root dispatch repair result

## Summary

The dispatch-to-runtime repair is complete across code, regression tests,
deployment, and production smoke. The root ticket was split into code repair,
targeted tests, and deploy/smoke subproblems; all three child problems now have
successful checks.

## Done

- P001 repaired the dispatch path by extending the Business subscriber HTTP
  timeout, preventing long background Queue claim/recovery work from blocking
  foreground dispatch, adding bounded SQLite busy retry/commit ownership to the
  generic FSM store, and adding dispatch-only acknowledgement for successful
  Environment-to-Queue delivery.
- P002 added targeted regression coverage for the repaired boundaries.
- P003 deployed all backend services and verified a live IM
  `18c14d716c0a` reached Queue/Runtime once without duplicate redispatch after
  the dispatch lease TTL.

## Verification

- Child checks: P001, P002, and P003 are success.
- Production smoke: `input_received = 1`,
  `dispatch_wake_start_queued = 1`, `dispatch_attempts = 1`, and Runtime
  executed `session.init`, `im_read`, context append, and `llm.call` for wake
  scope `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0`.

## Gaps

None for the root dispatch/monitor-reaction problem. Natural-language reply
content still depends on the LLM/provider and agent behavior above the harness,
which is outside this repair's state-machine/dispatch boundary.

## Artifacts

- `.complex-problems/L20260508-184401/views/P001-code-repair-queue-dispatch-and-saga-claim.md`
- `.complex-problems/L20260508-184401/views/P003-deploy-and-production-smoke.md`
