# P447: Cortex media payload and projection compatibility guard

Status: done
Parent: P420
Root: P000
Source Ticket: T435 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P447
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P447/README.md
Ticket(s): T437

## Problem
Final Cortex verification needs a focused guard for shell/display/tool-result/payload projection boundaries, especially raw base64 or large payloads entering LLM history as text.

## Success Criteria
- Save source guard scans for `_mcp_content`, base64/media payload markers, shell artifact contracts, step-result projection, and payload readback.
- Classify remaining hits as shell text manifest, display perception path, bounded payload inspection, tests/fixtures, or unresolved risk.
- Confirm shell/agent-facing behavior remains pointer-oriented and does not expose raw screenshot/file payloads as ordinary context text.
- Confirm display perception remains shell-outside and does not poison historical context.

## Subproblems
- none

## Results
- R430

## Latest Check
C456

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P447/README.md
- Ticket T437: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P447/tickets/T437.md
- Result R430: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P447/results/R430.md
- Check C456: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P447/checks/C456.md

## Follow-ups
- none
