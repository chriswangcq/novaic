# P021: Classify Gateway SQLite State and Postgres Boundary

Status: done
Parent: P010
Root: P000
Source Ticket: T019 (split)
Source Check: none
Package: problems/P000/children/P004/children/P010/children/P021
Body: problems/P000/children/P004/children/P010/children/P021/README.md
Ticket(s): T020

## Problem
Gateway may have a live or archived `gateway.db` containing auth, file registry, or operational state. Its tables need explicit classification before deciding whether they migrate to `novaic_gateway`, remain obsolete residue, or are owned by Entangled/other services.

This belongs under P010 because Gateway has a distinct runtime and ownership boundary from Cortex.

## Success Criteria
- The live `api` host is checked for `gateway.db` and any WAL/SHM files, including file metadata and open holders if present.
- Gateway process args and code paths that reference SQLite are identified without recording secrets.
- Gateway schema and row counts are captured if a live or archived DB exists.
- Gateway tables are classified as auth state, file/entity ops state, obsolete residue, or migration candidate.
- Future Postgres boundary and backup expectations are documented.
- No Gateway production cutover is attempted.

## Subproblems
- none

## Results
- R017

## Latest Check
C017

## Bodies
- Problem: problems/P000/children/P004/children/P010/children/P021/README.md
- Ticket T020: problems/P000/children/P004/children/P010/children/P021/tickets/T020.md
- Result R017: problems/P000/children/P004/children/P010/children/P021/results/R017.md
- Check C017: problems/P000/children/P004/children/P010/children/P021/checks/C017.md

## Follow-ups
- none
