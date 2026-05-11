# Audit shell capability and tool CLI migration residue

## Problem Definition

Several harness/interface tools were moved into shell CLIs (`agentctl`, `devicectl`, media commands) while only a minimal set should remain outside shell. We need audit whether old direct tool schemas, handlers, or capability env gaps remain live.

## Proposed Solution

Inspect Cortex builtin tool schemas, runtime tool handlers, shell capability scripts, queue runtime tool execution, and device/media command surfaces. Identify which tools are exposed as shell CLI, which still exist as direct LLM/harness tools, and whether any direct surface violates the intended boundary.

## Acceptance Criteria

- List shell CLI capabilities and direct tool schema surfaces.
- Identify missing CLI coverage, missing identity/env binding, or stale direct tool exposure.
- Separate intended out-of-shell tools from old direct tools.
- Record evidence pointers.

## Verification Plan

- Search for `im_read`, `im_reply`, `im_send`, `subagent_spawn`, `display`, `audio_qa`, `device`, `devicectl`, `agentctl`, and builtin schema definitions.
- Inspect `shell_capabilities.py`, `builtin_tools.py`, runtime tool handlers, and queue shell env injection.

## Risks

- The user’s desired boundary evolved: display may intentionally remain outside shell, while most interface tools move inside shell. Use current code and recent design as evidence, not old assumptions.

## Assumptions

- `skill_begin`, `skill_end`, and `sleep` may remain harness-level; most IM/subagent/device/media commands should be shell CLI accessible.
