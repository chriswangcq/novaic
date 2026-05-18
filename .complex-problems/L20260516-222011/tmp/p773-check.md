# App message media and Blob renderer discovery check

## Summary

Success. The discovery child is scoped to chat/message/media rendering, and R755 supplies bounded evidence that the current message/media renderer uses BlobRef/cache/object-URL flows rather than raw tool media payloads. The one-go path is acceptable here because no code was modified, the inspected surface is narrow, and the scan explicitly classified suspicious hits instead of ignoring them.

## Evidence

- R755 records the relevant frontend files discovered by bounded `rg --files` and focused `rg -n -i` scans.
- `.complex-problems/L20260516-222011/tmp/p773-message-media-scan.txt` includes the search terms and high-signal hit list for BlobRefs, attachments, base64/data URLs, display, artifacts, and images.
- `novaic-app/src/services/fileUpload.ts` requires returned upload locators to start with `blob://`.
- `novaic-app/src/application/blobAttachmentPath.test.ts` guards against legacy base64 attachment paths and FileReader/data URL upload patterns.
- `novaic-app/src/components/hooks/useAuthenticatedImage.ts`, `novaic-app/src/components/Chat/FileAttachment.tsx`, and `novaic-app/src/components/Chat/Markdown.tsx` show image display is loaded through cached bytes/object URLs from BlobRefs rather than inline LLM/tool payload text.
- Suspicious remaining base64/data URL hits were classified as silent audio fallback, WebRTC cursor rendering, or ActivityTimeline binary scrubbing.

## Criteria Map

- Relevant chat/message/media renderer files discovered: satisfied by the scan artifact and targeted file inspection.
- Hits for base64, data URLs, image rendering, attachments, Blob refs, display, and artifact manifests classified: satisfied by R755 Verification and Known Gaps sections.
- Exact remediation candidates listed, or absence recorded: satisfied; R755 explicitly records no remediation candidate in this slice.
- No frontend files modified: satisfied; R755 states no frontend files were modified and this was a discovery-only child.

## Execution Map

- T765 was classified as `one_go`, executed as a bounded discovery scan, and recorded as R755.
- No split, spawned child, or follow-up was needed for P773 because evidence covers the scoped message/media renderer surface.
- Broader factory log/raw JSON and shell artifact UI work remains correctly delegated to sibling problems P774 and P775, not hidden under this child.

## Stress Test

- Plausible failure mode: a raw base64 image path could hide in frontend rendering under a generic media or monitor component. The scan included broad terms (`base64`, `data:image`, `blob://`, `artifact`, `attachment`, `display`, `_mcp_content`) across `novaic-app/src`, then classified high-signal hits instead of relying only on chat component names.
- Plausible false positive: object URLs and data URLs may be legitimate browser rendering mechanics. The check accepts them only where they are frontend-local render/cache behavior and not LLM/tool context propagation.

## Residual Risk

- Non-blocking: this child did not inspect factory log raw JSON detail or shell artifact timeline projection; those are separate open sibling problems.
- Non-blocking: future code could reintroduce raw media payloads, but existing attachment tests and the discovered BlobRef rendering path provide local guardrails.

## Result IDs

- R755
