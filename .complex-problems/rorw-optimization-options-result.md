# RO/RW Optimization Models Comparison Result

## Summary

The best fit is not a pure FUSE or privileged mount solution. The strongest direction is a staged hybrid: keep the stable shell paths and disposable process semantics, but replace full per-exec tree materialization with explicit mount profiles, manifest/delta sync, and a managed per-agent cache. FUSE/OverlayFS can inform the model, but they should not be the first implementation substrate.

## Done

Compared the candidate models:

| Option | Performance Upside | Correctness Risk | Complexity | Fit |
| --- | --- | --- | --- | --- |
| Current disposable full materialization | Simple, reliable, clear cleanup | Cost grows with RO/RW size | Low | Baseline only |
| Lazy RO heuristic only | Already avoids RO for simple commands | Heuristic misses path intent; RW still full | Low | Keep but not enough |
| Explicit mount profiles | Avoids accidental full RO/RW for CLI-only commands | Needs command contract and tests | Low-medium | Strong Phase 1 |
| Manifest/delta sync | Avoids re-copying unchanged files | Requires content version/etag manifest and delete handling | Medium | Strong Phase 2 |
| Persistent per-agent cache | Turns repeated commands into local copy/link operations | Cache invalidation and concurrent exec isolation | Medium-high | Strong Phase 3 |
| OverlayFS-style lower/upper | Great conceptual model for RO lower + RW upper copy-up | Privileged/host-specific mount behavior, whiteout/copy-up semantics | High | Learn from it, do not start here |
| FUSE virtual filesystem | True lazy file reads and directory listings | Daemon lifecycle, deadlock/hang behavior, security and ops burden | High | Defer; maybe future substrate |
| CLI-native object reads | Fast for payload/search/display workflows | Does not satisfy arbitrary POSIX shell tools | Low-medium | Excellent complement |
| Hybrid managed cache + explicit CLI | Combines ergonomics with bounded sync | Needs clear cache lifecycle | Medium | Recommended |

Key external filesystem references:

- Linux FUSE docs describe FUSE as a userspace filesystem with a kernel/userspace daemon connection, non-privileged mount concerns, waiting/abort controls, and possible deadlock/hang scenarios. That is a warning sign for this product path: it is powerful, but adds daemon lifecycle and failure semantics that are heavier than the current shell substrate.
- Linux OverlayFS docs describe the lower/upper model, merged directories, whiteouts, copy-up, and delayed data copy-up. That model is conceptually useful for RO/RW semantics, but direct OverlayFS use would introduce privileged mount and host filesystem assumptions.

## Verification

- Used P001 current-path audit as local source of truth.
- Checked primary Linux kernel documentation:
  - FUSE overview: https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse.html
  - OverlayFS documentation: https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html
- Compared against product constraints:
  - stable `/cortex/ro` and `/cortex/rw` paths;
  - same-agent subagents sharing team workspace;
  - shell CLI as the interface surface;
  - explicit identity and tenant boundaries;
  - no unnecessary hidden state.

## Known Gaps

- This comparison does not benchmark real object counts or byte volumes. The implementation plan should add metrics before changing behavior.

## Artifacts

- `novaic-cortex/novaic_cortex/sandbox.py`
- `novaic-cortex/novaic_cortex/blob_store.py`
- FUSE docs: https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse.html
- OverlayFS docs: https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html
