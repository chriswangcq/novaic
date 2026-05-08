# Check success

## Summary

Success for diagnosis scope. The task was to find the clear reason why a user message got no reply and no agent-monitor reaction. The result identifies the exact failed handoff and the deeper runtime condition, with DB and log evidence.

## Evidence

- Entangled persisted user message `d0fd5569974f` and its notification.
- The notification is `failed` with `dispatch_attempts=5`.
- Subscriber logs show `ReadTimeout` posting to `http://127.0.0.1:19997/api/queue/dispatch` for the same notification.
- Queue DB has no session event for `d0fd5569974f`, proving the message never entered the queue/session ledger.
- Queue Service logs show global FIFO lock waits around the same time and repeated SQLite `database is locked` errors.
- Saga workers repeatedly get 500 from `/api/queue/sagas/claim`; the existing wake saga is still pending.

## Criteria Map

- Find whether the message reached persistence: satisfied.
- Find whether the runtime/monitor saw it: satisfied; it did not reach queue session events.
- Find the immediate cause: satisfied; subscriber dispatch timed out.
- Find the deeper cause: satisfied; queue-service lock contention/database locking plus saga claim failures.
- Avoid guessing: satisfied; all claims are backed by production DB/log inspection.

## Execution Map

- T000 produced R000.
- R000 contains the root-cause diagnosis and evidence chain.

## Stress Test

Alternative explanations were checked:

- "Frontend lost the message" is false because the message exists in `environment_im_messages`.
- "Agent/LLM was slow" is false for this message because it never entered queue/session events.
- "Everything was down" is false because processes were up; the failure is an internal queue-service contention/error path.
- "Monitor bug only" is insufficient because there is no queue session event for the message.

## Residual Risk

The exact production fix is not included in this diagnosis. The next step should be a separate repair ticket focused on dispatch fast-path isolation, DB lock reduction, saga claim 500s, and a production E2E smoke test.

## Result IDs

- R000

## Blocking Gaps

None for the diagnostic question. There are implementation gaps for repair, but they are outside this ticket's success criteria.
