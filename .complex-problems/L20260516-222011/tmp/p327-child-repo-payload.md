# Attach repository payload generation audit

## Problem

Map how `SessionRepository` decides an input is attachable, computes `expected_session_generation`, and records the attach outbox payload. Verify stale scope/session state cannot produce a misleading current-generation attach payload.

## Success Criteria

- File-reference attach decision and `expected_session_generation` computation paths.
- Classify `SessionLedgerRepository.active_generation(...)` behavior when active scope mismatches.
- Verify attach outbox payload includes scope and expected generation from authoritative state.
- Flag or fix any repository-side stale-scope attach acceptance.

