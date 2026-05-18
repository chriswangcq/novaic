# App VMuse copied resource sync discovery ticket

## Problem Definition

App VMuse copied resource/generated trees may ship stale FastMCP/direct media behavior or diverge from source VMuse cleanup candidates.

## Proposed Solution

Scan the two app VMuse copy roots, compare representative copied files with source VMuse, and classify direct media/FastMCP/base64/display hits as copied source residue, current lower-level VMuse transport, or unrelated generated vocabulary.

## Acceptance Criteria

- VMuse app copy files are discovered.
- High-signal direct media/FastMCP hits are classified.
- Required source-to-copy synchronization/remediation candidates are listed.
- No app resource/generated files are modified.

## Verification Plan

Use `rg --files` and focused `rg` under `novaic-app/src-tauri/resources/novaic-mcp-vmuse` and `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`; compare checksums with source VMuse for representative files.

## Risks

- The copies intentionally mirror source VMuse, so findings should state whether source cleanup must be propagated instead of manually editing copies in isolation.

## Assumptions

- The relevant copy roots are the resource and generated Apple asset VMuse directories.
