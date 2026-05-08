# Runtime worker supervision

## Problem Definition

Runtime workers are launched as background subprocesses, but startup success can still be inferred from a coarse process count. That hides missing roles, duplicate roles, or fast-crashing workers behind a vague "workers N" status.

## Proposed Solution

Make the runtime worker roster explicit in the production start/status path. `scripts/start.sh` should verify the exact required worker/subscriber roles after launch and fail startup if any required role is missing or duplicated. `deploy status` should show the same role-level supervision table. Add a CI guard so the role roster and verification hook cannot be removed silently.

## Acceptance Criteria

- `scripts/start.sh` verifies exact expected counts for task-control, task-execution, saga, session-outbox, saga-outbox, health, scheduler, and subscriber after startup.
- Startup exits non-zero if any required worker role count is wrong.
- `./deploy status` reports role-level runtime worker counts instead of only a coarse worker total.
- CI/lint coverage guards the supervision functions, expected roles, and workflow wiring.
- Documentation explains that worker roles are explicit required subprocesses.

## Verification Plan

- `bash -n scripts/start.sh`
- `bash -n deploy`
- Run a new runtime-supervision lint script.
- Run existing start/config and current docs lints.
- Inspect the diff for stale coarse-only worker status.

## Risks

- Exact role counts may expose duplicate/stale worker processes that previously went unnoticed. That is desirable for correctness, but deploy failures may become more explicit.
- Process matching must be precise enough not to count unrelated helper commands.

## Assumptions

- Production worker command lines include `main_novaic.py` plus the role names used by `start.sh`.
- There should be exactly 2 control task workers, 2 execution task workers, 2 saga workers, and exactly 1 each of session-outbox, saga-outbox, health, scheduler, and subscriber.
