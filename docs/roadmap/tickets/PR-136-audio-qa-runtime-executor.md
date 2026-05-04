# PR-136: Port `audio_qa` to the Runtime native executor

## Status

`[deployed]`

## Background

`audio_qa` used to be a real capability in the retired `novaic-tools-server`. The restored Runtime executor now works through Blob Service, resolves the agent audio model config, sends an OpenAI-compatible `input_audio` payload through LLM Factory, and returns the answer/transcription.

After Tools Server was deleted, the new Runtime native tool path only ported `display` and `chat_history`. This ticket restores the executable backend capability without reintroducing Tools Server, TRS, or any fallback branch.

## Scope

- Add a synchronous Runtime executor `_exec_audio_qa` in `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.
- Keep the executor on the current unified tool dispatch path:
  - `dispatch(tool_name) -> executor(args, deps) -> dict -> Cortex step result`.
- Reuse BlobRef parsing rules from `display`.
- Fetch audio bytes through Blob Service using the current `user_id`.
- Resolve audio LLM config from Business internal config: `/internal/config/llm/agent/{agent_id}/audio`.
- Call LLM Factory `/v1/chat/completions` with OpenAI-compatible `input_audio`.
- Return a plain text `_mcp_content` result for LLM-visible context.
- Add execution-log display summary for `audio_qa`.

## Non-goals

- Do not expose `audio_qa` to the LLM schema yet. PR-137 owns schema exposure.
- Do not restore `novaic-tools-server`.
- Do not add provider-specific direct API-key logic in Runtime.
- Do not add arbitrary external URL fetch.

## Unit Tests

- Runtime executor is registered in `_EXECUTORS`.
- Audio executor rejects missing `file_url`, missing `user_id`, or missing `agent_id`.
- Audio executor downloads the Blob bytes with `X-User-ID`.
- Audio executor fetches Business audio config.
- Audio executor posts the expected `input_audio` payload to Factory.
- Audio executor returns the Factory answer as `_mcp_content` text.
- Existing display/chat_history tests continue to pass.

## Smoke Test

- Invoke `_exec_audio_qa` with fake Blob Service, Business, and Factory clients in test.
- After deploy, confirm Runtime imports and no `Unknown tool: audio_qa` path exists if a direct tool call is made.

## Deployment Checklist

- [x] Unit tests pass locally.
  - `cd novaic-agent-runtime && python -m pytest tests/unit/task_queue/test_tool_handlers_display_chat_history.py tests/test_pr86_execution_log_metadata.py -q`
- [x] Commit Runtime changes.
  - `25c0417 feat(runtime): add audio qa tool executor`
- [x] Push Runtime branch.
- [x] Deploy Runtime.
  - Deployed as part of `./deploy services` on 2026-05-01.
- [x] Production smoke: Runtime logs show no startup error after deploy.
  - `./deploy status` showed all backend services up.
  - Remote Runtime import confirmed `audio_qa_registered= True`.
  - Tail grep on queue/task/cortex logs showed no fresh `Traceback`, `event=tool_call_failed`, or `audio_qa` error.
- [x] Update this ticket and parent submodule pointer.

## GitHub / Merge

- This ticket is independently mergeable before schema exposure.
- Suggested commit message: `feat(runtime): add audio qa tool executor`
