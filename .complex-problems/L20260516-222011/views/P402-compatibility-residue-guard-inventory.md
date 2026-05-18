# P402: Compatibility residue guard inventory

Status: done
Parent: P329
Root: P000
Source Ticket: T393 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P402
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P402/README.md
Ticket(s): T394

## Problem
The project needs a concrete guard inventory before cleanup. Broad searches must enumerate optional/missing/stale generation compatibility patterns across runtime queue code, task handlers, Cortex code, tests, and migration-like files, then classify which areas require deeper child work.

## Success Criteria
- Run source guards covering generation/session_generation/expected_generation/finalize_generation/current_generation defaulting, optional branches, active lookup, and active clear/restart/archive helpers.
- Include runtime queue code, task handlers/sagas/contracts, Cortex code, tests, and migration-like directories in the search scope.
- Produce a hit matrix with file references and initial classification buckets.
- Identify which hits are already safe due to explicit validators/tests and which require child cleanup.
- Do not change implementation code in this inventory child.

## Subproblems
- none

## Results
- R389

## Latest Check
C415

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P402/README.md
- Ticket T394: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P402/tickets/T394.md
- Result R389: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P402/results/R389.md
- Check C415: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P402/checks/C415.md

## Follow-ups
- none
