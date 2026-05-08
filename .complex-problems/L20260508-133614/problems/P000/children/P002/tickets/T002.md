# P002 Ticket - Worker DSL 与 roster SSOT 收口

## Problem Definition
Worker assembly has a generic substrate, but worker roster and boot commands are still repeated across runtime code, `scripts/start.sh`, `deploy`, lint scripts, and documentation. This makes old worker paths easy to leave behind and makes runtime topology drift from code.

## Proposed Solution
Create one runtime-owned worker roster source of truth and generate/consume all operational worker lists from it. Keep worker computation in business modules, but make process names, commands, service names, and supervision expectations derive from a small infrastructure registry.

## Acceptance Criteria
- One canonical roster module/file owns the queue runtime worker list.
- Runtime assembly imports the canonical roster instead of hard-coded duplicate lists.
- Start/deploy/lint checks consume the canonical roster or an exported generated view.
- No stale separate hard-coded worker roster remains in core operational paths.
- Tests/lints verify that startup/deploy/supervision references match the canonical roster.

## Verification Plan
- Inspect current worker definitions in runtime code, scripts, deploy, CI lint scripts, and docs.
- Add or update a focused test/lint that compares operational references with the canonical roster.
- Run targeted worker assembly / supervision tests.
- Run relevant shell syntax/lint checks for touched scripts.

## Risks
- Deployment scripts may have shell constraints that make direct Python imports awkward. If so, generate a plain text or JSON roster artifact from the canonical module and make scripts consume that.
- Some documentation may intentionally describe old topology. Mark it retired or update it, rather than carrying compatibility text.

## Assumptions
- We do not need backward compatibility with old worker names unless they are still active in current deployment.
- The business worker implementation can remain in business modules; this ticket only makes roster/assembly SSOT.
