# P722: Artifact/display/context projection discovery

Status: done
Parent: P708
Root: P000
Source Ticket: T713 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/README.md
Ticket(s): T715

## Problem
Discover how screenshot/artifact outputs flow through shell output, Blob/artifact manifests, display, LLM request construction, and Cortex/Runtime context history. This belongs under P708 because previous failures involved base64 leaking into context or display not projecting media to the LLM correctly.

## Success Criteria
- Shell/tool output contract for screenshots/artifacts is identified.
- Blob/artifact URI and manifest-only history behavior are identified.
- Display tool output and LLM image projection path are identified.
- Cleanup candidates are listed for any active path that still embeds large media bytes as text.

## Subproblems
- P725: Shell artifact manifest output contract discovery
- P726: Blob artifact manifest and history replay discovery
- P727: Display current-round LLM image projection discovery
- P728: Legacy and standalone media-byte surface classification

## Results
- R725

## Latest Check
C770

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/README.md
- Ticket T715: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/tickets/T715.md
- Result R725: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/results/R725.md
- Check C770: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/checks/C770.md

## Follow-ups
- none
