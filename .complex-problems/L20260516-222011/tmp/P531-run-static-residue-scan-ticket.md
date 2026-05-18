# Run Static Residue Scan Ticket

## Problem Definition

P512 needs the raw static residue scan output from the P514/P516 guard pattern before any classification can be trusted.

## Proposed Solution

Run the P514 guard pattern over `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, `novaic-agent-runtime/queue_service/fsm`, and `novaic-agent-runtime/tests`. Save raw output, production/test split files, and counts.

## Acceptance Criteria

- Exact pattern and command are recorded.
- Raw scan output is saved.
- Production and test hit split files are saved.
- Total, production, and test hit counts are recorded.

## Verification Plan

- Use `.complex-problems/L20260516-222011/tmp/p514/guard-pattern.txt` as the pattern.
- Use absolute `rg` path if needed.
- Save artifacts under `.complex-problems/L20260516-222011/tmp/p531/`.

## Risks

- Broad pattern will produce noisy hits; P532 owns classification.

## Assumptions

- P514/P516 scope and pattern are authoritative.
