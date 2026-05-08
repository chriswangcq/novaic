# P007 Ticket - Roster-driven runtime launch generation

## Problem Definition
`scripts/start.sh` now consumes the canonical runtime roster for verification, but it still manually launches each runtime worker role with duplicated loops and command blocks. This leaves a second operational worker list in the launch path.

## Proposed Solution
Move runtime worker launch commands into the canonical roster view and make `scripts/start.sh` execute the generated launch commands. Keep URL/config argument variables in `start.sh`, but remove worker role/count/log duplication from the script.

## Acceptance Criteria
- `runtime_roster.py` owns launch command generation for all runtime/subscriber roles.
- `scripts/start.sh` launches runtime workers by consuming `runtime_worker_roster.py launch-commands`.
- No manual task/saga/outbox/health/scheduler/subscriber launch loops or duplicate process role lists remain in `scripts/start.sh`.
- Tests/lints fail if launch commands drift from the roster.

## Verification Plan
- Add/update tests for `launch-commands`.
- Run worker roster SSOT tests.
- Run runtime worker supervision lint and deploy fresh-smoke lint.
- Run `bash -n scripts/start.sh` and `bash -n deploy`.

## Risks
- Generated shell commands rely on trusted repository code and shell variables defined by `start.sh`; quote carefully and verify syntax.

## Assumptions
- Backward compatibility with old launch block structure is not needed.
