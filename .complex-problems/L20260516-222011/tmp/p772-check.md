# App resource packaging and generated asset wiring discovery check

## Summary

Success. The resource packaging discovery met its scoped criteria: it found relevant resource/generated asset wiring, classified synchronized stale copies versus packaging drift, listed exact remediation candidates, and did not modify resource files.

## Evidence

- `R753` cites scan artifact `.complex-problems/L20260516-222011/tmp/p772-resource-packaging-scan.txt`.
- `R753` records checksum equality between source resources and generated Apple assets for service config, backend startup script, and representative VMUSE files.
- `R753` records that Tauri desktop/iOS/Android configs bundle `resources/config`, `resources/backends`, and `resources/novaic-mcp-vmuse`.
- `R753` identifies a generated-only `novaic-storage-a` backend binary.
- `R753` identifies `start-backends.sh` expecting `novaic-blob-service` while source resource backends do not include that binary.
- `R753` identifies that VMUSE FastMCP/direct-media residue is bundled via resource and generated asset copies.

## Criteria Map

- Relevant resource packaging and generated asset wiring files discovered: satisfied by bundle configs, resource/gen directories, backend scripts, and service config scans.
- Copied resource/script/config hits classified: satisfied by checksum sync classification and generated-only binary drift classification.
- Remediation candidates listed or absence recorded: satisfied by five explicit candidate groups in `R753`.
- No resource/package wiring files modified: satisfied by `R753`; this child only wrote ledger artifacts.

## Execution Map

- The ticket ran bounded scans over Tauri resource directories, generated Apple assets, Tauri configs, and app scripts.
- It compared representative source resource and generated asset checksums.
- It inspected Tauri bundle mappings and backend resource file lists.
- It recorded result `R753` without making changes.

## Stress Test

- Plausible failure mode: generated assets could be stale even when source resources are fixed. `R753` checks both source and generated paths and finds checksum identity for key text resources plus one generated-only binary drift.
- Plausible failure mode: packaged startup could expect missing services. `R753` finds the mismatch between `novaic-blob-service` expectation and shipped backend binaries.
- Plausible failure mode: VMUSE source cleanup might not reach app bundles. `R753` confirms app bundles include resource/generated VMUSE copies that must be synchronized.

## Residual Risk

- This child did not decide the final desired packaged backend service graph; that belongs to remediation/design work after discovery aggregation.
- Large third-party resource directories were not semantically audited beyond high-signal keyword scans; they are not central to the current shell/blob/display contract problem.

## Result IDs

- R753
