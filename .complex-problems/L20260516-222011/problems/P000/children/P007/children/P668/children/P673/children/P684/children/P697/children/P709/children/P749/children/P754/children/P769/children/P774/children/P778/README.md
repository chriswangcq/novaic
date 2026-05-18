# App raw JSON and truncation primitives discovery

## Problem

Discover whether shared raw JSON, smart value, truncation, sanitization, and binary-detection primitives can still leak raw tool/media payloads into user-visible detail views. This belongs under P774 because these primitives may be reused by factory logs, monitor details, and future debugging surfaces.

## Success Criteria

- Shared JSON/value/truncation/sanitization primitives are discovered with bounded commands.
- Hits for raw JSON, pretty-printing, copy/detail rendering, `_mcp_content`, base64/data URLs, BlobRefs, artifacts, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No shared UI primitive files are modified in this discovery child.
