# Status Codes

Allowed status values:

- `PLANNED`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`
- `DONE_WITH_GAPS`
- `REJECTED`

## Rules

- `DONE` requires execution evidence.
- `DONE_WITH_GAPS` must include explicit gap, owner, and target_round.
- `BLOCKED` must include dependency and unblock action.
