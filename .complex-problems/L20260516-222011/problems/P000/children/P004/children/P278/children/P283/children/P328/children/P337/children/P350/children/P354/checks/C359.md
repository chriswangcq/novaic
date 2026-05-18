# P354 success check

## Summary

Success. R338 solves P354: terminal subagent status mutation is no longer based on coarse `agent_id/subagent_id` alone. The path now has explicit payload identity, handler validation before Business mutation, and a session-ended acceptance gate before terminal status tasks can run.

## Evidence

- P357/R334/C355: `wake_finalize` terminal status payloads carry `scope_id` and positive `session_generation`; missing/non-positive generation is rejected; legacy last-scope fields are not emitted.
- P358/R335/C356: terminal status handlers validate `scope_id` and positive `session_generation` before `entity_update()`; malformed payloads do not touch Business.
- P359/R336/C357: `session_ended` is ordered before terminal status tasks, both status tasks depend on `session_ended`, and `finalize_rejected` fails the task gate rather than unblocking downstream status mutations.
- P360/R337/C358: aggregate verification passed 109 tests and source guards.

## Criteria Map

- Inspect subagent status payload builders and Business handlers: met by P357 and P358.
- Add explicit expected wake/session identity checks before status mutation or prove independence: met by P357 payload propagation and P358 pre-mutation validation.
- Add tests for missing identity and stale identity: met by P358 malformed/missing identity tests and P359 stale-finalize rejection gate test.
- Remove compatibility path that lets missing identity mutate status: met by P358 tests asserting `entity_update()` is not called for missing identity and P360 source guard/mutation scan.

## Execution Map

- Parent split ticket T341 produced child problems P357-P360.
- All child problems are done and have success checks:
  - C355
  - C356
  - C357
  - C358
- Parent result R338 consolidates those child results.

## Stress Test

- Plausible stale-finalize failure chain: payload has only `agent_id/subagent_id`, handler accepts it, `session_ended` later rejects generation after Business status already changed. This chain is broken at three points:
  - payload builders now require and emit current identity.
  - handlers reject missing/invalid identity before mutation.
  - status tasks cannot run until `session_ended` succeeds, and rejected finalize now fails the task gate.

## Residual Risk

- P351 still owns recovery/compensation finalize identity. That is outside P354's terminal subagent status path and is explicitly tracked elsewhere.

## Result IDs

- R338
