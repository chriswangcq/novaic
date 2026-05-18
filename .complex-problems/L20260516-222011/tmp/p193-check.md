# P193 Check: active-stack-after-display media preservation

## Summary

Success. R175 solves P193: the runtime preserves display media through sanitize/multimodal conversion even when a system active-stack message follows the display tool result, while the tool result itself is placeholder-only.

## Evidence

- `sanitize_context` explicitly preserves `_projection` on tool messages until multimodal conversion.
- `process_multimodal_messages` converts only `_projection == "display_perception"` tool messages into separate user image messages.
- `result_to_text_only` replaces image data in the tool message with a placeholder.
- The focused regression `test_prepare_llm_call_injects_display_step_image_before_following_system` covers the exact ordering.

## Criteria Map

- Context/multimodal media extraction code is mapped: satisfied by R175's map of `context.py` and `multimodal.py`.
- Display media survives with following active-stack system message: satisfied by the prepared message order `assistant`, `tool`, `user`, `system`.
- Display tool message is placeholder-only and contains no raw base64: satisfied by assertions that the image placeholder has no `data`.
- Converted message order is deterministic and keeps following system message: satisfied by the exact order assertion and final system role assertion.
- Focused runtime tests pass: `9 passed in 0.08s`.

## Execution Map

- T180 was executed as one bounded ordering/media-preservation audit.
- No code changes were needed because the regression already covered the suspected failure mode.

## Stress Test

- The stress case is exactly the user-observed shape: a display tool result is followed by a system active-stack message. The test proves the image is inserted before the following system message rather than lost or downgraded.

## Residual Risk

- P193 does not validate the provider/factory request serializer. That remains open under P190.

## Result IDs

- R175
