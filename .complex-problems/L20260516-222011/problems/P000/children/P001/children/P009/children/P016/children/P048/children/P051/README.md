# Child Problem: display and LLM image projection avoids text base64

## Problem

The display/image path must not serialize image bytes as text inside LLM messages. When an image artifact is loaded for model perception, context assembly should use the provider's native image/multimodal content shape or a compact artifact reference, not a text blob containing base64.

## Success Criteria

- Display tool observations returned to text history remain concise and do not include image base64.
- LLM request assembly for displayed images uses model-native image content or the intended non-text image representation.
- Focused tests or request-shape inspections prove no `role=tool` text message contains display base64.
