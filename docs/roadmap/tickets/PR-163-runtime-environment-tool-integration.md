# PR-163 — Runtime Environment Tool Integration

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-agent-runtime`, `novaic-business`, docs |
| Depends on | PR-162 |
| Theme | LLM observation/action tools |

## Goal

Expose Environment through native LLM tools so the agent observes and acts like a subject in an environment instead of receiving raw messages as prompt facts.

The first-class tool surface should cover IM reading, replying, sending to other agents/subagents, and resource/payload inspection where appropriate. Existing user communication and subagent communication paths must converge here instead of growing parallel tool families.

## Required Process

1. Analyze existing tool schemas, runtime executors, `chat_reply`, `chat_history`, `subagent_send`, and related product semantics.
2. Create small tickets for each independently testable tool slice.
3. Implement one small ticket at a time.
4. For each small ticket: unit tests, smoke test, deploy plan/result, Git commit/merge evidence.
5. Confirm no old tool path remains for the same product function before closing.

## Planned Small Tickets

- [x] [PR-163A — Environment tool schema candidates](PR-163A-environment-tool-schema-candidates.md) — deployed in `novaic-common` commit `ef35576`.
- [x] [PR-163B — Runtime executors for Environment IM tools](PR-163B-runtime-environment-im-executors.md) — deployed in `novaic-business` commit `e7f95ef` and `novaic-agent-runtime` commit `116fd04`; active LLM tools unchanged.
- [x] [PR-163C — Environment tool exposure and old communication tool cleanup](PR-163C-environment-tool-cutover-cleanup.md) — deployed and production-smoke verified.

## Current-State Analysis

Completed 2026-05-02.

Current live tool stack:

- `novaic-common/common/tools/llm_builtin.py` is the active canonical LLM tool schema source.
- Runtime `task_queue/handlers/tool_handlers.py` owns executor dispatch via `_EXECUTORS`.
- Runtime tests guard that active schemas, executors, tool product semantics, and execution-log display kinds stay aligned.
- `chat_reply` directly creates `AGENT_REPLY` rows through Business/Entangled.
- `subagent_send` directly calls Business subagent send route, which writes `SUBAGENT_SEND` rows.
- `chat_history` directly calls Business recent chat history.
- `context.read` still reads `scope.meta.input_message_ids`, fetches message rows, renders IM text, and appends LLM-visible context. That is the current pre-Environment observation path.

Conclusion: new Environment tools must not be added to active `AGENT_BUILTIN_TOOL_SCHEMAS` until Runtime executors, Business service/API, product semantics, and monitor display are present. PR-163A therefore creates candidate schemas only; PR-163B adds executors; PR-163C flips exposure and deletes superseded communication paths.

## Progress Notes

- PR-163A added candidate `im_read`, `im_reply`, and `im_send` schemas in `novaic-common` while keeping active tool exposure unchanged.
- PR-163B added Business internal Environment IM routes plus Runtime candidate executors. Production smoke confirmed `active_intersection []`, so no LLM-facing behavior changed yet.
- PR-163C completed the hot-path cutover: Environment IM tools are active, prompt/tool descriptions and Agent Monitor semantics are aligned, and superseded communication executors/routes were physically deleted.

## Boundary Invariants

- Tool schema source is shared, not duplicated.
- Runtime executes tools; Business owns Environment storage/service.
- Tool result payloads use references when large or sensitive.
- `subagent_report`, query/cancel residue, and direct hidden message channels must not return.

## Done Criteria

- LLM sees Environment tools from the canonical schema.
- Runtime executors call Environment services and produce consistent failure semantics.
- Product smoke confirms user reply and subagent IM still work.
- Old communication tool paths are physically deleted or guarded.
- Deployed 2026-05-02.
