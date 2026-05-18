# App frontend and Monitor output contract discovery

## Problem

Discover whether app frontend/Monitor/log UI code still expects or renders raw base64/media payloads, old tool result JSON, or stale shell/display contracts. This belongs under P754 because the frontend is where tool-output and LLM-log contract drift becomes visible to users.

## Success Criteria

- Relevant frontend/Monitor/log/UI files are discovered with bounded commands.
- Suspicious hits around tool output, display, image/base64 payloads, artifact manifests, Blob refs, shell output, and factory logs are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend/app UI files are modified in this discovery child.
