# Final large-output leakage cross-scan

## Problem
Run final cross-repository scans after child sweeps to catch unbounded `json.dumps`, raw payload reads, no-limit text projections, or stale base64/large-output guidance not covered by previous children.

## Success Criteria
- Final findings are mapped to child classifications or fixed.
- No unclassified active large-output-to-LLM/log path remains.
- Representative tests pass after any changes.
