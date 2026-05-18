# Result: Extracted service entrypoint discovery scan

## Summary

Completed read-only discovery for extracted service entrypoints and launch references. Artifacts were written under `.complex-problems/L20260516-222011/tmp/p695` and cover file-path candidates, launch/config/package-script references, package scripts, and a per-service evidence matrix.

## Done

- Built `all-files.txt` using repository-wide file enumeration with noisy generated/dependency paths excluded.
- Built `candidate-service-files.txt` for service-name path candidates.
- Built `launch-reference-scan.txt` for launch/config/entrypoint/service-name references.
- Built `package-scripts.txt` from all package manifests.
- Built `service-evidence-matrix.md` with per-service candidate path and launch-reference counts and slices.
- Built `scan-summary.md` with aggregate counts and required-service presence.

## Verification

`scan-summary.md` reports required service evidence counts. The scan found evidence for Blob, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, devicectl, and agentctl. LogicalFS appears under both `logicalfs` and `logical-fs` patterns, with evidence captured for later classification.

## Gaps

This is discovery evidence only. It intentionally does not decide active vs stale for every match and does not patch code. Boundary classification and cleanup remain for sibling problems P696, P697, and P698.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p695/scan-commands.md`
- `.complex-problems/L20260516-222011/tmp/p695/all-files.txt`
- `.complex-problems/L20260516-222011/tmp/p695/candidate-service-files.txt`
- `.complex-problems/L20260516-222011/tmp/p695/launch-reference-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p695/package-scripts.txt`
- `.complex-problems/L20260516-222011/tmp/p695/service-evidence-matrix.md`
- `.complex-problems/L20260516-222011/tmp/p695/scan-summary.md`
