# P769: App frontend and Monitor output contract discovery

Status: done
Parent: P754
Root: P000
Source Ticket: T758 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/README.md
Ticket(s): T764

## Problem
Discover whether app frontend/Monitor/log UI code still expects or renders raw base64/media payloads, old tool result JSON, or stale shell/display contracts. This belongs under P754 because the frontend is where tool-output and LLM-log contract drift becomes visible to users.

## Success Criteria
- Relevant frontend/Monitor/log/UI files are discovered with bounded commands.
- Suspicious hits around tool output, display, image/base64 payloads, artifact manifests, Blob refs, shell output, and factory logs are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend/app UI files are modified in this discovery child.

## Subproblems
- P773: App message media and Blob renderer discovery
- P774: App factory log and raw JSON detail discovery
- P775: App shell artifact output UI contract discovery

## Results
- R764

## Latest Check
C810

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/README.md
- Ticket T764: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/tickets/T764.md
- Result R764: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/results/R764.md
- Check C810: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/checks/C810.md

## Follow-ups
- none
