# P057: Phase 5C.1 Current Documentation And Comment Residue Audit

Status: done
Parent: P047
Root: P000
Package: problems/P000/children/P006/children/P047/children/P057
Body: problems/P000/children/P006/children/P047/children/P057/README.md
Ticket(s): T056

## Problem
The repo contains both current architecture docs and historical roadmap/review docs. A raw grep for fallback/legacy/file-walk terms is noisy. We need to classify current residue before editing, so historical provenance is not accidentally rewritten.

## Success Criteria
- Run focused static searches over `docs`, Cortex source comments, and relevant tests.
- Classify hits into current docs to edit, live comments/docstrings to edit, intentional guard wording, and historical docs to leave untouched.
- Specifically classify `_walk_scope_tree`, `include_display`, `/tmp/novaic-cortex-sandbox-*`, in-memory/process-local, and fallback/local authority wording.
- Produce an execution map for the remaining Phase 5C child problems.

## Subproblems
- none

## Results
- R053

## Latest Check
C057

## Bodies
- Problem: problems/P000/children/P006/children/P047/children/P057/README.md
- Ticket T056: problems/P000/children/P006/children/P047/children/P057/tickets/T056.md
- Result R053: problems/P000/children/P006/children/P047/children/P057/results/R053.md
- Check C057: problems/P000/children/P006/children/P047/children/P057/checks/C057.md

## Follow-ups
- none
