# P652: Remove Cortex API URL Default from Test Helper

Status: done
Parent: P651
Root: P000
Source Ticket: none (none)
Source Check: C682
Package: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/children/P652
Body: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/children/P652/README.md
Ticket(s): T647

## Problem
`novaic-cortex/cortex_tests/workspace_test_utils.py::make_cortex_with_store` still defaults `cortex_api_url` to `http://cortex.test`. This is test-only, but it violates the explicit dependency boundary: tests can build Cortex without stating the service URL dependency.

## Success Criteria
- `make_cortex_with_store` requires an explicit `cortex_api_url` argument or an explicit fixture/config object with no hidden default.
- Existing tests are updated to pass an explicit fake URL at call sites or through an explicit local fixture/helper wrapper whose name states the fake URL contract.
- Focused Cortex runtime/helper tests still pass.
- A scan for `cortex_api_url: str =` under Cortex runtime and test helper code returns no hidden helper default.

## Subproblems
- none

## Results
- R642

## Latest Check
C683

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/children/P652/README.md
- Ticket T647: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/children/P652/tickets/T647.md
- Result R642: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/children/P652/results/R642.md
- Check C683: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/children/P652/checks/C683.md

## Follow-ups
- none
