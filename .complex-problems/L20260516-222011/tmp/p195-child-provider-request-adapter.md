# Factory provider request adapter media preservation

## Problem

Audit Factory's provider request adapter so structured image content from runtime is sent to the provider API in the correct schema instead of being dropped, stringified, or flattened.

## Success Criteria

- Locate Factory provider adapter/client modules.
- Prove OpenAI-compatible `image_url` content survives to the provider request.
- Prove raw base64 is not moved into text fields.
- Add or verify focused adapter tests.

