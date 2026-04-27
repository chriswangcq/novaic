# PR-72 — Align prompt and tool contract with agent-root continuity

| Field | Value |
|---|---|
| **Ticket** | PR-72 |
| **Status** | `[✓]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P1 contract drift — prompt still mixes agent-root semantics with retired `<PREV_SCOPE_*>` and impossible tool guidance. |
| **Blocks** | PR-73 |
| **Blocked by** | PR-70 and PR-71 recommended. |
| **Invariant** | The LLM prompt must describe only the current continuity path and only tools actually available in the current call. |

## Intent

Remove prompt/tool drift introduced while moving from R9 prompt-layer continuity to Cortex agent-root DFS continuity.

The model should understand that cross-wake continuity comes from the agent-root scope tree and folded wake summaries, not from `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` or forced root `skill_end`.

## Required Behavior

- System prompt no longer mentions `<PREV_SCOPE_HISTORY>` or `<PREV_SCOPE_TAIL>` in the main path.
- Prompt says closed wake scopes are folded as summaries under agent-root.
- Prompt does not instruct the model to use unavailable persistence APIs.
- No-tool warning does not force unrelated tools such as `shell` or `skill_begin`.
- Tool descriptions do not tell the model to close root/meta scopes that the tool will reject.

## Acceptance Criteria

- Fresh LLM calls contain no `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` wording.
- No-tool retry warning only asks the model to call an appropriate real tool, usually `chat_reply`.
- Active-stack guidance is accurate for child scopes and does not invite invalid root close behavior.
- Existing prompt assembly tests still pass with updated expectations.

## Engineering Checklist

### Unit Tests

- `[x]` Runtime prompt test: main system prompt contains agent-root continuity wording and no legacy PREV tokens.
- `[x]` Runtime warning test: no-tool warning does not mention forced `shell`, `skill_begin`, or root `skill_end`.
- `[x]` Tool-schema test: root/meta close guidance matches actual Cortex behavior.

Evidence:

- `cd novaic-agent-runtime && pytest -q tests/test_llm_prompt_contract.py tests/test_no_tool_warning.py tests/test_pr69_agent_root_continuity_prompt.py` → `13 passed in 0.09s`
- `cd novaic-business && pytest -q tests/test_pr72_prompt_defaults_contract.py` → `2 passed in 0.01s`
- `cd novaic-cortex && pytest -q tests/test_tool_schemas_limits.py` → `7 passed in 0.03s`
- `cd novaic-agent-runtime && pytest -q` → `253 passed in 0.94s`
- `cd novaic-business && pytest -q` → `136 passed, 1 warning in 1.09s`

### Smoke Tests

- `[x]` Inspect a fresh 小牛 LLM request and confirm prompt contract is coherent.
- `[x]` Trigger no-tool retry and confirm warning text is minimal and accurate.
- `[x]` Confirm normal `chat_reply` still works.

Evidence:

- Sent production 小牛 message `1cf59a8db211`: `PR72 smoke：请简短回复收到`.
- Agent reply `151cfdec5c56`: `收到！✅`.
- Archived wake scope `4e19418b-b008-4fab-9c74-4ef572736db5` context inspection:
  - `messages 3`
  - `has_agent_root True`
  - `has_summary_md True`
  - `has_prev False`
  - `has_skill_end_report False`
  - `has_root_meta_instruction False`
  - `has_smoke True`
  - `has_received True`
- Deployed Business drive defaults for 小牛:
  - `has_agent_root True`
  - `has_summary_md True`
  - `has_prev_history False`
  - `has_prev_tail False`
  - `has_skill_end_report False`
  - `has_root_meta_instruction False`
  - `has_subagent_rest False`
- Deployed Runtime `NO_TOOL_WARNING`:
  - `forces_shell_command False`
  - `forces_skill_begin False`
  - `forces_skill_end False`
  - `old_must_call_list False`

### Deployment

- `[x]` Deploy Runtime / Business prompt source if touched.
- `[x]` Run health checks.
- `[x]` Capture LLM request excerpts for prompt and warning text.

Evidence:

- `./deploy services` → all backend services synced and restarted.
- `./deploy status` → Entangled, Gateway, Business, Device, Queue, Storage-A, Cortex healthy; Workers `8`; Relay active.
- Log/API evidence captured from `/v1/context/read`, Business drive defaults, and deployed Runtime `NO_TOOL_WARNING`.

### GitHub / Commit

- `[x]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[x]` Commit message should reference PR-72.
- `[x]` PR description must include prompt excerpts and test output.

Evidence:

- Runtime submodule commit: `2e85fd5 runtime: align prompt contract with agent-root continuity`.
- Business submodule commit: `1f173f3 business: align default prompts with agent-root continuity`.
- Parent repo commit: this ticket update and submodule bump.

## Out of Scope

- Reintroducing legacy prompt blocks.
- User profile prompt redesign.
