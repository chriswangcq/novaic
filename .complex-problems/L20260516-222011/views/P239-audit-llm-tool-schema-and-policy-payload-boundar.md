# P239: Audit LLM tool schema and policy payload boundary

Status: done
Parent: P230
Root: P000
Source Ticket: T231 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230/children/P239
Body: problems/P000/children/P003/children/P129/children/P230/children/P239/README.md
Ticket(s): T232

## Problem
The LLM-visible tool policy/schema surface must expose shell and explicit payload tools consistently with the payload boundary, without stale direct-tool or hidden large-output assumptions.

This belongs under `P230` because schema/policy is what tells the model which tools exist and how payload inspection is invoked.

## Success Criteria
- Runtime tool surface policy is mapped and confirms payload inspection tools are explicit CLI/shell capabilities where intended.
- Tool schema tests verify payload tools and limits are present and bounded.
- No active schema guidance encourages raw payload/base64 injection into normal context.

## Subproblems
- P241: Fix cross-package pytest tests namespace conflict

## Results
- R228

## Latest Check
C247

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P239/README.md
- Ticket T232: problems/P000/children/P003/children/P129/children/P230/children/P239/tickets/T232.md
- Result R228: problems/P000/children/P003/children/P129/children/P230/children/P239/results/R228.md
- Check C242: problems/P000/children/P003/children/P129/children/P230/children/P239/checks/C242.md
- Check C247: problems/P000/children/P003/children/P129/children/P230/children/P239/checks/C247.md

## Follow-ups
- P241: Fix cross-package pytest tests namespace conflict
