# P735: Classify Device VmControl screenshot route

Status: done
Parent: P734
Root: P000
Source Ticket: T724 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P735
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P735/README.md
Ticket(s): T725

## Problem
Determine the status of `novaic-device/device/vmcontrol_routes.py` screenshot output. It currently returns inline MCP-style image bytes from `/api/vmcontrol/vms/{vm_id}/screenshot`. We need to know whether this is active product/runtime behavior, legacy compatibility, safe-to-retire, or a remediation candidate for the Blob/artifact contract.

## Success Criteria
- The screenshot route implementation is inspected with file pointers.
- Route mounting and call sites are checked so its active/dormant status is evidence-based.
- The final classification states exactly one status: active product path, legacy compatibility, safe-to-retire, or remediation candidate.
- If remediation is needed, the required change is stated minimally.

## Subproblems
- none

## Results
- R715

## Latest Check
C759

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P735/README.md
- Ticket T725: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P735/tickets/T725.md
- Result R715: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P735/results/R715.md
- Check C759: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P735/checks/C759.md

## Follow-ups
- none
