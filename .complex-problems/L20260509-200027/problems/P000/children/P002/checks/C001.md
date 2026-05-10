# RO/RW Optimization Models Check

## Summary

Success. The comparison covers the required models, calls out poor fits, preserves shell path ergonomics, and identifies a strong hybrid direction.

## Evidence

- Result R001 includes a candidate comparison matrix covering current disposable sync, lazy RO, explicit mount profiles, manifest/delta sync, persistent cache, OverlayFS-style design, FUSE, CLI-native object access, and hybrid managed cache.
- Result R001 cites primary Linux kernel documentation for FUSE and OverlayFS.
- Result R001 separates useful concepts from unsuitable first implementation substrates.

## Criteria Map

- Compare each candidate on performance, correctness, complexity, and fit -> satisfied by the matrix in R001.
- Preserve stable shell contract -> R001 recommends keeping `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW`.
- Explicitly reject/defer poor fits -> R001 defers FUSE and direct OverlayFS as first substrates.

## Execution Map

- T002 -> R001: comparative research and architecture option matrix.

## Stress Test

- Failure mode: pick a clever filesystem primitive that increases operational risk. Result: R001 defers FUSE/OverlayFS as substrates and recommends a product-native hybrid first.
- Failure mode: optimize only RO while RW remains slow. Result: R001 calls out RW full materialization and recommends mount profiles plus cache/delta sync.

## Residual Risk

- Non-blocking: no runtime benchmarks yet. This is intentionally handled in the recommended design phase.

## Result IDs

- R001

## Blocking Gaps

- none
