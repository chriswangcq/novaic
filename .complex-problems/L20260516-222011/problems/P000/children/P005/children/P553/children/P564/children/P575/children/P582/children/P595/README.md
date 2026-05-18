# Durable Shell and Display Output Base64 Absence Test Coverage

## Problem

Verify that durable shell/display output tests protect the contract that large visual payloads are represented by BlobRef manifests rather than raw base64 text in durable tool results.

## Success Criteria

- Records exact scans for base64/data-url assertions in shell, display, tool handler, and Cortex projection tests.
- Cites tests proving `devicectl hd screenshot` or equivalent shell-visible screenshot output returns a BlobRef artifact manifest.
- Cites tests proving `display` durable payload stores `image_ref` or display file metadata without inline `data`.
- Creates a concrete follow-up if durable base64 absence is not directly tested.
- Explains why this belongs under the display regression inventory split.
