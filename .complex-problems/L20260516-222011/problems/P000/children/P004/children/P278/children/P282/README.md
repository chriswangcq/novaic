# Problem: Session schema and state ownership audit

## Problem

Audit the queue session persistence schema and repository roles to determine which table is the authority for session state, whether `tq_active_sessions` remains a live pointer/cache/view, and where input/inbox events and pending projections are stored.

## Success Criteria

- Map session-related tables and repository methods with file references.
- State clearly whether `tq_session_state` is the authoritative state source.
- Identify any duplicate active-session source that can drift or should be removed/demoted.
