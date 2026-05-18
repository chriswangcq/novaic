# LogicalFS Sandbox Blob Call Path Map Result

## Summary

P557 call-path mapping is complete. Current layering direction is: Cortex owns Workspace semantics and adapts them to LogicalFS; LogicalFS owns generic snapshot/materialize/diff mechanics; sandboxd owns process execution and bind-mounting; blob owns cheap payload/artifact/object bytes below semantic layers. Two residue items are explicitly passed to P553: `Workspace.materialize()` and `BlobObjectStore` exposure/usage boundary.

## Done

- Closed P559 Cortex boundary call path map with R549 / C583.
- Closed P560 sandbox/logicalfs/blob service call path map with R550 / C584.
- Closed P561 artifact/display blob usage map with R551 / C585.

## Verification

- Cortex shell path has no local execution fallback: `Sandbox` requires sandboxd executor and `MountNamespaceLogicalFS`.
- Sandboxd is process/mount execution service, not LogicalFS semantic owner.
- LogicalFS local provider materializes explicit snapshots and observes RW patches.
- Blob usage is intended for runtime/user artifacts, Cortex large payloads, and object-store bytes below LogicalFS.
- Suspicious/classification items are not hidden:
  - `Workspace.materialize()` writes external bytes into `/rw/scratch`.
  - `BlobObjectStore` uses RO/RW-like object keys below LogicalFS and must not become a semantic Workspace API from higher layers.

## Known Gaps

- This result maps call paths but does not remediate. P553/P554/P555 own residue inventory, remediation, and final verification.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p559-result.md`
- `.complex-problems/L20260516-222011/tmp/p560-result.md`
- `.complex-problems/L20260516-222011/tmp/p561-result.md`
