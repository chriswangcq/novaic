# P002: Render Agent Monitor titles from public fields, not reasoning keywords

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
The frontend `ActivityTimeline` currently derives public titles from `record.text` for reasoning records. This creates incorrect labels such as `正在组织回复` from private thought content. The app should consume structured `public_title` when available and use safe structured fallback for legacy records.

## Success Criteria
- TypeScript activity record type includes `public_title`.
- `useActivityTimeline` normalization carries only the explicit public title field, without spreading raw entities.
- `ActivityTimeline` uses `public_title` first, then existing structured tool/phase fallback.
- Reasoning text is still shown as detail when safe, but is not used to infer titles.
- Frontend tests cover legacy records, explicit public titles, read/reply behavior, and the screenshot regression.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
