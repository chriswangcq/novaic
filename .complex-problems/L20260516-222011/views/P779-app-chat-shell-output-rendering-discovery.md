# P779: App chat shell output rendering discovery

Status: done
Parent: P775
Root: P000
Source Ticket: T770 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P779
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P779/README.md
Ticket(s): T771

## Problem
Discover whether chat-facing UI renders shell tool output as terminal text plus attachments/artifact manifests, or whether it still expects shell stdout/tool results to contain rich JSON/media payloads. This belongs under `P775` because chat is the primary user-visible surface for shell output contract violations.

## Success Criteria
- Chat message, Markdown, attachment, converter, and tool-result display files are discovered with bounded commands.
- Hits for shell stdout, `tool-output.v1`, artifacts, Blob refs, display output, base64/data URLs, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No chat UI files are modified in this discovery child.

## Subproblems
- none

## Results
- R760

## Latest Check
C806

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P779/README.md
- Ticket T771: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P779/tickets/T771.md
- Result R760: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P779/results/R760.md
- Check C806: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P779/checks/C806.md

## Follow-ups
- none
