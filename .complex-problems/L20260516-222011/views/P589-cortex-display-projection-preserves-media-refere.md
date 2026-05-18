# P589: Cortex display projection preserves media references

Status: done
Parent: P586
Root: P000
Source Ticket: T576 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P589
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P589/README.md
Ticket(s): T579

## Problem
Cortex step-result projection currently understands data URLs as display images and degrades normal URLs to text. After runtime durable payloads become BlobRef-only, Cortex must preserve BlobRef display media references for `display_perception` while keeping history and summary projections text/reference-only.

## Success Criteria
- `parse_tool_result` recognizes explicit display media references such as `image_ref` or BlobRef-backed `display_files`.
- `format_for_display_perception_llm` can emit an unresolved image reference item without embedding base64.
- `format_for_history_llm` and preview paths remain text/reference-only.
- Shell/tool artifact manifest projection remains unchanged and does not become visual perception by accident.

## Subproblems
- none

## Results
- R572

## Latest Check
C609

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P589/README.md
- Ticket T579: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P589/tickets/T579.md
- Result R572: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P589/results/R572.md
- Check C609: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P589/checks/C609.md

## Follow-ups
- none
