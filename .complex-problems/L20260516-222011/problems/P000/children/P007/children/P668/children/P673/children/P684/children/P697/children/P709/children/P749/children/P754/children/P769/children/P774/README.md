# App factory log and raw JSON detail discovery

## Problem

Discover whether LLM factory logs, Monitor details, and raw JSON views still display or store tool/image payloads in a way that violates the shell-text-plus-BlobRef contract. This belongs under P769 because the user-visible logs recently exposed stale raw/base64 behavior.

## Success Criteria

- Relevant factory log, monitor, raw JSON, request/response detail, and truncation files are discovered with bounded commands.
- Hits for `_mcp_content`, raw JSON, request body, response body, display tool results, base64, Blob refs, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend/log UI files are modified in this discovery child.
