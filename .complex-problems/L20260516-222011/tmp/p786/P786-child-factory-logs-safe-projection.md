# Child Problem: Factory logs safe payload projection

## Problem

`novaic-llm-factory/static/factory-logs.html` still has detail rendering paths that stringify raw request/response/messages/tool details. This can surface large payloads or base64-like content in the logs UI and mislead future debugging.

## Success Criteria

- Request/response raw JSON detail rendering is bounded or scrubbed before display.
- Message and tool-call renderers project large or media-like values safely rather than dumping raw content.
- The UI still exposes enough metadata for debugging: role, model, status, latency, token counts, tool names, and compact references.
- Focused static checks or lightweight tests prove obvious base64/blob-like payloads are redacted or summarized.
