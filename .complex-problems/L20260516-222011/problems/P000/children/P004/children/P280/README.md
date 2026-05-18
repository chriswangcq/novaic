# Finalize, watchdog, and recovery ownership audit

## Problem

Audit finalize ownership, suspected-dead/watchdog behavior, recovery wake creation, and remaining stack archival semantics.

## Success Criteria

- Map finalize/recovery code paths with file references.
- Confirm ownership is event/FSM-oriented or identify gaps.
- Add/fix tests if the audit finds an active gap.
