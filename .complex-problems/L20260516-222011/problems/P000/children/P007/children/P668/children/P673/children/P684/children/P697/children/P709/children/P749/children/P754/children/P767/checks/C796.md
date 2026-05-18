# App VMuse copied resource sync discovery check

## Summary

Success. The discovery child solved its scoped problem: it found the app VMuse resource/generated copy roots, classified the high-signal media/FastMCP/base64/display hits, proved source-to-copy synchronization state with checksum comparison, and did not modify app copy files. The stale direct media behavior remains a remediation candidate for the later cleanup phase, not a failure of this discovery-only child.

## Evidence

- `R750` records the two discovered copy roots:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`
- Scan artifact `.complex-problems/L20260516-222011/tmp/p767-vmuse-copy-scan.txt` contains focused file discovery and high-signal `rg` hits for FastMCP, ImageContent, base64, screenshot, display, blob, tool-output, and HTTP server terms.
- The checksum comparison in the scan artifact reports representative files as byte-identical between source VMuse and both app copy trees.
- `R750` explicitly classifies stale direct MCP image content as copied source residue, while lower-level VMuse HTTP/base64 transport is not classified as the stale LLM-context path.
- `R750` states no app resource/generated files were modified.

## Criteria Map

- VMuse resource/generated copy files discovered: satisfied by the two copy roots and file list in `p767-vmuse-copy-scan.txt`.
- Direct media/FastMCP/base64/display hits classified: satisfied by `R750` separating FastMCP/ImageContent direct media residue from lower-level HTTP/base64 transport.
- Required source-to-copy synchronization/remediation candidates listed: satisfied by the eight explicit source/copy propagation targets in `R750`.
- No app resource/generated files modified: satisfied by `R750`; this was a read-only discovery child.

## Execution Map

- The one-go ticket used bounded `rg --files`, focused `rg -n -i`, and a checksum comparison script scoped to app VMuse copy roots and source VMuse.
- The result captured the discovered evidence and did not perform remediation work, matching the discovery-only ticket boundary.
- No child work was required because this child only needed to discover and classify app copy state.

## Stress Test

- Plausible failure mode: app copies could have diverged from source VMuse, causing source cleanup to miss packaged behavior. The checksum comparison covered representative entrypoint, CLI, server, package, and launcher files and found them identical, so the remediation target is synchronization from source cleanup into both copies rather than an independent app-only drift.
- Plausible failure mode: base64 hits could be over-classified as stale. The check distinguishes lower-level VMuse HTTP/file transport base64 from direct MCP ImageContent LLM-context exposure.

## Residual Risk

- This child did not modify or test app packaging. That is acceptable because the problem was discovery-only under P754. The later remediation phase must remove or hard-disable stale FastMCP direct media paths in source and copied VMuse trees and verify packaging behavior.

## Result IDs

- R750
