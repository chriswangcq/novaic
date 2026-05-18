# Sandbox LogicalFS Blob Service Call Path Map Check

## Summary

P560 is successful. R550 maps sandbox/logicalfs/blob service-side direction with source evidence and correctly defers adapter-risk classification to P553/P561.

## Evidence

- R550.
- `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-boundary-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-counts.md`
- `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-slices.txt`

## Criteria Map

- Scans sandbox/logicalfs/blob service roots: satisfied by boundary scan.
- Reads high-signal service/core files: satisfied by source slices and R550.
- Explains sandbox/logicalfs/blob direction: satisfied by R550.
- Records suspicious adapter paths for P553/P561: satisfied, `BlobObjectStore` is explicitly deferred.

## Execution Map

- Ran broad keyword scan over sandbox service, sandbox SDK, and LogicalFS.
- Read sandbox service entrypoint/process/mount namespace files.
- Read LogicalFS local provider and blob object store files.
- Recorded R550.

## Stress Test

- False cleanup risk: result does not delete or condemn `BlobObjectStore`; it records it as below-LogicalFS adapter to classify later.
- Missing sandbox fallback risk: source slices show sandboxd is execution/mount service, not alternate LogicalFS authority.
- One-go skepticism: this was read-only mapping with no code changes.

## Residual Risk

This child does not classify every scan hit; P553/P561 own residue classification.

## Result IDs

- R550
