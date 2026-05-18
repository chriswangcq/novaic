# Finalize and recovery ownership remediation

## Problem

The ownership map may reveal active gaps where finalize, watchdog, or recovery paths can mutate session state or archive scopes outside the intended event/FSM/outbox ownership model.

## Success Criteria

- Any concrete active ownership gap from the map is fixed or split into a smaller follow-up.
- Required compensation/recovery paths are retained and documented rather than deleted.
- Focused tests are added or updated for any changed behavior.
- If no source change is needed, the result explicitly explains why the map found no active gap.
