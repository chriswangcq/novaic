# P779 success check

## Summary

Success for discovery. `R760` covers the chat shell-output rendering surface with bounded scans, source inspection, and focused tests. It does not claim the codebase is fully optimized: it identifies one concrete cleanup candidate in `AssistantMessage.tsx` legacy event rendering.

## Evidence

- `R760` inspected chat rendering, message conversion, attachment rendering, Markdown images, Blob upload, and type contracts.
- `parseMessageContent` only accepts canonical `{text, attachments}` envelopes and ignores retired raw string content.
- `useMessages` does not populate legacy `events` or `toolCalls`, so current Chat rows are not rendering shell stdout/tool-output JSON directly.
- File/image/audio attachments are BlobRef-based and existing tests guard against base64 upload regressions.
- Focused tests passed: `converters.test.ts`, `blobAttachmentPath.test.ts`, and `chatMessageContract.test.ts`.

## Criteria Map

- Chat message, Markdown, attachment, converter, and tool-result display files are discovered: satisfied by the bounded scan and source slices.
- Hits for shell stdout, `tool-output.v1`, artifacts, Blob refs, display output, base64/data URLs, and truncation are classified: satisfied by the active message path, BlobRef attachment path, Markdown/FileAttachment image loading, and legacy event classification.
- Exact remediation candidates are listed, or absence is explicitly recorded: satisfied by the `AssistantMessage.tsx` legacy event-rendering cleanup candidate and the explicit absence of active shell-rich payload parsing in Chat.
- No chat UI files are modified: satisfied; only ledger/tmp artifacts were added.

## Execution Map

- `T771` was a one-go discovery ticket after parent-level split narrowed the surface to Chat.
- Execution included bounded search, source inspection, and focused unit tests.
- Result `R760` records both active-path compliance and residual risk.

## Stress Test

- Could Chat still display images? Yes, through BlobRef-backed attachments and Markdown image URLs resolved by `useAuthenticatedImage`; this is intended.
- Could raw shell JSON in the message content render directly? Active converter behavior rejects raw string content and only accepts `{text, attachments}` envelopes.
- Could future code misuse legacy events? Yes; `AssistantMessage.tsx` still contains event-based raw object/image rendering. This is a real cleanup candidate for parent optimization.

## Residual Risk

The discovery is complete, but implementation should remove or strictly narrow `AssistantMessage.tsx` legacy event rendering to prevent future accidental reactivation of rich/raw event payload rendering.

## Result IDs

- `R760`
