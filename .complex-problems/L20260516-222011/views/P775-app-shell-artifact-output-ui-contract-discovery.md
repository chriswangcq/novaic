# P775: App shell artifact output UI contract discovery

Status: done
Parent: P769
Root: P000
Source Ticket: T764 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/README.md
Ticket(s): T770

## Problem
Discover whether the frontend assumes shell tool output contains rich JSON/media payloads instead of terminal text plus optional artifact/blob manifests. This belongs under P769 because the shell contract changed and UI affordances must not encourage raw payload exposure.

## Success Criteria
- Relevant shell/tool output, artifact manifest, monitor timeline, and tool-call UI files are discovered with bounded commands.
- Hits for `tool-output.v1`, artifacts, Blob refs, shell stdout, truncation, display, and media preview are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend UI files are modified in this discovery child.

## Subproblems
- P779: App chat shell output rendering discovery
- P780: App monitor shell artifact projection discovery
- P781: App BlobRef and artifact preview contract discovery

## Results
- R763

## Latest Check
C809

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/README.md
- Ticket T770: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/tickets/T770.md
- Result R763: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/results/R763.md
- Check C809: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/checks/C809.md

## Follow-ups
- none
