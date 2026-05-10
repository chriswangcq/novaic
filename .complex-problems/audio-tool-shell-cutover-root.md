# Audio QA tool schema cutover to shell

## Problem

`audio_qa` remains a direct LLM-facing tool. The target surface should keep display as the special visual/file perception tool, while other interface actions move behind shell capabilities. Audio transcription/QA can be represented as an explicit shell media command with file URLs and prompts.

## Success Criteria

- LLM-visible builtin schemas no longer include `audio_qa`.
- Shell schema advertises `agentctl media audio-qa`.
- The shell command fetches a Blob audio object, resolves the configured audio model, calls Factory, and returns JSON text output.
- Runtime guard tests classify direct `audio_qa` as schema-cutover compatibility only.
- Targeted tests cover schema cutover and the shell audio command path.
