# Guard false-positive and stale-assumption review

## Problem

Review guard scripts for stale assumptions or overly broad scans that can punish valid current architecture code, especially lower-layer LogicalFS/Blob/Sandbox tests and docs.

## Success Criteria

- Inspects high-signal guard scripts for over-broad terms.
- Fixes any concrete stale or false-positive-prone guard logic.
- Records retained broad terms with justification.
