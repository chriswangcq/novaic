# P000: Make Agent Monitor activity titles structured and non-heuristic

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Activity Monitor currently projects public row titles in the frontend by inspecting private reasoning text. This produced incorrect non-model-generated titles such as `正在组织回复` when the reasoning content merely contained the word `回复`. The long-term architecture should make monitor titles a structured public projection instead of UI keyword guessing, while preserving agent reasoning detail as the detailed text when available.

Scope includes the runtime activity projection, shared/app entity contract, frontend normalization/rendering, regression tests, and repository commit hygiene for the touched subrepos and parent gitlink.

## Success Criteria
- Runtime activity records expose an explicit structured public title field for monitor UI.
- Frontend renders activity titles from structured public fields or safe phase/status fallback, not from reasoning text keywords.
- Agent reasoning content can still be shown as detail text; only heuristic title generation is removed.
- Existing read/reply/tool/summary monitor behavior remains user-facing and low-level shell labels remain hidden.
- Tests cover the screenshot regression: reasoning text containing `回复` must not render `正在组织回复` unless that title is explicitly provided as a public title.
- Relevant frontend and runtime tests pass, and unrelated lint failures are documented if they pre-exist.
- Changes are committed in affected subrepos and the parent repo records updated submodule pointers.

## Subproblems
- P001: Add structured public title to activity projection contract and runtime
- P002: Render Agent Monitor titles from public fields, not reasoning keywords
- P003: Verify, clean, and commit structured activity title change

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R003: problems/P000/results/R003.md
- Check C003: problems/P000/checks/C003.md

## Follow-ups
- none
