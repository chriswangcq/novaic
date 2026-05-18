# P773: App message media and Blob renderer discovery

Status: done
Parent: P769
Root: P000
Source Ticket: T764 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P773
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P773/README.md
Ticket(s): T765

## Problem
Discover whether the chat/message UI and media renderer still expects raw base64 image/audio payloads instead of BlobRefs/artifact manifests. This belongs under P769 because message rendering is where users should see files/images rather than raw tool payloads.

## Success Criteria
- Relevant chat/message/media renderer files are discovered with bounded commands.
- Hits for base64, data URLs, image rendering, attachments, Blob refs, display, and artifact manifests are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend files are modified in this discovery child.

## Subproblems
- none

## Results
- R755

## Latest Check
C801

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P773/README.md
- Ticket T765: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P773/tickets/T765.md
- Result R755: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P773/results/R755.md
- Check C801: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P773/checks/C801.md

## Follow-ups
- none
