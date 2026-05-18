# P808: VMuse Runtime URL Config Contract Remediation

Status: done
Parent: P805
Root: P000
Source Ticket: T796 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P808
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P808/README.md
Ticket(s): T800

## Problem
`services.json` still contains `runtime.vmuse_mcp_url` pointing at `http://127.0.0.1:8080/mcp`, while VMuse was cleaned to an HTTP JSON server. The field may be unused, stale, or still consumed by app/runtime code, so usage must be inspected before changing it.

## Success Criteria
- Active consumers of `vmuse_mcp_url` are identified.
- If the field is active, its name/value/usage are updated to the current HTTP JSON contract.
- If the field is inactive, it is removed or quarantined with a narrow cleanup note so stale `/mcp` config no longer looks authoritative.
- Resource and generated `services.json` copies remain synchronized after any change.
- Targeted scans for `vmuse_mcp_url`, `/mcp`, and VMuse HTTP endpoints show only intentional references.

## Subproblems
- none

## Results
- R789

## Latest Check
C837

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P808/README.md
- Ticket T800: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P808/tickets/T800.md
- Result R789: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P808/results/R789.md
- Check C837: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P808/checks/C837.md

## Follow-ups
- none
