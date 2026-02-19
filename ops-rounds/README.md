# Ops Rounds Control Plane

This directory is the single source of truth for round-based execution.

## Workflow
1. `00-control`: define round charter, gates, and scoreboard
2. `10-dispatch`: assign team work orders
3. `20-reports`: teams submit work reports with evidence
4. `30-review`: reviewer records findings and pass/fail decision
5. `40-redispatch`: targeted re-assignment based on findings
6. `90-close`: round retrospective and carry-over items

## Round Rules
- Every task must include owner, due date, acceptance criteria, and evidence.
- Any open P0 finding blocks round closure.
- No verbal status is considered complete without file-based evidence.
- All status updates must use governance status codes.

## Directory Convention
- `round-XXX` where `XXX` is a zero-padded integer, e.g. `round-002`.
