# Operating Model

## Goal
Enable 7 teams to execute in parallel with low conflict and high evidence quality.

## Interaction pattern
1. Program owner updates control files.
2. Teams execute dispatch tasks and update only their own report file.
3. Program owner records round feedback.
4. Redispatch unresolved items.
5. Close round with retro.

## File ownership guidance
- Teams:
  - can edit only `rounds/<round-id>/20-reports/team-<team>-report.md`
- Program owner:
  - edits `30-round-feedback/*`
- Program/Platform:
  - edits `00-control/*`, `40-redispatch/*`, and governance files

## Conflict reduction rules
- One file, one owner per round stage.
- Shared files changed only by designated owner.
- Decisions captured in file, not chat-only.
