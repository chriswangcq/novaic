# App shell artifact output UI contract discovery

## Problem

Discover whether the frontend assumes shell tool output contains rich JSON/media payloads instead of terminal text plus optional artifact/blob manifests. This belongs under P769 because the shell contract changed and UI affordances must not encourage raw payload exposure.

## Success Criteria

- Relevant shell/tool output, artifact manifest, monitor timeline, and tool-call UI files are discovered with bounded commands.
- Hits for `tool-output.v1`, artifacts, Blob refs, shell stdout, truncation, display, and media preview are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend UI files are modified in this discovery child.
