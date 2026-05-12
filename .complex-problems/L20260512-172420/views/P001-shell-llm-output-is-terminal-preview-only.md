# P001: Shell LLM Output Is Terminal Preview Only

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Tighten the runtime shell output contract so the LLM-facing `tool-output.v1` text behaves like a terminal preview: exit code, bounded stdout/stderr, truncation markers, and small metadata. It must not duplicate full raw stdout/stderr in diagnostics. Full replay remains available from Cortex step/payload storage.

## Success Criteria
- `raw_shell_result` is removed from shell `tool-output.v1.diagnostics`.
- Shell diagnostics keep only small, explicit fields such as exit code, stdout/stderr char counts, truncation flags, and changed file count.
- Shell text remains useful and bounded for success and nonzero exit cases.
- Unit tests cover large stdout/stderr and assert full raw output is not embedded in the LLM-facing envelope.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
