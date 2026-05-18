# P774: App factory log and raw JSON detail discovery

Status: done
Parent: P769
Root: P000
Source Ticket: T764 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/README.md
Ticket(s): T766

## Problem
Discover whether LLM factory logs, Monitor details, and raw JSON views still display or store tool/image payloads in a way that violates the shell-text-plus-BlobRef contract. This belongs under P769 because the user-visible logs recently exposed stale raw/base64 behavior.

## Success Criteria
- Relevant factory log, monitor, raw JSON, request/response detail, and truncation files are discovered with bounded commands.
- Hits for `_mcp_content`, raw JSON, request body, response body, display tool results, base64, Blob refs, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend/log UI files are modified in this discovery child.

## Subproblems
- P776: App factory logs page and detail discovery
- P777: App monitor timeline payload projection discovery
- P778: App raw JSON and truncation primitives discovery

## Results
- R759

## Latest Check
C805

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/README.md
- Ticket T766: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/tickets/T766.md
- Result R759: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/results/R759.md
- Check C805: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/checks/C805.md

## Follow-ups
- none
