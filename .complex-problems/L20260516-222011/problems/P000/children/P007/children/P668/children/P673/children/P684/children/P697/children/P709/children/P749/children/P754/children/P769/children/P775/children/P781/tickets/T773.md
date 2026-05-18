# App BlobRef and artifact preview contract discovery ticket

## Problem Definition

App image/file preview paths may still rely on raw base64/data URLs, direct file bytes, or shell stdout media payloads instead of resolving BlobRefs/artifact references through the Blob/Gateway-backed cache path. That would violate the shell terminal-text plus artifact-manifest contract.

## Proposed Solution

Discover BlobRef attachment, authenticated image, image preview, file upload/download, and artifact-related UI code/tests under `novaic-app/src` and `novaic-app/src-tauri/src`. Inspect whether previews/downloads resolve `blob://` references through the intended cache/fetch path and whether any legacy from-base64/data URL paths remain.

## Acceptance Criteria

- Blob attachment, authenticated image, image preview, file upload/download, and artifact-related UI files/tests are discovered.
- Hits for `blob://`, artifact manifests, image preview, base64/data URLs, direct file bytes, display integration, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No BlobRef/artifact preview UI files are modified.

## Verification Plan

Use bounded `rg --files` and focused `rg -n -i` scans under `novaic-app/src`, `novaic-app/src-tauri/src`, and app tests. Inspect high-signal source slices and run relevant blob/attachment tests if lightweight.

## Assumptions

- BlobRef rendering is correct when the UI passes `blob://...` to the Rust cache/fetch path and uses browser object URLs for display.
- Tiny built-in placeholders/fallbacks should be classified separately from runtime media payload transport.

## Risks

- Tauri/Rust file commands may include lower-level byte fetch logic; classify data-plane bytes separately from UI-visible raw payload leakage.
