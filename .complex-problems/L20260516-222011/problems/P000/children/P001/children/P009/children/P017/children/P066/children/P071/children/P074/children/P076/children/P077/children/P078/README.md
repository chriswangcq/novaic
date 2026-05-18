# Remove or justify Business subagent no-op agent stub path

## Problem
`business/internal/subagent_utils.py` contains a no-op `ensure_agent_stub`, and `business/internal/subagent.py` still calls it. This looks like compatibility residue and may keep misleading extension points alive.

## Success Criteria
- The helper and call site are removed if no current behavior depends on them.
- Tests are updated if they monkeypatch or assert the no-op helper.
- If any part must remain, it is renamed/reworded as current behavior and covered by a focused test.
