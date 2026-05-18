# Production fix or no-op proof for near-integrated regression

## Problem

After the regression exists, decide whether production code needs changes. If it passes on current implementation, record a no-op proof; if it fails, fix the smallest boundary-respecting defect and remove stale conflicting code.

## Success Criteria

- New regression is run at least once.
- If failing, production fix is implemented at context/projection boundary.
- If passing, no-op proof cites the passing regression and explains why no production change is needed.
- No obsolete branch is left behind if a production fix is required.
