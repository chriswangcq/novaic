# P812: Child Problem: Factory logs safe payload projection

Status: done
Parent: P786
Root: P000
Source Ticket: T804 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/README.md
Ticket(s): T805

## Problem
`novaic-llm-factory/static/factory-logs.html` still has detail rendering paths that stringify raw request/response/messages/tool details. This can surface large payloads or base64-like content in the logs UI and mislead future debugging.

## Success Criteria
- Request/response raw JSON detail rendering is bounded or scrubbed before display.
- Message and tool-call renderers project large or media-like values safely rather than dumping raw content.
- The UI still exposes enough metadata for debugging: role, model, status, latency, token counts, tool names, and compact references.
- Focused static checks or lightweight tests prove obvious base64/blob-like payloads are redacted or summarized.

## Subproblems
- P816: Child Problem: Factory logs rendering inventory
- P817: Child Problem: Factory logs safe projection helper
- P818: Child Problem: Wire factory log renderers to safe projection
- P819: Child Problem: Factory logs projection verification

## Results
- R800

## Latest Check
C849

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/README.md
- Ticket T805: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/tickets/T805.md
- Result R800: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/results/R800.md
- Check C849: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/checks/C849.md

## Follow-ups
- none
