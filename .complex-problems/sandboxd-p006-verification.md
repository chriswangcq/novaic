# End-to-end verification of sandboxd extraction

## Problem

The extraction is only complete if unit, integration, and active-path smoke checks prove sandboxd is actually used and the old path is not silently serving requests.

## Success Criteria

- `novaic-common`, `novaic-sandbox-service`, and `novaic-cortex` tests pass for the changed surfaces.
- A smoke check demonstrates Cortex shell execution routes through sandboxd.
- Service health checks cover sandboxd.
- The final ledger check records remaining risk explicitly; if any active-path gap remains, a follow-up problem is created.
