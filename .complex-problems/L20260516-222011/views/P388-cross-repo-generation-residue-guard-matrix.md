# P388: Cross-repo generation residue guard matrix

Status: done
Parent: P385
Root: P000
Source Ticket: T376 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/README.md
Ticket(s): T379

## Problem
After runtime and Cortex patches, the cross-repo guards must be rerun and classified so the parent problem can prove no unclassified live generation residue remains.

## Success Criteria
- Rerun the generation coercion guard over runtime and Cortex target directories.
- Rerun the active/finalize/archive residue guards.
- Provide a concise matrix classifying each remaining hit as fixed, safe helper/test code, or safe boundary signature.
- No live path remains that silently defaults generation or acts on stale active session generation.
- This belongs under P385 because source guard proof is required after patching both repositories.

## Subproblems
- P389: Normalize remaining runtime generation default boundaries

## Results
- R372

## Latest Check
C410

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/README.md
- Ticket T379: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/tickets/T379.md
- Result R372: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/results/R372.md
- Check C395: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/checks/C395.md
- Check C410: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/checks/C410.md

## Follow-ups
- P389: Normalize remaining runtime generation default boundaries
