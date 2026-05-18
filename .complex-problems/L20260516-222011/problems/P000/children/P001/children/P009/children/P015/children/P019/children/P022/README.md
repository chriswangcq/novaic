# Remove tracked generated complex-problems dashboard residue

## Problem

The tracked `dashboards/complex-problems-dashboard.html` generated snapshot is stale, large, and pollutes architecture residue scans. Remove it from source and prevent future generated dashboard HTML from being committed accidentally.

## Success Criteria

- `dashboards/complex-problems-dashboard.html` is deleted from the tracked source tree.
- The repository ignores generated dashboard HTML if appropriate.
- Residue searches no longer return this stale dashboard as a hit.
- The deletion does not remove the real `.complex-problems` ledger source of truth.
