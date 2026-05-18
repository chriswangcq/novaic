# P670: Smoke-test ergonomics and deployment freshness guard audit

Status: done
Parent: P007
Root: P000
Source Ticket: T667 (split)
Source Check: none
Package: problems/P000/children/P007/children/P670
Body: problems/P000/children/P007/children/P670/README.md
Ticket(s): T831

## Problem
Inspect smoke-test scripts, deployment freshness guards, runbooks, and tests used after deploy/runtime changes. Find places where smoke failures are hard to interpret, rely on stale tool contracts, or omit important runtime checks.

## Success Criteria
- Existing smoke scripts, deploy freshness guards, and smoke-related docs/tests are searched and inspected.
- Current expected smoke behavior is documented or encoded where missing.
- Low-risk script/test/doc improvements are applied for concrete gaps.
- Smoke-related checks are run locally where possible without destructive deployment actions.

## Subproblems
- P833: Smoke and deploy guard script inventory and contract check
- P834: Smoke and deploy guard local execution verification

## Results
- R831

## Latest Check
C880

## Bodies
- Problem: problems/P000/children/P007/children/P670/README.md
- Ticket T831: problems/P000/children/P007/children/P670/tickets/T831.md
- Result R831: problems/P000/children/P007/children/P670/results/R831.md
- Check C880: problems/P000/children/P007/children/P670/checks/C880.md

## Follow-ups
- none
