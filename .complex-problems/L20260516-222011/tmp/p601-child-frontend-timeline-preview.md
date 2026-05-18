# Frontend Agent Monitor Timeline Preview Boundary

## Problem

Audit frontend agent monitor/timeline rendering to ensure displayed tool outputs are escaped/truncated human previews and not assumed to be LLM request context.

## Success Criteria

- Records exact scans for monitor timeline, tool result, modal/detail, truncation, and base64/image rendering.
- Cites frontend slices showing truncation/escaping or artifact-specific rendering.
- Separates UI presentation from actual LLM context.
- Creates a follow-up if frontend renders raw unredacted image bytes from tool text.
