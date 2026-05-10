# RO/RW Auto Mount Optimization Research Result

## Summary

Completed the design research. Current shell execution is correct but expensive because it repeatedly builds disposable RO/RW temp trees. The recommended optimization is a staged hybrid: metrics first, then explicit mount profiles, then manifest/delta sync, then a per-agent local object cache, then selective hydration. FUSE/OverlayFS are deferred as future options, not first implementation substrates.

## Done

- P001 / R000 audited the current Runtime -> Cortex -> Sandbox shell path.
- P002 / R001 compared optimization models and identified the hybrid cache/profile approach as the best fit.
- P003 / R002 produced the detailed staged architecture and follow-up implementation tickets.

## Verification

- Each child problem passed its own success check:
  - P001 / C000: current path audit complete.
  - P002 / C001: optimization model comparison complete.
  - P003 / C002: recommended design complete.
- The final design maps directly to root success criteria:
  - repeated work identified;
  - slowdown causes explained;
  - optimization models compared;
  - staged architecture recommended;
  - correctness constraints listed;
  - follow-up tickets defined.

## Known Gaps

- none for the research/design pass.
- Implementation and benchmarking are intentionally deferred to follow-up tickets.

## Artifacts

- `.complex-problems/rorw-audit-current-path-result.md`
- `.complex-problems/rorw-optimization-options-result.md`
- `.complex-problems/rorw-recommended-design-result.md`
- FUSE documentation: https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse.html
- OverlayFS documentation: https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html
