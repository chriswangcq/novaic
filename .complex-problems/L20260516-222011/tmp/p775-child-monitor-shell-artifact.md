# App monitor shell artifact projection discovery

## Problem

Discover whether Agent Monitor / ActivityTimeline surfaces project shell outputs and artifact manifests safely, without exposing raw shell-rich JSON, `_mcp_content`, raw artifact payloads, base64/data URLs, or implementation-only fields. This belongs under `P775` because Monitor is the other high-visibility surface for shell/tool output.

## Success Criteria

- Monitor, ActivityTimeline, activity hook/type, and guard test files are discovered with bounded commands.
- Hits for shell actions, tool output details, `tool-output.v1`, artifacts, Blob refs, truncation, raw payload hiding, and display/media preview are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Monitor UI files are modified in this discovery child.
