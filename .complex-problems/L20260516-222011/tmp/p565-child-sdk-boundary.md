# Sandbox SDK Client Boundary Residue

## Problem

Audit `novaic-sandbox-sdk` and runtime call sites to confirm clients talk to sandboxd/service instead of direct legacy process execution or host path manipulation.

## Success Criteria

- Records exact scans for SDK client, exec/session API, base64 wire decoding, fallback/local paths, and runtime call sites.
- Cites SDK/runtime slices.
- Runs focused SDK tests and runtime shell output tests.
- Creates follow-up if active runtime bypasses sandboxd.
