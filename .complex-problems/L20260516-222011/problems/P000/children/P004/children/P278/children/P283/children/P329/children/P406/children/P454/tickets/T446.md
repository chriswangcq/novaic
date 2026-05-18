# Ticket: Run aggregate compatibility focused behavior tests

## Problem Definition

The aggregate source/test guard matrix is classified, but behavior must be verified through focused runtime and Cortex test suites. This ticket validates the live paths for attach, finalize, session end, recovery, session-state/generation guards, archive/context/event/payload/shell projection, and compatibility residue guards.

## Proposed Solution

- Run the focused `novaic-agent-runtime` tests covering:
  - generation-checked attach and outbox cutover
  - finalize ownership and session-ended behavior
  - suspected-dead recovery and recovery outbox
  - session state SSOT and active-session removal
  - legacy/compat residue guards
  - shell output and no historical tool-image injection contracts
- Run the focused `novaic-cortex` tests covering:
  - context event lifecycle and skill lifecycle
  - context writes/read-source guards/projection/store
  - payload inspection and scope summary contracts
  - shell capability blob contract and tool/step output projection
  - legacy skill lifecycle removal and lock/compat boundary guards
- Save logs and exit statuses under `.complex-problems/L20260516-222011/tmp/p454/`.
- If any suite fails, do not mark success; spawn a repair/follow-up ticket with the concrete failing tests.

## Acceptance Criteria

- Runtime focused test log is saved with exit status.
- Cortex focused test log is saved with exit status.
- All selected tests pass, or failures are converted into repair follow-up tickets.
- Result explicitly cites test commands and artifacts.

## Verification Plan

- Inspect both logs for pass/fail summary and unexpected skips.
- Confirm the exact test selection covers all P454 success criteria.
- Record a result only after both suites complete.
