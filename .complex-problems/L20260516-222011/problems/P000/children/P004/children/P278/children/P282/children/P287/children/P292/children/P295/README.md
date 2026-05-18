# Problem: Session finalize restart rebuild transaction flow audit

## Problem

Audit session finalize/session_ended, pending restart, suspected-dead recovery, and startup rebuild flows for generation correctness and state mutation ownership.

## Success Criteria

- Map finalize/restart/rebuild branches and transaction boundaries with file references.
- Identify whether stale finalize/restart paths can mutate current state.
- Flag any duplicated state mutation outside the ledger boundary.
