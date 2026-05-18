# App message media and Blob renderer discovery

## Problem

Discover whether the chat/message UI and media renderer still expects raw base64 image/audio payloads instead of BlobRefs/artifact manifests. This belongs under P769 because message rendering is where users should see files/images rather than raw tool payloads.

## Success Criteria

- Relevant chat/message/media renderer files are discovered with bounded commands.
- Hits for base64, data URLs, image rendering, attachments, Blob refs, display, and artifact manifests are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend files are modified in this discovery child.
