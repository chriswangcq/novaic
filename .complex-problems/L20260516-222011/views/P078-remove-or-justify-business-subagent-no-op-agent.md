# P078: Remove or justify Business subagent no-op agent stub path

Status: done
Parent: P077
Root: P000
Source Ticket: T068 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P078
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P078/README.md
Ticket(s): T069

## Problem
`business/internal/subagent_utils.py` contains a no-op `ensure_agent_stub`, and `business/internal/subagent.py` still calls it. This looks like compatibility residue and may keep misleading extension points alive.

## Success Criteria
- The helper and call site are removed if no current behavior depends on them.
- Tests are updated if they monkeypatch or assert the no-op helper.
- If any part must remain, it is renamed/reworded as current behavior and covered by a focused test.

## Subproblems
- none

## Results
- R061

## Latest Check
C073

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P078/README.md
- Ticket T069: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P078/tickets/T069.md
- Result R061: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P078/results/R061.md
- Check C073: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P078/checks/C073.md

## Follow-ups
- none
