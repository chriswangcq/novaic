# Finalize and session-ended generation ownership audit

## Problem

Audit finalize/session-ended paths to verify they close or advance only the intended session generation and cannot clear a newer active session because of stale saga completion, watchdog, recovery, or nested skill closure behavior.

## Success Criteria

- Map all finalize/session-ended entry points and the generation/session keys they carry.
- Verify current-generation checks before clearing active state, restarting pending input, or archiving remaining stack.
- Identify whether remaining stack and reason are recorded at the generation boundary.
- Add or identify tests proving stale finalize/session-ended events do not close the wrong active generation.

