# Verify runtime bridge emits structured step requests

## Problem Definition

The agent runtime bridge is the producer of Cortex step-write requests during real agent loops. It must send structured `observation` plus refs, not legacy inline raw `result`, otherwise the stricter Cortex API can reject live tool results or lose pointer recoverability.

## Proposed Solution

Map runtime bridge code that calls Cortex step-write APIs, inspect the constructed request shape, run focused runtime tests if available, and patch producer/tests if stale inline shapes remain.

## Acceptance Criteria

- Runtime bridge step-write call sites are mapped with source pointers.
- Produced request shape includes structured `observation` and uses `payload`/`payload_ref` for full output where applicable.
- No active runtime bridge code sends inline raw `result`.
- Focused test/source evidence proves live shell/tool output follows the new contract.

## Verification Plan

Use `rg` to locate `steps/write`, `write_step`, `payload_ref`, and bridge client calls in runtime code. Run relevant runtime tests around Cortex bridge/tool result recording. Add regression coverage if a request-building helper exists.

## Risks

- Runtime tests may be integration-heavy or absent.
- Some shell output projection may happen in worker code rather than bridge code, requiring a small spawn if discovered.

## Assumptions

- Cortex API-side validation is already covered by `P149`; this ticket focuses on producer shape before API submission.
