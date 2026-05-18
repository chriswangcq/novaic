# P781: App BlobRef and artifact preview contract discovery

Status: done
Parent: P775
Root: P000
Source Ticket: T770 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P781
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P781/README.md
Ticket(s): T773

## Problem
Discover whether App image/file preview and BlobRef handling surfaces treat artifacts as references resolved through Blob/Gateway, instead of embedding raw base64/data URLs or assuming shell stdout contains displayable media bytes. This belongs under `P775` because shell now emits terminal text plus artifact manifests, and preview affordances must consume those references safely.

## Success Criteria
- Blob attachment, authenticated image, image preview, file upload/download, and artifact-related UI files/tests are discovered with bounded commands.
- Hits for `blob://`, artifact manifests, image preview, base64/data URLs, direct file bytes, display integration, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No BlobRef/artifact preview UI files are modified in this discovery child.

## Subproblems
- none

## Results
- R762

## Latest Check
C808

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P781/README.md
- Ticket T773: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P781/tickets/T773.md
- Result R762: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P781/results/R762.md
- Check C808: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P781/checks/C808.md

## Follow-ups
- none
