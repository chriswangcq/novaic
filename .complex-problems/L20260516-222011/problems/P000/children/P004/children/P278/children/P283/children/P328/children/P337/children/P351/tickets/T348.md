# Recovery compensation finalize identity hardening

## Problem Definition

Recovery and compensation code can synthesize `wake_finalize` work after a failed saga or dead session. If those synthesized contexts omit wake scope identity or positive session generation, the runtime can reintroduce stale finalize hazards even after the normal wake-finalize path is hardened.

## Proposed Solution

Audit and harden recovery/compensation sources that create or replay `wake_finalize` contexts. The solution should trace the failed saga/session identity from persistence through recovery decision and compensation task creation, then either preserve positive session generation and wake scope identity or reject/reroute ambiguous contexts before they can mutate Cortex or Business state.

## Acceptance Criteria

- Inspect `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, recovery tests, compensation tests, and any helper that creates `wake_finalize` from failure state.
- Identify every compensation/recovery path that emits `wake_finalize` or equivalent finalize mutation work.
- Preserve explicit positive `session_generation` and wake scope identity when the source saga/session had them.
- Reject or route missing-generation recovery through a non-mutating dead-session/recovery path rather than creating ambiguous finalize mutation work.
- Add focused tests proving generation preservation and rejection/reroute behavior.
- Run residue searches for generation defaulting or compatibility fallback in recovery/compensation paths.

## Verification Plan

Run focused recovery and compensation pytest files after implementation, plus source searches for `wake_finalize`, `session_generation`, and zero/default generation patterns under `queue_service`. Also compile touched modules and record exact evidence in the result.

## Risks

- Recovery code may have multiple entry points and historical compatibility assumptions; a single-pass implementation could miss a path.
- Some tests may encode old fallback behavior; failures should be treated as useful evidence rather than patched around casually.
- If persisted failed saga records do not contain generation, a correct fix may require explicit non-mutating recovery behavior instead of pretending the data is available.

## Assumptions

- P350 has already hardened the normal wake-finalize path; this ticket focuses on synthesized recovery/compensation finalize contexts.
- Backward compatibility for ambiguous historical finalize records is not required; the user prefers deleting or rejecting stale compatibility paths over preserving old behavior.
