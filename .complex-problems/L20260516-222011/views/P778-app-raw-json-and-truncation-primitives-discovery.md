# P778: App raw JSON and truncation primitives discovery

Status: done
Parent: P774
Root: P000
Source Ticket: T766 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P778
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P778/README.md
Ticket(s): T769

## Problem
Discover whether shared raw JSON, smart value, truncation, sanitization, and binary-detection primitives can still leak raw tool/media payloads into user-visible detail views. This belongs under P774 because these primitives may be reused by factory logs, monitor details, and future debugging surfaces.

## Success Criteria
- Shared JSON/value/truncation/sanitization primitives are discovered with bounded commands.
- Hits for raw JSON, pretty-printing, copy/detail rendering, `_mcp_content`, base64/data URLs, BlobRefs, artifacts, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No shared UI primitive files are modified in this discovery child.

## Subproblems
- none

## Results
- R758

## Latest Check
C804

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P778/README.md
- Ticket T769: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P778/tickets/T769.md
- Result R758: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P778/results/R758.md
- Check C804: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P778/checks/C804.md

## Follow-ups
- none
