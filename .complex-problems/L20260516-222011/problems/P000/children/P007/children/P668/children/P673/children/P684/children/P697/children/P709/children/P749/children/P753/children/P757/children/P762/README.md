# Blob service residue discovery

## Problem

Scan Blob service code for stale local fallback, compatibility, direct file-server bypass, raw payload/base64, or ownership wording that conflicts with Blob as the cheap durable file/object service. This belongs under P757 because Blob is the lower file storage layer in the current architecture.

## Success Criteria

- Blob service source files are discovered and scanned with bounded commands.
- Suspicious hits are classified as current object-server behavior, adapter boundary, stale residue, or unrelated vocabulary.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.
