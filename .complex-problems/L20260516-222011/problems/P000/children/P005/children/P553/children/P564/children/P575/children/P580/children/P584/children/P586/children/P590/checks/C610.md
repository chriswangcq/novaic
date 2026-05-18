# P590 Check

## Summary

Success. Runtime now resolves current-round display `image_ref` entries into image MCP content before multimodal provider conversion, and it does not fetch refs for history projection.

## Strict Review

- Resolution is gated on `projection == "display_perception"` inside `expand_step_ref_to_content`.
- History projection explicitly remains unresolved and does not call Blob Service.
- Failure fallback is bounded text, not a crash and not hidden base64.
- The existing multimodal conversion remains responsible for moving image data out of tool text and into provider-native user image messages.
- Updated tests prove current-round display reaches image content while historical replay does not inject old images.

## Stress Test

Checked three edge paths:

- current display BlobRef resolves to base64 image MCP content,
- old/history display BlobRef stays as `image_ref` and never fetches,
- Blob Service 404 becomes a text diagnostic.

## Residual Risk

The resolver uses runtime's service config and internal HTTP client as the IO boundary. Broader cleanup/verification still needs to run all display-related tests and searches, and unrelated session-generation failures in the larger PR-71 test file remain outside this display resolver ticket.
