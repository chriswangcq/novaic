# VMuse service residue discovery

## Problem

Scan VMuse service/MCP code for stale direct media exposure, raw screenshot/base64 stdout, fallback/compatibility, or ownership wording that conflicts with the current shell Blob artifact + display perception boundary. This belongs under P757 because VMuse lower-level protocols may handle media bytes but must not leak them as active shell/LLM text.

## Success Criteria

- VMuse source files are discovered and scanned with bounded commands.
- Suspicious hits are classified as current lower-level media protocol, shell artifact boundary, stale residue, or unrelated vocabulary.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.
