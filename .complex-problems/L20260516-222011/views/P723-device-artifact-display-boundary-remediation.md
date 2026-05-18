# P723: Device/artifact/display boundary remediation

Status: done
Parent: P708
Root: P000
Source Ticket: T713 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/README.md
Ticket(s): T733

## Problem
Patch safe active stale claims or small contract violations found by the Device/devicectl and artifact/display discovery children. This belongs under P708 because active code/docs must reflect the final media boundary: Device captures, Blob stores bytes, shell returns text/manifests, display projects media to model input.

## Success Criteria
- Discovery cleanup candidates are reviewed and dispositioned.
- Safe active stale docs/code claims are patched.
- Any active large-media-as-text path found in shell/history/context surfaces is patched or split into a blocking subproblem.
- Risky broad changes are not hidden; they become follow-up/spawned problems.

## Subproblems
- P742: Update stale VMuse protocol mapping documentation
- P743: Clean VMuse source residue and resource sync
- P744: Disposition Device VmControl screenshot route

## Results
- R731

## Latest Check
C776

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/README.md
- Ticket T733: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/tickets/T733.md
- Result R731: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/results/R731.md
- Check C776: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/checks/C776.md

## Follow-ups
- none
