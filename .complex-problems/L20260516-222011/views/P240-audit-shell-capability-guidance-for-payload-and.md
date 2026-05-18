# P240: Audit shell capability guidance for payload and output boundaries

Status: done
Parent: P230
Root: P000
Source Ticket: T231 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230/children/P240
Body: problems/P000/children/P003/children/P129/children/P230/children/P240/README.md
Ticket(s): T237

## Problem
Shell capability help and CLI guidance must teach bounded terminal output, explicit payload read/search/summarize/qa commands, and artifact/display usage without encouraging agents to paste raw large outputs or base64 into replies/context.

This belongs under `P230` because most interface tools now live inside shell, so CLI guidance is the practical contract the agent sees.

## Success Criteria
- `shell_capabilities.py` payload/help text is mapped with file/function pointers.
- Guidance clearly points to explicit `cortex payload ...` commands for full payload inspection.
- Focused shell capability and output contract tests pass.
- Any stale or misleading wording found is corrected.

## Subproblems
- P245: Map shell capability payload and artifact guidance
- P246: Correct stale shell capability wording if found
- P247: Verify shell payload and output boundary tests

## Results
- R236

## Latest Check
C251

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P240/README.md
- Ticket T237: problems/P000/children/P003/children/P129/children/P230/children/P240/tickets/T237.md
- Result R236: problems/P000/children/P003/children/P129/children/P230/children/P240/results/R236.md
- Check C251: problems/P000/children/P003/children/P129/children/P230/children/P240/checks/C251.md

## Follow-ups
- none
