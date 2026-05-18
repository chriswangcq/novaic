# P643: Path Normalization and Abuse RW Fixture Rewrite

Status: done
Parent: P639
Root: P000
Source Ticket: T634 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P643
Body: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P643/README.md
Ticket(s): T637

## Problem
Path normalization/adversarial tests include `/rw/scratch` in positive and negative path strings. These should be rewritten carefully so they still test normalization and traversal rejection without canonizing root scratch.

## Success Criteria
- Updates `test_paths_adversarial.py`, `test_runtime_path_abuse.py`, and any related path tests.
- Preserves traversal rejection, double-slash normalization, unicode/control/path abuse checks, and runtime path validation semantics.
- Runs focused path abuse tests.

## Subproblems
- none

## Results
- R631

## Latest Check
C672

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P643/README.md
- Ticket T637: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P643/tickets/T637.md
- Result R631: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P643/results/R631.md
- Check C672: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P643/checks/C672.md

## Follow-ups
- none
