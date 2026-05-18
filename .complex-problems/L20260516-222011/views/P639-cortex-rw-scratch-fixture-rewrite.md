# P639: Cortex RW Scratch Fixture Rewrite

Status: done
Parent: P636
Root: P000
Source Ticket: T632 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639
Body: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/README.md
Ticket(s): T634

## Problem
Cortex tests use root `/rw/scratch` as generic writable fixture paths. These tests should use neutral `/rw/tmp` or current subagent-aware scratch paths so root scratch no longer looks canonical.

## Success Criteria
- Rewrites Cortex test fixture paths from `/rw/scratch` to appropriate current paths.
- Preserves each test's original invariant: path normalization, binary IO, truncation, metrics, abuse rejection, and RW tree reading.
- Keeps current `/rw/subagents/main/scratch` sandboxd tests intact.
- Runs focused tests for touched files.

## Subproblems
- P641: Workspace and Authority RW Fixture Rewrite
- P642: Runtime and Tool RW Fixture Rewrite
- P643: Path Normalization and Abuse RW Fixture Rewrite

## Results
- R632

## Latest Check
C673

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/README.md
- Ticket T634: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/tickets/T634.md
- Result R632: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/results/R632.md
- Check C673: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/checks/C673.md

## Follow-ups
- none
