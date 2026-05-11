# P005: Audit and fix agentctl CLI Blob contract

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P005
Body: problems/P000/children/P003/children/P005/README.md
Ticket(s): T004

## Problem
`agentctl` shell capability commands must not emit raw binary artifact content inline. This child problem audits IM, subagent, and media commands, and fixes any output path that violates the Blob contract.

## Success Criteria
- `agentctl media audio-qa` requires `blob://` input and does not print raw audio bytes.
- `agentctl im` command output is text/metadata only and does not inline attachment bytes.
- `agentctl subagent spawn` output is ordinary text/metadata only.
- Any violation discovered in active code is fixed and verified.
- Evidence references concrete code paths and test results.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/children/P005/README.md
- Ticket T004: problems/P000/children/P003/children/P005/tickets/T004.md
- Result R002: problems/P000/children/P003/children/P005/results/R002.md
- Check C002: problems/P000/children/P003/children/P005/checks/C002.md

## Follow-ups
- none
