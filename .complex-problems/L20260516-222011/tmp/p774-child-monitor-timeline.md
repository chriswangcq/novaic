# App monitor timeline payload projection discovery

## Problem

Discover whether Agent Monitor timeline/detail rendering still exposes raw tool payloads, `_mcp_content`, base64 media, or stale display output instead of projected shell text and BlobRef/artifact manifests. This belongs under P774 because Monitor cards and detail drawers are a separate user-visible path from the factory-log page.

## Success Criteria

- Monitor/timeline files and tests are discovered with bounded commands.
- Hits for `_mcp_content`, tool output, display results, base64/data URLs, BlobRefs, artifacts, truncation, and projection helpers are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No monitor/timeline UI files are modified in this discovery child.
