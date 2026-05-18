# App chat shell output rendering discovery ticket

## Problem Definition

Chat-facing UI may still render shell tool output or display-tool results as rich JSON/media content instead of terminal text plus BlobRef/artifact references. This can cause the chat to expose raw payload envelopes or fail to show artifact-backed media in the intended way.

## Proposed Solution

Discover chat message rendering, Markdown rendering, attachment conversion, image/file preview, and chat-specific guard tests under `novaic-app/src`. Inspect high-signal files for shell stdout handling, `tool-output.v1`, artifact manifests, BlobRefs, display output, raw base64/data URLs, and truncation behavior.

## Acceptance Criteria

- Chat message, Markdown, attachment, converter, and tool-result display files are discovered.
- Hits for shell stdout, `tool-output.v1`, artifacts, Blob refs, display output, base64/data URLs, and truncation are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No chat UI files are modified.

## Verification Plan

Use bounded `rg --files` and focused `rg -n -i` scans under `novaic-app/src/components/Chat`, `novaic-app/src/application`, and chat-related tests/types. Inspect source slices for high-signal matches and run existing targeted tests only if they are directly relevant and lightweight.

## Assumptions

- Chat UI should display human-authored text and attachment cards/previews, not parse arbitrary shell stdout into rich media.
- BlobRef/image rendering is legitimate when driven by attachments or explicit preview components.

## Risks

- Some shell output appears in chat only after the agent sends a reply through IM; avoid misclassifying normal assistant text as tool output.
