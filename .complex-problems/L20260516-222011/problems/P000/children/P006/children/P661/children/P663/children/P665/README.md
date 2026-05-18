# Guard contract gap matrix

## Problem

Compare the current architecture contracts against the inventory and produce an explicit gap matrix. This should say which contracts are guarded, by what, and whether any concrete missing/stale coverage exists.

## Success Criteria

- Lists current contracts to protect.
- Maps each contract to root CI guard(s) and/or module guard test(s).
- Identifies concrete guard gaps or states no-gap with evidence.
- Saves the matrix as a ledger artifact.
