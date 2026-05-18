# Run Unit Tool Output Focused Pytest Ticket

## Problem Definition

The P528 unit/tool-output target list is validated but unexecuted. P529 must run pytest on that exact list and preserve exact evidence.

## Proposed Solution

Create a runtime-cwd target list by stripping `novaic-agent-runtime/`, run pytest from `novaic-agent-runtime`, and save target count, command, exit code, and pytest log.

## Acceptance Criteria

- Pytest runs against exactly the P528 target list.
- The command, target count, exit code, collected count, and final summary are saved.
- Empty-suite and partial-run false positives are rejected.
- Failures are recorded for follow-up instead of patched in this ticket.

## Verification Plan

- Diff the stripped runtime-cwd list against the P528 list transformation.
- Run pytest from `novaic-agent-runtime`.
- Inspect log for collected count and final pass/fail summary.

## Risks

- Cwd mismatch could produce false failures.
- Empty or partial run could look green without adequate evidence.

## Assumptions

- P528 target list is authoritative.
