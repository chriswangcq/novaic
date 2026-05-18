# P719: Business/subscriber code dependency boundary audit

Status: done
Parent: P716
Root: P000
Source Ticket: T708 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P719
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P719/README.md
Ticket(s): T711

## Problem
Audit Business/subscriber active code for hidden env/config reads or ownership leaks that contradict the explicit dependency boundary, especially around subscriber aggregation config and dispatch behavior. This belongs under P716 because code-level residue would be higher impact than doc residue and must be proven clean or patched.

## Success Criteria
- Active subscriber aggregation path is checked for dynamic `os.environ` reads inside business decisions.
- Business/subscriber code paths are checked for direct wake/session/Cortex lifecycle ownership leakage.
- Safe code residue is patched if found.
- Test-only environment reads or fixtures are classified and not mistaken for production hidden inputs.
- If code remediation is not needed, the result cites exact evidence.

## Subproblems
- none

## Results
- R703

## Latest Check
C747

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P719/README.md
- Ticket T711: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P719/tickets/T711.md
- Result R703: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P719/results/R703.md
- Check C747: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P719/checks/C747.md

## Follow-ups
- none
