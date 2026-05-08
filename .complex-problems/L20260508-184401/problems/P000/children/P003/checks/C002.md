# Check P003 deploy and production smoke

## Evidence

- Result `R002` records deploy and smoke evidence.
- `./deploy services` completed and fresh-smoke logs passed for every backend and runtime process.
- Live smoke notification `18c14d716c0a` reached Entangled, Queue, Runtime, and LLM execution.
- After the dispatch TTL, the notification still had `dispatch_attempts=1` and Queue had exactly one `input_received` and one `dispatch_wake_start_queued`, proving the duplicate dispatch/lease expiry bug is closed for this path.

## Criteria Map

- Code deployed: satisfied by successful `./deploy services` and fresh-smoke.
- Production message delivery restored: satisfied by Entangled notification plus Queue session events for `18c14d716c0a`.
- Runtime monitor/loop reaction restored: satisfied by wake scope `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0`, successful `session.init`, `im_read`, context append, and LLM calls.
- No duplicate redispatch after ack: satisfied by `dispatch_attempts=1` and single Queue input event count after TTL.

## Execution Map

- Local regression tests: business 65, common 18, runtime 24 all passed.
- Deploy: `./deploy services` completed with all required processes up.
- Smoke: created live IM notification, waited beyond dispatch TTL, queried Entangled and Queue durable stores.

## Stress Test

The TTL wait specifically exercised the previous failure mode where a successful dispatch left the notification pending under an expiring lease and caused repeated dispatch attempts. The new dispatch ack kept attempts at 1 while preserving Runtime semantic claim.

## Residual Risk

The smoke confirms the main user-facing failure path. It does not exhaustively prove every historical active/ending/recovering session branch, but the targeted tests cover claim/recovery DB contention, outbox store commit ownership, active attach outbox behavior, and subscriber dispatch ack behavior.
