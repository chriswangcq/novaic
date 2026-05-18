# P624: Runtime Sandbox SDK Call Site Residue

Status: done
Parent: P621
Root: P000
Source Ticket: T617 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624
Body: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/README.md
Ticket(s): T619

## Problem
Audit active runtime shell/tool execution call sites to verify they use the sandbox SDK/service boundary and do not perform direct subprocess execution, host path mounting, or legacy local fallback.

## Success Criteria
- Records exact scans over `novaic-agent-runtime` call sites for sandbox SDK imports, shell execution, subprocess/process/local/fallback/host/mount terms.
- Cites the runtime source slices that instantiate or call the sandbox SDK.
- Confirms active runtime shell/tool handlers call the SDK/service boundary.
- Creates a remediation follow-up if any active runtime path bypasses sandboxd.

## Subproblems
- P626: Runtime Shell Handler SDK Wiring
- P627: Runtime Legacy Execution Residue Classification

## Results
- R616

## Latest Check
C657

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/README.md
- Ticket T619: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/tickets/T619.md
- Result R616: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/results/R616.md
- Check C657: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/checks/C657.md

## Follow-ups
- none
