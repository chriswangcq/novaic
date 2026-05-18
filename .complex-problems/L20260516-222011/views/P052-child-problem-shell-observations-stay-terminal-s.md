# P052: Child Problem: shell observations stay terminal-shaped

Status: done
Parent: P048
Root: P000
Source Ticket: T041 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/README.md
Ticket(s): T049

## Problem
The shell tool should behave like a human terminal: return bounded text output and pointers, not structured media blobs. Even when a subprocess emits large JSON or accidental base64, shell observation projection should remain bounded and should not encourage the model to treat truncated binary text as semantic context.

## Success Criteria
- Shell result projection has explicit length bounds and terminal-style text semantics.
- Shell output contract documents that complete data lives in Cortex RO steps/artifacts rather than inline LLM context.
- Tests or scans cover a large-media stdout case and prove context receives only bounded text or manifests.

## Subproblems
- P059: Child Problem: runtime shell wrapper enforces bounded terminal text
- P060: Child Problem: Cortex shell step projection preserves terminal semantics
- P061: Child Problem: large media-like shell stdout regression coverage

## Results
- R047

## Latest Check
C059

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/README.md
- Ticket T049: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/tickets/T049.md
- Result R047: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/results/R047.md
- Check C059: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/checks/C059.md

## Follow-ups
- none
