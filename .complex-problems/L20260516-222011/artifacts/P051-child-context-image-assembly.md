# Child Problem: LLM context assembly preserves displayed images as images

## Problem

After `display(blob://...)`, the next LLM request must contain the displayed image as model-visible image content, not just an `OK` text marker and not a base64 blob inside a text message. The context assembly layer is responsible for preserving the semantic image reference into the model call.

## Success Criteria

- A displayed image artifact becomes model-visible image content in the assembled request.
- The assembled request does not put image bytes into `role=tool` text content.
- Focused tests inspect the actual assembled message/request shape.
