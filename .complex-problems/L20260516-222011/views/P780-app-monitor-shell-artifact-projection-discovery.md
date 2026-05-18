# P780: App monitor shell artifact projection discovery

Status: done
Parent: P775
Root: P000
Source Ticket: T770 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P780
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P780/README.md
Ticket(s): T772

## Problem
Discover whether Agent Monitor / ActivityTimeline surfaces project shell outputs and artifact manifests safely, without exposing raw shell-rich JSON, `_mcp_content`, raw artifact payloads, base64/data URLs, or implementation-only fields. This belongs under `P775` because Monitor is the other high-visibility surface for shell/tool output.

## Success Criteria
- Monitor, ActivityTimeline, activity hook/type, and guard test files are discovered with bounded commands.
- Hits for shell actions, tool output details, `tool-output.v1`, artifacts, Blob refs, truncation, raw payload hiding, and display/media preview are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Monitor UI files are modified in this discovery child.

## Subproblems
- none

## Results
- R761

## Latest Check
C807

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P780/README.md
- Ticket T772: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P780/tickets/T772.md
- Result R761: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P780/results/R761.md
- Check C807: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P769/children/P775/children/P780/checks/C807.md

## Follow-ups
- none
