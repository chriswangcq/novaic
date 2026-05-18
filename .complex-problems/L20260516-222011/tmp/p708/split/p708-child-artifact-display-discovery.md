# Artifact/display/context projection discovery

## Problem

Discover how screenshot/artifact outputs flow through shell output, Blob/artifact manifests, display, LLM request construction, and Cortex/Runtime context history. This belongs under P708 because previous failures involved base64 leaking into context or display not projecting media to the LLM correctly.

## Success Criteria

- Shell/tool output contract for screenshots/artifacts is identified.
- Blob/artifact URI and manifest-only history behavior are identified.
- Display tool output and LLM image projection path are identified.
- Cleanup candidates are listed for any active path that still embeds large media bytes as text.
