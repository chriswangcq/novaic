# P385: Close residual live generation coercions

Status: done
Parent: P380
Root: P000
Source Ticket: none (none)
Source Check: C392
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/README.md
Ticket(s): T376

## Problem
The cross-repo residue guard still reports three live implicit generation coercions after T375: two in Cortex operational store write paths and one in runtime session attach active-state handling. These need to be fixed with explicit validation helpers, focused tests, and a rerun guard matrix.

## Success Criteria
- Replace the remaining raw generation coercions in `novaic-cortex/novaic_cortex/operational_store.py` with explicit non-negative generation validation.
- Replace the remaining raw active-session generation coercion in `novaic-agent-runtime/queue_service/session_repo.py` with explicit positive generation validation.
- Add focused tests that reject bool/missing/negative generation inputs where the patched boundaries can be directly exercised.
- Run focused runtime and Cortex tests covering the patched boundaries.
- Rerun cross-repo guards and provide a concise matrix classifying all remaining hits as fixed or safe.

## Subproblems
- P386: Runtime attach active generation validation
- P387: Cortex operational store generation validation
- P388: Cross-repo generation residue guard matrix

## Results
- R386

## Latest Check
C411

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/README.md
- Ticket T376: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/tickets/T376.md
- Result R386: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/results/R386.md
- Check C411: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/checks/C411.md

## Follow-ups
- none
