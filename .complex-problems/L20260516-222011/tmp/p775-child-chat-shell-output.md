# App chat shell output rendering discovery

## Problem

Discover whether chat-facing UI renders shell tool output as terminal text plus attachments/artifact manifests, or whether it still expects shell stdout/tool results to contain rich JSON/media payloads. This belongs under `P775` because chat is the primary user-visible surface for shell output contract violations.

## Success Criteria

- Chat message, Markdown, attachment, converter, and tool-result display files are discovered with bounded commands.
- Hits for shell stdout, `tool-output.v1`, artifacts, Blob refs, display output, base64/data URLs, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No chat UI files are modified in this discovery child.
