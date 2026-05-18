# P389: Normalize remaining runtime generation default boundaries

Status: done
Parent: P388
Root: P000
Source Ticket: none (none)
Source Check: C395
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/README.md
Ticket(s): T380

## Problem
The widened cross-repo guard found remaining raw generation/defaulting patterns in runtime session FSM, session repo state adapters, session ledger/audit, and broader task/saga/lease FSM infrastructure. Some may be safe projection/counter adapters, but they are not yet explicitly classified or normalized.

## Success Criteria
- Audit all widened guard hits involving `generation`, `finalize_generation`, `current_generation`, and related control-plane defaults in runtime Queue/task code.
- Replace live control-plane session generation coercions with explicit validators or typed inputs.
- Classify audit/projection/generic counter adapters as safe only with clear file evidence and tests where needed.
- Add focused regression tests for any live generation boundary changed.
- Rerun narrow and widened guards and provide a final clean matrix with no unclassified residue.

## Subproblems
- P390: Session FSM finalize generation validation
- P391: Session repo and ledger generation adapters
- P392: Audit and generic FSM generation classification
- P393: Round and stack-depth default classification
- P398: Close remaining unclassified generation-like guard hits

## Results
- R381

## Latest Check
C409

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/README.md
- Ticket T380: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/tickets/T380.md
- Result R381: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/results/R381.md
- Check C404: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/checks/C404.md
- Check C409: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/checks/C409.md

## Follow-ups
- P398: Close remaining unclassified generation-like guard hits
