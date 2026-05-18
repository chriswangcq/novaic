# Harden session recovery archive identity handling

## Problem Definition

Session recovery can publish a direct `cortex.scope_end` archive task for a failed wake scope. After P350, that mutation must include positive session generation and must not publish when generation is missing or malformed.

## Proposed Solution

Propagate session generation from the suspected-dead session event into the recovery marker, require positive generation when building the recovery archive effect, and validate the archive outbox payload before publishing `TaskTopics.CORTEX_SCOPE_END`. Add tests for generation preservation and missing/invalid generation rejection.

## Acceptance Criteria

- Recovery markers preserve positive session generation from suspected-dead events.
- Recovery archive effects include `session_generation` in the direct `cortex.scope_end` payload.
- Missing, zero, boolean, or malformed generation does not publish a recovery archive mutation.
- Existing recovery dispatch and archive retry behavior remains intact.
- Focused tests cover marker/effect generation preservation and publisher-level rejection.

## Verification Plan

Compile touched recovery/outbox files and run focused tests for session recovery, recovery outbox cutover, suspected-dead recovery, active inbox recovery, and session finalize ownership. Search the recovery archive path for `session_generation` and positive-generation validation.

## Risks

- Recovery archive was historically best-effort; rejecting missing generation may leave malformed historical failed scopes unarchived, but that is safer than mutating a potentially newer session.
- Session event generation must be treated as the recovery archive generation source; tests must prove it is carried into the archive task.

## Assumptions

- Current suspected-dead session events have positive session ledger generation when they correspond to an active failed wake.
- Backward compatibility for missing generation is not required.
