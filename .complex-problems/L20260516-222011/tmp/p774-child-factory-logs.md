# App factory logs page and detail discovery

## Problem

Discover whether the LLM factory logs page, list query, detail modal, and request/response JSON rendering still expose raw tool payloads, `_mcp_content`, base64 media, or unprojected display results. This belongs under P774 because factory logs are the user-visible place where raw request/response JSON recently looked wrong.

## Success Criteria

- Factory-log page, hook/service, table, detail modal, and API-client files are discovered with bounded commands.
- Hits for request body, response body, raw JSON, `_mcp_content`, base64, BlobRefs, artifacts, display results, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No factory-log UI files are modified in this discovery child.
