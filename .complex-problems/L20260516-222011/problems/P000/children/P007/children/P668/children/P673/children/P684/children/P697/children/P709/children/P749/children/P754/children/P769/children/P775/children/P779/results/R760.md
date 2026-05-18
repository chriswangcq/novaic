# App chat shell output rendering discovery result

## Summary

Chat's active message path is contract-compliant: `useMessages` converts Entangled message rows through `parseMessageContent`, which accepts only canonical `{text, attachments}` envelopes, renders text through Markdown, and renders files/images/audio from BlobRef-backed attachments. Focused tests for converters, Blob attachment path, and chat message contract pass. However, `AssistantMessage.tsx` still contains a legacy event renderer that can stringify nested event object content and render event-provided image URLs. That path is not wired by the active `useMessages` conversion today, but it is dangerous residue and should be deleted or narrowed.

## Done

- Scanned Chat, application converter, message type, upload, attachment, Markdown, and preview files for shell/artifact/media/raw-payload terms.
- Inspected `useMessages.ts`, `converters.ts`, `AssistantMessage.tsx`, `Markdown.tsx`, `FileAttachment.tsx`, `useAuthenticatedImage.ts`, type contracts, and Blob upload guards.
- Ran focused app tests for chat message content parsing and BlobRef attachment paths.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p779-chat-shell-output-scan.txt`.
- `novaic-app/src/components/hooks/useMessages.ts` maps Entangled `MessageEntity` rows to view models via `parseMessageContent`, passing only `content` text and `attachments`; it does not populate `events` or `toolCalls`.
- `novaic-app/src/application/converters.ts` parses only canonical object/JSON envelopes with `text` or `attachments`; raw string content returns empty text.
- `novaic-app/src/services/fileUpload.ts` uploads chat files through Blob direct multipart and returns `blob_ref` / `url` metadata.
- `novaic-app/src/components/Chat/FileAttachment.tsx` and `Markdown.tsx` render images through `useAuthenticatedImage` and Tauri cached bytes, not inline base64 payload strings.
- `novaic-app/src/components/Chat/AssistantMessage.tsx` has legacy `events` handling and `extractContent` can `JSON.stringify(content)` when event data contains object content; `image` events can render `image_url` / `image_path`.
- Focused tests passed: `cd novaic-app && npm run test:unit -- converters.test.ts blobAttachmentPath.test.ts chatMessageContract.test.ts` => 3 files, 7 tests passed.

## Known Gaps

- Remediation candidate: remove or strictly narrow legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx` because the active message store does not populate it and it can reintroduce raw object/image-url rendering if reused.
- No active Chat message path was found that parses shell stdout or `tool-output.v1` as rich media payloads.
- No chat UI files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p779-chat-shell-output-scan.txt`
- Focused test output from `novaic-app` unit run.
