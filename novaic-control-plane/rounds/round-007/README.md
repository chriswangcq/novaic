# Round 007

## Objective
Fix Round 006 evidence integrity issues and close the round with clean, auditable PASS conditions.

## Root cause to fix
- Teams passed local checks but not round-level gates.
- Audit script false positives reduced trust in feedback.
- Canonical `repo_url` policy was applied inconsistently.

See `00-control/problem-solution-target.md` for mandatory closure definition.

## Round cadence
- blocker sync during active round
- reports submitted before round close

## Team task entrypoints
- Platform: `10-dispatch/team-platform.md`
- API: `10-dispatch/team-api.md`
- Runtime: `10-dispatch/team-runtime.md`
- Agent Runtime: `10-dispatch/team-agent-runtime.md`
- Tools: `10-dispatch/team-tools.md`
- Storage-A/B: `10-dispatch/team-storage-ab.md`
- Desktop: `10-dispatch/team-desktop.md`

## Hard rule
- Canonical `repo_url` violations must be zero.
- Audit artifacts must match current report states.
- DONE requires replayable evidence and no template placeholders.
