# P614: Shell Wrapper Terminal Output Boundary

Status: done
Parent: P576
Root: P000
Source Ticket: T607 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P614
Body: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P614/README.md
Ticket(s): T608

## Problem
Audit shell execution/wrapper output paths to verify shell tool results shown to LLM are bounded terminal text plus artifact manifests, not raw media/base64 payloads.

## Success Criteria
- Records scans for shell wrapper, tool-output contract, truncation, artifact manifest, and devicectl wrappers.
- Cites code slices showing bounded text and BlobRef artifact manifest behavior.
- Runs focused shell output contract tests.
- Creates follow-up if shell history can inline raw media/base64 output.

## Subproblems
- none

## Results
- R603

## Latest Check
C644

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P614/README.md
- Ticket T608: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P614/tickets/T608.md
- Result R603: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P614/results/R603.md
- Check C644: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P614/checks/C644.md

## Follow-ups
- none
