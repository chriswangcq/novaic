# P605: Add exact backend preview boundary evidence and focused tests

Status: done
Parent: P603
Root: P000
Source Ticket: none (none)
Source Check: C626
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P603/children/P605
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P603/children/P605/README.md
Ticket(s): T596

## Problem
Close the evidence gap for P603 by collecting exact line-numbered backend slices and focused test output for Agent Monitor/progress preview payload boundaries. The follow-up must prove whether backend monitor/progress paths expose bounded text/payload references and remain separate from LLM request image injection.

## Success Criteria
- Append exact line-numbered slices for `/v1/steps/read_preview`, payload inspection APIs, step payload externalization/indexing, and Business monitor/progress schema or event projection surfaces.
- Run focused tests that directly cover payload externalization, bounded payload preview/read APIs, and Agent Monitor timeline/progress boundary behavior.
- Record whether any backend monitor/progress event path can carry raw image bytes or base64.
- Map evidence back to the original P603 criteria with residual risk explicitly stated.

## Subproblems
- none

## Results
- R589

## Latest Check
C627

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P603/children/P605/README.md
- Ticket T596: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P603/children/P605/tickets/T596.md
- Result R589: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P603/children/P605/results/R589.md
- Check C627: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P603/children/P605/checks/C627.md

## Follow-ups
- none
