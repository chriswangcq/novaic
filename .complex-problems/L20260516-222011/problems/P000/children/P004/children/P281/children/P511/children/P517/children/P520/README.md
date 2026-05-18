# Repair Session Outbox Finalize Focused Test Failures

## Problem

The P517 focused pytest subset failed in three tests covering recovery remaining-stack semantics, attach outbox published status, and session repository wrapper-boundary expectations.

## Success Criteria

- Understand whether each failure is a production bug or stale test expectation.
- Apply the minimal correct code/test updates.
- Rerun the failing tests and the P517 focused subset successfully.
- Record exact files changed, commands, and counts.
