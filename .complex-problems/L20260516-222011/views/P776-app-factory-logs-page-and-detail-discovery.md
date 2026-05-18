# P776: App factory logs page and detail discovery

Status: done
Parent: P774
Root: P000
Source Ticket: T766 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P776
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P776/README.md
Ticket(s): T767

## Problem
Discover whether the LLM factory logs page, list query, detail modal, and request/response JSON rendering still expose raw tool payloads, `_mcp_content`, base64 media, or unprojected display results. This belongs under P774 because factory logs are the user-visible place where raw request/response JSON recently looked wrong.

## Success Criteria
- Factory-log page, hook/service, table, detail modal, and API-client files are discovered with bounded commands.
- Hits for request body, response body, raw JSON, `_mcp_content`, base64, BlobRefs, artifacts, display results, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No factory-log UI files are modified in this discovery child.

## Subproblems
- none

## Results
- R756

## Latest Check
C802

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P776/README.md
- Ticket T767: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P776/tickets/T767.md
- Result R756: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P776/results/R756.md
- Check C802: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P776/checks/C802.md

## Follow-ups
- none
