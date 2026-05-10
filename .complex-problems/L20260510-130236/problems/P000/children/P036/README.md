# Fix Canonical Test Matrix LogicalFS Dependency Boundary

## Problem

The final root verification exposed that `scripts/run_all_tests.sh` ran `novaic-logicalfs` tests with `PYTHONPATH="."` only. After adding `logicalfs.blob_store`, the package explicitly depends on `novaic-common` for `common.http.clients`, so the canonical matrix failed even though package-local targeted tests passed with an explicit PYTHONPATH.

## Success Criteria

- `scripts/run_all_tests.sh` encodes the LogicalFS dependency boundary explicitly.
- The canonical test matrix passes end to end.
- The fix is recorded and checked before root problem closure.
