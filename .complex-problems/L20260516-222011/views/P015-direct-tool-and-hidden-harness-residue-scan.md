# P015: Direct tool and hidden harness residue scan

Status: done
Parent: P009
Root: P000
Source Ticket: T008 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015
Body: problems/P000/children/P001/children/P009/children/P015/README.md
Ticket(s): T009

## Problem
Search active code/tests/docs for old direct LLM tools that should now be shell CLI capabilities, such as `im_reply`, `payload_read`, `subagent_spawn`, and `audio_qa`, and distinguish current intended references from stale residue.

## Success Criteria
- Active code and current tests are searched with bounded output.
- Current tool schema contract is not contradicted by stale references.
- Any active direct-tool exposure or misleading docs are fixed or routed.
- Historical ledger hits are excluded or labeled as historical.

## Subproblems
- P018: IM direct tool residue scan
- P019: Payload direct tool residue scan
- P020: Subagent and audio direct tool residue scan
- P025: Clean ActivityTimeline legacy direct-tool assumptions
- P028: Reconcile remaining current docs with shell-first tool contract
- P031: Update Cortex environment notification hint to shell-first IM read
- P032: Neutralize internal reply-cap comments from direct im_reply wording
- P033: Follow-up: classify and isolate remaining direct-tool vocabulary

## Results
- R013

## Latest Check
C045

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/README.md
- Ticket T009: problems/P000/children/P001/children/P009/children/P015/tickets/T009.md
- Result R013: problems/P000/children/P001/children/P009/children/P015/results/R013.md
- Check C018: problems/P000/children/P001/children/P009/children/P015/checks/C018.md
- Check C022: problems/P000/children/P001/children/P009/children/P015/checks/C022.md
- Check C026: problems/P000/children/P001/children/P009/children/P015/checks/C026.md
- Check C028: problems/P000/children/P001/children/P009/children/P015/checks/C028.md
- Check C030: problems/P000/children/P001/children/P009/children/P015/checks/C030.md
- Check C045: problems/P000/children/P001/children/P009/children/P015/checks/C045.md

## Follow-ups
- P025: Clean ActivityTimeline legacy direct-tool assumptions
- P028: Reconcile remaining current docs with shell-first tool contract
- P031: Update Cortex environment notification hint to shell-first IM read
- P032: Neutralize internal reply-cap comments from direct im_reply wording
- P033: Follow-up: classify and isolate remaining direct-tool vocabulary
