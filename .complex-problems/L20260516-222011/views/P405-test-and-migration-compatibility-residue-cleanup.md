# P405: Test and migration compatibility residue cleanup

Status: done
Parent: P329
Root: P000
Source Ticket: T393 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/README.md
Ticket(s): T440

## Problem
Tests, fixtures, migration-like files, and historical compatibility names can keep stale behavior alive by documenting or asserting old missing-generation semantics. These residues must be audited so future work does not reintroduce unsafe defaults.

## Success Criteria
- Inspect inventory hits in tests, fixtures, migration-like files, and compatibility-named code.
- Delete or rewrite tests that assert missing/stale generation success.
- Classify migration-like or historical artifacts as safe only if they are not live runtime behavior.
- Add source guards or tests that prevent reintroducing unsafe compatibility behavior where appropriate.
- Record any intentionally retained historical reference with a clear non-live classification.

## Subproblems
- P450: Test and fixture compatibility assertion audit
- P451: Migration-like and compatibility-named source audit
- P452: Test migration residue final guard

## Results
- R438

## Latest Check
C464

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/README.md
- Ticket T440: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/tickets/T440.md
- Result R438: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/results/R438.md
- Check C464: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/checks/C464.md

## Follow-ups
- none
