# PR-138: Route audio attachments toward `audio_qa`

## Status

`[deployed]`

## Background

After PR-136 and PR-137, the tool exists and is visible, but user-uploaded audio attachments still render as generic files in LLM context. The model needs an explicit, non-ambiguous hint that audio attachments should be inspected with `audio_qa`, not `display`.

## Scope

- Update `user_content_to_llm` so audio MIME types are rendered with an `audio_qa(file_url=..., prompt=...)` hint.
- Preserve the existing image -> `display` hint.
- Keep generic non-image/non-audio files generic.
- Add tests for audio, image, and generic file hints.

## Non-goals

- Do not inline audio base64 into the user message.
- Do not auto-run `audio_qa`; the LLM still decides when to call the tool.
- Do not change chat message storage shape.

## Unit Tests

- Audio attachment produces an `audio_qa` hint.
- Image attachment still produces a `display` hint.
- Generic attachment remains generic and does not mention `audio_qa`.

## Smoke Test

- Send or simulate a user message with an audio attachment.
- Confirm the assembled LLM user content contains the `audio_qa` hint.
- After deploy, send an audio attachment smoke and confirm the LLM tool list plus message hint make the tool callable.

## Deployment Checklist

- [x] Unit tests pass locally.
  - `cd novaic-agent-runtime && python -m pytest tests/unit/task_queue/test_user_content.py tests/unit/task_queue/test_tool_handlers_display_chat_history.py tests/test_im_rendering.py -q`
- [x] Commit Runtime changes.
  - `2f99cc7 feat(runtime): route audio attachments to audio qa`
- [x] Push Runtime branch.
- [x] Deploy Runtime.
  - Deployed as part of `./deploy services` on 2026-05-01.
- [x] Production smoke: audio attachment appears in assembled LLM context with `audio_qa` hint.
  - Local smoke confirmed audio attachment renders an `audio_qa(...)` hint
    using the attachment's BlobRef.
  - Production tools smoke confirmed `audio_qa` is available to the LLM after deploy.
- [x] Update this ticket and parent submodule pointer.

## GitHub / Merge

- Depends on PR-136 and PR-137.
- Suggested commit message: `feat(runtime): route audio attachments to audio qa`
