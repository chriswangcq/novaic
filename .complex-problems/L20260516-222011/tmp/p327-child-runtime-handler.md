# Runtime attach handler generation enforcement audit

## Problem

Audit the runtime side of active input attachment to verify `expected_session_generation` is required and compared with current wake/session generation before mutating context or inbox.

## Success Criteria

- Locate runtime attach handler and current session generation source.
- Verify missing expected generation is rejected.
- Verify stale expected generation is rejected.
- Identify tests proving handler-side generation enforcement.

