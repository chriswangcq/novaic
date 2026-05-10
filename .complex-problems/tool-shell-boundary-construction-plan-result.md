# Tool shell boundary construction plan

## Summary

This is a construction plan, not an implementation patch. The plan turns the prior system design into dependency-ordered implementation phases with concrete tickets, module targets, verification commands, and deletion gates.

The migration should be treated as a **kernel shrink + capability-plane buildout + old-path deletion** project:

```text
Phase 0: baseline freeze and guardrails
Phase 1: ToolOutputV1 + ArtifactManifest substrate
Phase 2: Cortex manifest-aware storage/projection
Phase 3: shell capability substrate
Phase 4: resource-first producers: shell/display/device/audio/payload
Phase 5: move IM/subagent/payload/device/audio APIs behind shell
Phase 6: monitor/UI artifact projection
Phase 7: physical deletion of legacy harness tools and multimodal compat
Phase 8: deploy, smoke, rollback, and production observability
```

The non-negotiable cutover test is:

```text
The LLM-visible tool list contains only:
shell, display, skill_begin, skill_end, sleep

All former interface tools are reachable through shell capabilities,
and old direct harness paths are either deleted or hard-failed by guard tests.
```

## Done

- Created a schema-v6 solve-complex-problems ledger for the construction plan.
- Reviewed the prior system design ledger `L20260509-160042`.
- Inspected representative current code paths:
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-agent-runtime/task_queue/handlers/environment_tool_handlers.py`
  - `novaic-agent-runtime/task_queue/device_tools.py`
  - `novaic-agent-runtime/task_queue/contracts/llm_call.py`
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - `novaic-agent-runtime/task_queue/utils/context.py`
  - `novaic-agent-runtime/task_queue/utils/multimodal.py`
  - `novaic-agent-runtime/task_queue/utils/user_content.py`
  - `novaic-agent-runtime/task_queue/utils/activity_projection.py`
  - `novaic-cortex/novaic_cortex/workspace.py`
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
- Mapped the current direct-tool surface to concrete cleanup gates.
- Produced phased implementation tickets with file targets and verification.

## Verification

- The plan maps to real code evidence:
  - direct Runtime executors are centralized in `_EXECUTORS` in `tool_handlers.py`;
  - direct IM executors live in `environment_tool_handlers.py`;
  - dynamic device tool execution currently returns Device responses as-is in `device_tools.py`;
  - Cortex projection currently parses `_mcp_content`, `display_files`, and `data:` URLs in `step_result_projection.py`;
  - LLM preparation still runs `expand_messages_for_llm`, `sanitize_context`, and `process_multimodal_messages` in `llm_call.py`;
  - legacy multimodal extraction can still synthesize user image messages from tool results in `context.py` / `multimodal.py`.
- The plan includes deletion gates, not just additive new code.
- Runtime code was not changed in this ticket.

## Known Gaps

- Exact CLI command names are proposed, not finalized.
- The plan assumes the shell runtime can mount internal CLIs/filesystem views with scoped credentials.
- Security policy and audit schema are specified at construction level, but exact table/entity schemas need implementation tickets.
- This plan does not deploy or test code because it intentionally does not implement code changes.

## Artifacts

- Root problem: `.complex-problems/tool-shell-boundary-construction-plan-root.md`
- Ticket: `.complex-problems/tool-shell-boundary-construction-plan-ticket.md`
- Result/plan: `.complex-problems/tool-shell-boundary-construction-plan-result.md`

## 1. Current-State Anchors

### Runtime Tool Surface

Current central dispatch is in:

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`

Important current facts:

- `_ok()` serializes executor output into `content` via `json.dumps(...)`.
- `_EXECUTORS` currently includes:
  - `subagent_spawn`
  - `sleep`
  - `shell`
  - `display`
  - `audio_qa`
  - `payload_read/search/summarize/qa`
  - `skill_begin/end`
  - dynamic device tools
  - `ENVIRONMENT_EXECUTORS`
- `ENVIRONMENT_EXECUTORS` contributes `im_read`, `im_reply`, `im_send`, `im_history`, `im_search`, `im_context`.

This is the main surface to shrink.

### Direct Environment Tools

Current IM environment executors live in:

- `novaic-agent-runtime/task_queue/handlers/environment_tool_handlers.py`

They contain important logic that cannot disappear:

- `im_read` marks observed input IDs in Cortex session meta.
- `im_reply` checks read-before-reply and reply cap.
- IM history/search/context are bounded.

The plan is not to delete this behavior. The plan is to move the behavior behind shell-facing capabilities and remove it from the LLM-visible harness tool list.

### Device Tools

Current dynamic device tool routing lives in:

- `novaic-agent-runtime/task_queue/device_tools.py`

Current risk:

- `execute_mounted_device_tool()` returns Device JSON as-is.
- Device tools are mounted directly as LLM tools through `_EXECUTORS`.

The construction plan must normalize device output into `ToolOutputV1` and expose device operations through shell capability commands.

### Cortex Projection

Current projection risk lives in:

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/task_queue/utils/context.py`
- `novaic-agent-runtime/task_queue/utils/multimodal.py`

Current risks:

- `_mcp_content` image data can become `display_files`.
- `display_files` can carry `data:` URLs.
- `format_for_llm(... include_display=True)` can re-expand images.
- `process_multimodal_messages()` can synthesize user image messages from tool results.

The construction plan must make manifests the durable truth and delete or quarantine these compatibility paths.

## 2. Target Architecture At Implementation Level

### 2.1 LLM-Visible Harness Tool Set

Final LLM-visible tool set:

```text
shell
display
skill_begin
skill_end
sleep
```

Not final:

```text
im_read
im_reply
im_send
im_history
im_search
im_context
subagent_spawn
audio_qa
payload_read
payload_search
payload_summarize
payload_qa
hd_screenshot
hd_mouse
hd_keyboard
hd_shell_exec
hd_clipboard_get
hd_clipboard_set
hd_file_pull
hd_file_push
```

Those become shell capabilities.

### 2.2 Shell Capability Plane

Shell gets a small set of internal CLIs or mounted commands:

```bash
agentctl im read --limit 20
agentctl im reply --message-file reply.md
agentctl im history --limit 20
agentctl im search --query ...
agentctl subagent spawn --task-file task.md
agentctl subagent send --id ... --message-file msg.md

device screenshot --emit-artifact
device click --x ... --y ...
device type --text-file ...
device shell --command-file cmd.sh
device clipboard get

cortex payload read "$PAYLOAD_REF" --mode head --limit 2000
cortex payload search "$PAYLOAD_REF" --query ...
cortex artifact stat "$ARTIFACT_URI"

blob get "$URI" --out path
blob put path --mime ...

runtimectl sessions --agent "$AGENT_ID"
runtimectl outbox --agent "$AGENT_ID"
```

The CLI layer may be implemented as Python entrypoints, small shell shims, or mounted virtual commands. The exact mechanism is secondary; the boundary is primary.

### 2.3 Durable Tool Output Contract

All tool/capability outputs converge to:

```json
{
  "version": "tool-output.v1",
  "ok": true,
  "text": "bounded text summary",
  "artifacts": [],
  "events": [],
  "diagnostics": {
    "duration_ms": 10,
    "truncated": false
  }
}
```

Historical Cortex projection must prefer:

```text
text + artifact/event manifest + access hints
```

Current-turn `display` may produce provider-visible visual content, but stored history remains manifest-only.

## 3. Phase Plan

## Phase 0 — Baseline Freeze, Inventory, And Guardrails

### Goal

Prevent implementation from becoming another additive branch where new code exists but old paths still run.

### Tickets

#### T0.1 Tool Surface Inventory Snapshot

Files:

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/task_queue/handlers/environment_tool_handlers.py`
- `novaic-agent-runtime/task_queue/device_tools.py`
- Runtime tests under `novaic-agent-runtime/tests/`

Work:

- Add an inventory document or generated test fixture listing current LLM-visible tools.
- Record current direct executors and classify each as:
  - keep harness primitive;
  - move into shell;
  - delete legacy/compat.

Acceptance:

- Inventory lists every `_EXECUTORS` key.
- Every key has target fate.

Verification:

```bash
cd /Users/wangchaoqun/new-build-novaic/novaic-agent-runtime
python -m pytest tests/test_runtime_tool_path_contract.py tests/test_llm_prompt_contract.py
```

Deletion Gate:

- None yet. This is measurement only.

#### T0.2 Architecture Guard Skeleton

Files:

- `novaic-agent-runtime/tests/test_tool_surface_boundary.py` new
- possibly `novaic-agent-runtime/tests/threshold_policy.py`

Work:

- Add skipped or xfail-free tests that can become enforcement later:
  - final allowed harness tools set;
  - no direct `im_*` in final LLM tool schemas;
  - no direct dynamic device tools in final LLM tool schemas;
  - no historical base64 image projection.

Acceptance:

- Guard tests exist and initially document current failing/direct state if not enforced yet.
- They are easy to flip into hard gates during Phase 7.

Verification:

```bash
python -m pytest tests/test_tool_surface_boundary.py
```

Deletion Gate:

- None yet.

## Phase 1 — `ToolOutputV1` And Artifact Manifest Substrate

### Goal

Create the explicit output contract before migrating producers/consumers.

### Tickets

#### T1.1 Shared Tool Output Types

Files:

- Suggested new module: `novaic-agent-runtime/task_queue/tool_output.py`
- Optional shared module if cross-package reuse exists: `novaic-common/common/contracts/tool_output.py`
- Tests: `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`

Work:

- Define dataclasses or typed dicts:
  - `ToolOutputV1`
  - `ArtifactManifest`
  - `ToolEventManifest`
  - `ToolDiagnostics`
  - `ProjectionPolicy`
- Add constructors:
  - `tool_text(...)`
  - `tool_error(...)`
  - `artifact(...)`
  - `event(...)`
- Add serialization to JSON-compatible dict.
- Add text clamps and artifact validation.

Acceptance:

- No hidden reads of time/env/UUID inside pure constructors.
- IDs/timestamps supplied explicitly or at boundary.
- Text clamping deterministic.

Verification:

```bash
python -m pytest tests/unit/task_queue/test_tool_output_contract.py
```

Deletion Gate:

- None; this is substrate.

#### T1.2 Runtime `_ok()` Normalizes To `ToolOutputV1`

Files:

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- tests around `test_runtime_explicit_contracts.py`, `test_pr234_tool_logical_failure.py`

Work:

- `_ok()` accepts legacy dicts but normalizes them to `ToolOutputV1`.
- Preserve `tool_success` and current task status semantics.
- Store durable `content` as `ToolOutputV1` JSON.

Acceptance:

- Existing small text tools continue to work.
- Tool logical failure still sets `tool_success=false`.
- Old dict outputs become bounded text + diagnostics when no artifacts.

Verification:

```bash
python -m pytest tests/test_runtime_explicit_contracts.py tests/test_pr234_tool_logical_failure.py tests/unit/task_queue/test_tool_handlers_failure_event.py
```

Deletion Gate:

- Add TODO-ban/rg guard that no new executor returns raw `_mcp_content` as durable source of truth.

## Phase 2 — Cortex Manifest-Aware Storage And Projection

### Goal

Make Cortex understand `ToolOutputV1` and stop treating `_mcp_content` / `display_files` as the durable truth.

### Tickets

#### T2.1 Cortex Parser Supports `ToolOutputV1`

Files:

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/tests/test_tool_output_projection.py` new

Work:

- Extend `parse_tool_result()`:
  - first detect `version == "tool-output.v1"`;
  - extract bounded text;
  - extract artifacts and events;
  - treat `display_files` and `_mcp_content` as legacy fallback only.

Acceptance:

- `ToolOutputV1` with image artifact returns text manifest, not image base64.
- Legacy inputs still parse during migration.

Verification:

```bash
cd /Users/wangchaoqun/new-build-novaic/novaic-cortex
python -m pytest tests/test_tool_output_projection.py tests/test_payload_inspection_api.py tests/test_resolve_for_llm.py
```

Deletion Gate:

- Legacy `_mcp_content` parser marked compatibility-only and covered by a future deletion ticket.

#### T2.2 Split Current-Turn And History Projection

Files:

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`

Work:

- Replace generic `format_for_llm(include_display=...)` with explicit functions:
  - `format_for_history_llm()`
  - `format_for_current_tool_result_llm()`
  - `format_for_display_perception_llm()`
  - `format_for_monitor()`
- Ensure `prepare_llm_call()` passes `current_round_id=source.round_id` if still needed during transition.
- Ensure current-turn image bytes only come from explicit `display`.

Acceptance:

- Historical tool result with artifact never becomes base64.
- Current-turn non-display tool with screenshot artifact is manifest-only.
- Explicit display can still produce visual content.

Verification:

```bash
python -m pytest \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py
```

Deletion Gate:

- `include_display=True` on generic historical expansion must disappear or be isolated to display-only projection.

#### T2.3 Delete/Quarantine Generic Multimodal Tool Result Extraction

Files:

- `novaic-agent-runtime/task_queue/utils/context.py`
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
- tests: add/update `test_no_historical_tool_image_injection.py`

Work:

- Remove or hard-restrict `process_multimodal_messages()` image extraction from generic tool results.
- Allow provider image conversion only for explicit display perception records.

Acceptance:

- Tool result `_mcp_content` image from history cannot synthesize user image messages.
- User attachments remain reference-first.
- Explicit display still works.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/unit/task_queue/test_user_content.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py
```

Deletion Gate:

- Remove legacy image extraction helpers if no longer used.
- `rg "data:image|base64" task_queue/utils novaic_cortex` must show only explicit tests or display provider projection.

## Phase 3 — Shell Capability Substrate

### Goal

Build the surface that will host former interface tools.

### Tickets

#### T3.1 Agent Shell Command Runtime

Files:

- likely `novaic-cortex` shell bridge area, depending where `bridge.shell_exec` is implemented.
- possible new package/dir:
  - `novaic-agent-runtime/task_queue/shell_capabilities/`
  - `novaic-agent-runtime/task_queue/shell_capabilities/agentctl.py`
  - `novaic-agent-runtime/task_queue/shell_capabilities/device.py`
  - `novaic-agent-runtime/task_queue/shell_capabilities/cortexctl.py`

Work:

- Define how shell sees internal commands:
  - PATH-injected CLI scripts; or
  - shell prelude aliases; or
  - mounted filesystem commands.
- Bind scoped runtime credentials to shell process.
- Make each internal command emit bounded text or `ToolOutputV1`.

Acceptance:

- Shell can run a harmless internal command:
  - `agentctl --help`
  - `runtimectl --help`
  - `cortex payload --help`
- Commands are tenant/agent scoped.
- Command output is bounded by default.

Verification:

```bash
python -m pytest tests/unit/task_queue/test_shell_capability_runtime.py
```

Deletion Gate:

- None until shell commands cover old tools.

#### T3.2 Shell Output Normalizer

Files:

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- shell bridge implementation
- tests: `test_shell_output_projection.py`

Work:

- Convert shell stdout/stderr result into `ToolOutputV1`.
- Large stdout/stderr goes to payload/file/blob artifact.
- Prompt text includes preview and read/search hints.

Acceptance:

- Large stdout does not enter prompt in full.
- Shell timeout result is bounded and diagnostic.
- Full output is still recoverable by payload/file ref.

Verification:

```bash
python -m pytest tests/unit/task_queue/test_shell_output_projection.py novaic-cortex/tests/test_payload_inspection_api.py
```

Deletion Gate:

- `shell` result contract no longer returns arbitrary unbounded `stdout`/`stderr` as durable content.

## Phase 4 — Resource-First Producers

### Goal

Convert high-risk producers to artifacts before moving the tool surface.

### Tickets

#### T4.1 Display Becomes Ephemeral Perception Output

Files:

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-cortex/novaic_cortex/step_result_projection.py`
- tests: display history tests

Work:

- `_exec_display()` returns `ToolOutputV1`:
  - `text`: loaded file summary;
  - `artifacts`: original file ref metadata;
  - explicit `projection.current_turn = display_perception`;
  - explicit `projection.history = manifest_only`.
- Provider-visible `_mcp_content` is produced only at projection boundary, not durable content.

Acceptance:

- Current display call can show image.
- Historical display call renders as "looked at artifact X", not image data.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py \
  novaic-cortex/tests/test_resolve_for_llm.py
```

Deletion Gate:

- `_display_content_for_llm()` no longer returns durable `_mcp_content` directly.

#### T4.2 Device Tool Output Normalizers

Files:

- `novaic-agent-runtime/task_queue/device_tools.py`
- maybe `novaic-agent-runtime/task_queue/device_tool_output.py` new
- tests: `tests/unit/task_queue/test_device_tool_handlers.py`

Work:

- Normalize Device responses:
  - screenshot -> image artifact URI + optional thumbnail, no base64 durable output;
  - file pull -> file/blob artifact;
  - shell exec -> preview + payload artifact;
  - clipboard get -> bounded text;
  - mouse/keyboard/clipboard set -> event manifest.

Acceptance:

- Dynamic Device JSON is not returned as-is to tool history.
- Each device tool output class has explicit output policy.

Verification:

```bash
python -m pytest tests/unit/task_queue/test_device_tool_handlers.py tests/test_runtime_tool_path_contract.py
```

Deletion Gate:

- `execute_mounted_device_tool()` raw pass-through removed.

#### T4.3 Audio QA Moves To Resource Contract

Files:

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- maybe future shell command implementation
- tests for `audio_qa`

Work:

- Convert audio result into `ToolOutputV1`.
- Add size/duration guardrails if available.
- Long transcript becomes artifact/payload with preview.

Acceptance:

- No raw audio bytes in durable history.
- Transcript preview bounded.

Verification:

```bash
python -m pytest tests/unit/task_queue/test_audio_tool_output.py
```

Deletion Gate:

- Direct `audio_qa` tool remains only until Phase 5 shell command exists.

## Phase 5 — Move Interface Tools Behind Shell

### Goal

Make the shell capability plane functionally replace direct harness tools.

### Tickets

#### T5.1 IM Capability Commands

Files:

- new shell capability module for `agentctl im`
- reuse logic from `environment_tool_handlers.py`
- tests: existing `test_environment_tool_handlers.py`, new shell command tests

Work:

- Implement:
  - `agentctl im read`
  - `agentctl im reply`
  - `agentctl im send`
  - `agentctl im history`
  - `agentctl im search`
  - `agentctl im context`
- Preserve read-before-reply and reply cap semantics.
- Emit `ToolOutputV1` events.

Acceptance:

- Shell command can read current wake inbox.
- Shell command can reply with idempotent event output.
- Direct `im_reply` behavior and shell `agentctl im reply` behavior match.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/unit/task_queue/test_environment_tool_handlers.py \
  novaic-agent-runtime/tests/test_scope_end_environment_notifications.py \
  novaic-agent-runtime/tests/test_session_init_message_ids.py \
  novaic-agent-runtime/tests/test_shell_im_capabilities.py
```

Deletion Gate:

- Direct `im_*` LLM tool schemas removed from final tool list after parity smoke.

#### T5.2 Subagent Capability Commands

Files:

- new `agentctl subagent`
- move logic from `_exec_subagent_spawn` and subagent handlers
- tests around `test_pr124_subagent_spawn_im.py`, `test_subagent_state.py`

Work:

- Implement:
  - `agentctl subagent spawn`
  - `agentctl subagent send`
  - `agentctl subagent status`
  - `agentctl subagent list`
- Results are event manifests.

Acceptance:

- Subagent spawn works through shell.
- Subagent coordination is observable through IM/environment events.

Verification:

```bash
python -m pytest \
  novaic-business/tests/test_pr124_subagent_spawn_im.py \
  novaic-business/tests/test_subagent_state.py \
  novaic-agent-runtime/tests/test_shell_subagent_capabilities.py
```

Deletion Gate:

- Direct `subagent_spawn` removed from `_EXECUTORS`.

#### T5.3 Payload/Cortex Capability Commands

Files:

- new `cortex payload` / `cortex artifact`
- reuse bridge payload methods
- tests around `test_payload_tool_handlers.py`, `test_payload_inspection_api.py`

Work:

- Implement shell commands for:
  - payload read/search/summarize/qa;
  - artifact stat/list/read metadata.

Acceptance:

- Agent can inspect payloads from shell.
- Outputs are bounded and auditable.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/unit/task_queue/test_payload_tool_handlers.py \
  novaic-cortex/tests/test_payload_inspection_api.py \
  novaic-agent-runtime/tests/test_shell_payload_capabilities.py
```

Deletion Gate:

- Direct `payload_*` tools removed from `_EXECUTORS`.

#### T5.4 Device Capability Commands

Files:

- new `device` shell command surface
- `novaic-agent-runtime/task_queue/device_tools.py`

Work:

- Implement shell commands for HD operations.
- Make dynamic device tools no longer LLM-visible.
- Preserve permission checks through Device Service.

Acceptance:

- Screenshot/click/type/file/shell/clipboard operations work through shell.
- Device artifacts are manifests.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/unit/task_queue/test_device_tool_handlers.py \
  novaic-agent-runtime/tests/test_runtime_tool_path_contract.py \
  novaic-business/tests/test_pr151_device_binding_contract.py
```

Deletion Gate:

- Direct dynamic device tools removed from `_EXECUTORS` and tool schema assembly.

## Phase 6 — Monitor/UI Artifact Projection

### Goal

Make the user-visible monitor richer without affecting LLM context.

### Tickets

#### T6.1 Activity Projection Reads Artifacts

Files:

- `novaic-agent-runtime/task_queue/utils/activity_projection.py`
- Business/Entangled projection schemas if needed
- App monitor UI files if needed

Work:

- Add artifact-aware fields:
  - artifact count;
  - artifact modalities;
  - thumbnail URI;
  - has_visual_artifact;
  - has_payload;
  - current-turn perception flag.

Acceptance:

- Monitor can show screenshot thumbnail/artifact badge from manifest.
- LLM context remains manifest-only.

Verification:

```bash
python -m pytest novaic-agent-runtime/tests/test_pr193_activity_projection.py
```

Deletion Gate:

- UI must stop relying on model `_mcp_content` for visual rendering.

## Phase 7 — Physical Cutover And Legacy Deletion

### Goal

Make the new shape true, not aspirational.

### Tickets

#### T7.1 Shrink `_EXECUTORS`

Files:

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`

Work:

- Final `_EXECUTORS` includes only:
  - `shell`
  - `display`
  - `skill_begin`
  - `skill_end`
  - `sleep`
- Remove direct imports:
  - `ENVIRONMENT_EXECUTORS`
  - dynamic device tool executor entries
  - direct payload tools
  - direct audio_qa
  - direct subagent_spawn

Acceptance:

- Final tool path contract test proves only allowed harness tools.
- Calling removed tools returns unknown tool error.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/test_runtime_tool_path_contract.py \
  novaic-agent-runtime/tests/test_tool_surface_boundary.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py
```

Deletion Gate:

- Delete `environment_tool_handlers.py` if no longer used, or move it into shell capability internals and rename so it cannot be mistaken for harness executors.

#### T7.2 Delete Legacy Multimodal Compat

Files:

- `novaic-agent-runtime/task_queue/utils/multimodal.py`
- `novaic-agent-runtime/task_queue/utils/context.py`
- Cortex projection tests

Work:

- Remove generic image extraction from tool results.
- Keep only explicit display provider projection.

Acceptance:

- `rg "_mcp_content|display_files|data:"` shows no active durable-history image path except display projection and compatibility tests.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py \
  novaic-cortex/tests/test_tool_output_projection.py
```

Deletion Gate:

- Delete dead helper functions and stale tests; do not keep unused compatibility wrappers.

#### T7.3 Remove Legacy Tool Schema Exposure

Files:

- tool schema assembly path in Runtime/Business
- `novaic-agent-runtime/task_queue/device_tools.py`
- prompt/tool schema tests

Work:

- Ensure direct removed tools are not surfaced to LLM.
- Ensure documentation/prompt text tells agent to use shell commands.

Acceptance:

- No prompt says `Call im_read(...)`; prompt says use shell/agentctl.
- User attachment hint still says `display(file_url=...)` for images because display remains outside shell.

Verification:

```bash
python -m pytest \
  novaic-agent-runtime/tests/test_llm_prompt_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_user_content.py
```

Deletion Gate:

- Delete stale schema JSON/config entries for removed direct tools.

## Phase 8 — Deploy, Smoke, And Recovery

### Goal

Deploy safely and prove the new boundary in the real runtime.

### Tickets

#### T8.1 Local Full Matrix

Commands:

```bash
cd /Users/wangchaoqun/new-build-novaic/novaic-agent-runtime
python -m pytest

cd /Users/wangchaoqun/new-build-novaic/novaic-cortex
python -m pytest

cd /Users/wangchaoqun/new-build-novaic/novaic-business
python -m pytest
```

Acceptance:

- Runtime, Cortex, Business relevant suites pass.
- If full suite is too slow, define exact subset plus reason, then run full before deploy.

#### T8.2 Deploy Smoke

Smoke cases:

1. User sends message; agent reads/replies through shell IM command.
2. Agent calls shell `agentctl im read`.
3. Agent calls shell `agentctl im reply`.
4. Agent captures screenshot through shell device command.
5. Agent calls `display(blob://...)`.
6. Agent reads payload through shell Cortex command.
7. Agent opens/closes child skill through `skill_begin/end`.
8. Removed direct tool call is rejected.

Acceptance:

- Agent monitor shows activity.
- No runaway prompt growth.
- No shell timeout from loading RO/context.
- Context history stores artifact manifests.

#### T8.3 Rollback Plan

Rollback must not reintroduce residue silently.

Options:

- Feature flag for shell capability exposure.
- Feature flag for final tool list shrink.
- Emergency rollback branch.

Hard rule:

- Rollback can restore old direct tools temporarily, but must write a recovery ledger and expiration ticket.

## 4. Dependency Graph

```text
Phase 0
  -> Phase 1 ToolOutputV1
      -> Phase 2 Cortex projection
      -> Phase 3 shell capability substrate
          -> Phase 4 resource-first producers
              -> Phase 5 interface migration
                  -> Phase 6 monitor projection
                      -> Phase 7 deletion/cutover
                          -> Phase 8 deploy/smoke
```

Phase 2 and Phase 3 can proceed partly in parallel after Phase 1, but Phase 7 must wait for all parity tests.

## 5. Explicit Dependency Boundaries

### Pure / Deterministic Layer

Should have no hidden env/time/db/network:

- `ToolOutputV1` constructors
- artifact manifest validation
- projection decisions
- command argument parsers
- output truncation logic
- allowed tool set computation

Inputs must be explicit:

- clock;
- id provider;
- size limits;
- projection policy;
- current round id;
- tenant/agent IDs.

### IO Boundary Layer

Allowed to touch services:

- Business client;
- Device service client;
- Blob client;
- Cortex bridge;
- Queue/runtime inspect client.

All IO results must convert into `ToolOutputV1` before entering Cortex history.

## 6. Old-Code Cleanup Checklist

These are mandatory final checks, not optional polish:

- Remove direct `im_*` from `_EXECUTORS`.
- Remove direct `subagent_spawn` from `_EXECUTORS`.
- Remove direct `payload_*` from `_EXECUTORS`.
- Remove direct `audio_qa` from `_EXECUTORS`.
- Remove direct dynamic `hd_*` tools from `_EXECUTORS`.
- Remove or quarantine `ENVIRONMENT_EXECUTORS` as shell internal only.
- Remove raw device response pass-through.
- Remove generic historical `_mcp_content` image extraction.
- Remove durable `data:` URL image path.
- Remove stale prompt text instructing direct IM/payload/device calls.
- Remove stale tests that assert old tool list.
- Add rg guard for forbidden direct tool names in LLM tool schemas.

Suggested guard:

```bash
rg '\"(im_read|im_reply|im_send|im_history|im_search|im_context|subagent_spawn|payload_read|payload_search|payload_summarize|payload_qa|audio_qa|hd_screenshot|hd_mouse|hd_keyboard|hd_shell_exec|hd_clipboard_get|hd_clipboard_set|hd_file_pull|hd_file_push)\"' \
  novaic-agent-runtime/task_queue novaic-agent-runtime/tests
```

The guard must distinguish shell command names from direct harness tool schemas.

## 7. Cutover Definition Of Done

The project is not done until all are true:

- LLM-visible tool list is exactly `shell`, `display`, `skill_begin`, `skill_end`, `sleep`.
- IM read/reply smoke works through shell.
- Subagent spawn/send/status works through shell.
- Device screenshot/click/type works through shell.
- Payload read/search works through shell.
- Display can perceive a blob artifact.
- Historical context never replays image/audio/base64 bytes.
- Large shell output is preview + ref.
- Monitor shows artifact metadata without changing LLM prompt.
- Removed direct tools hard-fail as unknown if attempted.
- Deletion/compat cleanup tests pass.

## 8. Suggested Execution Order As Future Ledgers

When implementing, do not run this whole plan in one giant branch. Use phase ledgers:

1. `L-tool-output-v1-substrate`
2. `L-cortex-manifest-projection`
3. `L-shell-capability-substrate`
4. `L-resource-first-producers`
5. `L-shell-im-subagent-payload-device-migration`
6. `L-monitor-artifact-projection`
7. `L-harness-tool-surface-deletion`
8. `L-deploy-smoke-boundary`

Each ledger should follow:

```text
create phase problem
create tickets
execute tickets
record results
check success
if gap -> follow-up ticket
only then proceed
```

## 9. Strong Recommendation

Do not begin by deleting direct tools. Begin by making the new output contract and projection safe. Then build shell parity. Then delete.

The right order is:

```text
contract -> projection -> shell parity -> producer normalization -> migration -> deletion
```

If we reverse it, we will break agent IO. If we only add new shell commands and do not delete old direct tools, we will violate the user's core AI-era rule: code is cheap, residual branches are expensive.
