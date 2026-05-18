# P619 UI/Test Multimodal Residue Classification

## UI Runtime Uses

- WebRTC cursor `rgba_base64 -> canvas -> data:image` is intentional device cursor rendering and not artifact/tool-output display.
- Chat/assistant image rendering uses BlobRef/authenticated URLs and overlay preview; covered by P611.
- SmartValue only treats `blob://` and HTTP(S) image URLs as image previews, not `data:image`.

## Test Guard Uses

- ActivityTimeline tests intentionally include raw `data:image` and JPEG-like base64 to assert monitor detail redaction.
- Runtime/Cortex tests intentionally include `image_ref`, `display_perception`, and historical replay cases to assert current-turn-only media injection.
- Factory tests intentionally include provider image data to assert log redaction.

## Risky Residue

- No risky UI/test multimodal compatibility residue found.
