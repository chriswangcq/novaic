# P726: Blob artifact manifest and history replay discovery

Status: done
Parent: P722
Root: P000
Source Ticket: T715 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/README.md
Ticket(s): T717

## Problem
Discover how Blob/runtime-artifact URIs and `tool-output.v1` manifests are persisted, replayed, and projected into later context/history. This must verify manifest-only history behavior so old media does not re-enter LLM context as raw text.

## Success Criteria
- Runtime/Cortex code that parses or stores artifact manifests is identified with file pointers.
- History replay behavior for artifact manifests is identified with tests or code evidence.
- Any active history replay path that injects raw media/base64 text is listed as a remediation candidate.
- Blob ownership is separated from live LogicalFS/RO/RW semantics.

## Subproblems
- P729: Runtime artifact manifest handling discovery
- P730: Cortex tool output and context projection discovery
- P731: Historical image replay guardrail discovery

## Results
- R712

## Latest Check
C756

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/README.md
- Ticket T717: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/tickets/T717.md
- Result R712: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/results/R712.md
- Check C756: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/checks/C756.md

## Follow-ups
- none
