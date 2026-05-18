# P194 Check: runtime-to-factory multimodal request preservation

## Summary

Success. R177 solves P194: runtime's outbound Factory request now has a focused regression proving structured `image_url` content is preserved and base64 does not leak into ordinary text fields.

## Evidence

- Transport path mapped from handler to factory client.
- `FactoryLLMClient.chat` builds `payload["messages"] = messages` and posts it with `json=payload`.
- New test `test_factory_client_preserves_structured_image_content` captures the outbound payload at the client boundary.

## Criteria Map

- Runtime LLM transport/request builder is mapped: satisfied by R177's handler/business/client map.
- Structured `image_url` content is preserved in the Factory request: satisfied by the new outbound payload assertion.
- Base64 image bytes do not appear in ordinary text content fields: satisfied by recursive text-field assertion.
- Focused runtime tests pass: `10 passed in 0.09s`.

## Execution Map

- T182 was executed as a bounded runtime transport-boundary audit.
- One regression test was added because prior coverage stopped before the factory client request boundary.

## Stress Test

- The test uses a data URL image and a sibling text item in one user content array, then asserts the image remains a structured `image_url` item instead of becoming text.

## Residual Risk

- Factory/provider downstream handling is still P195 and is not judged here.

## Result IDs

- R177
