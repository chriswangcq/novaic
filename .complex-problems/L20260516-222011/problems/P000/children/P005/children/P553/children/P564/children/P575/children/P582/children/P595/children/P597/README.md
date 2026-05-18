# Shell Screenshot CLI BlobRef Manifest Test Coverage

## Problem

Verify shell-facing screenshot/device CLI output is protected by tests that require BlobRef artifact manifests instead of raw base64 terminal text.

## Success Criteria

- Records exact scans for shell/devicectl screenshot BlobRef manifest tests.
- Cites tests proving shell screenshot output contains `tool-output.v1` artifact metadata and BlobRef access instructions.
- Cites tests proving raw screenshot base64 is absent from shell-visible/durable text.
- Creates a concrete follow-up if shell CLI manifest coverage is missing.
