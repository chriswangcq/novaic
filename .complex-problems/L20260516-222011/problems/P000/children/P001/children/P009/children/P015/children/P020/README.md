# Subagent and audio direct tool residue scan

## Problem

Search for active direct LLM exposure or stale docs of `subagent_spawn` and `audio_qa` outside the intended `agentctl subagent ...` and `agentctl media audio-qa ...` shell CLIs and guard tests.

## Success Criteria

- Active code/tests/docs are searched with `.complex-problems` excluded.
- Valid references inside CLI implementation and absence-guard tests are identified.
- Stale or misleading references are fixed if found.
- Current direct LLM tool schemas remain free of subagent/audio direct tools.
