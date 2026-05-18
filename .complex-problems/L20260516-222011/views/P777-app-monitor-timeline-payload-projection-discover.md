# P777: App monitor timeline payload projection discovery

Status: done
Parent: P774
Root: P000
Source Ticket: T766 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P777
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P777/README.md
Ticket(s): T768

## Problem
Discover whether Agent Monitor timeline/detail rendering still exposes raw tool payloads, `_mcp_content`, base64 media, or stale display output instead of projected shell text and BlobRef/artifact manifests. This belongs under P774 because Monitor cards and detail drawers are a separate user-visible path from the factory-log page.

## Success Criteria
- Monitor/timeline files and tests are discovered with bounded commands.
- Hits for `_mcp_content`, tool output, display results, base64/data URLs, BlobRefs, artifacts, truncation, and projection helpers are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No monitor/timeline UI files are modified in this discovery child.

## Subproblems
- none

## Results
- R757

## Latest Check
C803

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P777/README.md
- Ticket T768: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P777/tickets/T768.md
- Result R757: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P777/results/R757.md
- Check C803: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P774/children/P777/checks/C803.md

## Follow-ups
- none
