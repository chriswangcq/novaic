# Repository finalize generation atomicity

## Problem

Repository methods that clear active state, record session ended/finalize events, or restart pending input must verify the current active session generation inside the same mutation boundary. Otherwise stale saga completion can clear or restart a newer wake.

## Success Criteria

- Map repository methods that mutate active session state during finalize/session-ended/restart/rebuild.
- Verify or implement generation/scope checks inside the same transaction as active clearing or pending restart projection.
- Remove unsafe implicit active-generation lookup or generation fallback behavior for finalize mutations.
- Add tests proving stale finalize/session-ended repository calls do not clear newer active sessions.
- Add tests proving valid finalize still clears/archives the intended active generation.

## Belongs Under

This is the state mutation boundary for T324/P328; it protects the authoritative session tables and projections.
