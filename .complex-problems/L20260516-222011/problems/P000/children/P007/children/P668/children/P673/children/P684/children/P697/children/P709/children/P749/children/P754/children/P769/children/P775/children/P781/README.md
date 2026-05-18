# App BlobRef and artifact preview contract discovery

## Problem

Discover whether App image/file preview and BlobRef handling surfaces treat artifacts as references resolved through Blob/Gateway, instead of embedding raw base64/data URLs or assuming shell stdout contains displayable media bytes. This belongs under `P775` because shell now emits terminal text plus artifact manifests, and preview affordances must consume those references safely.

## Success Criteria

- Blob attachment, authenticated image, image preview, file upload/download, and artifact-related UI files/tests are discovered with bounded commands.
- Hits for `blob://`, artifact manifests, image preview, base64/data URLs, direct file bytes, display integration, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No BlobRef/artifact preview UI files are modified in this discovery child.
