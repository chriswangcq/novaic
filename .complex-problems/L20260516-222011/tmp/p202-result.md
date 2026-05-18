# Cortex projection branch inventory result

## Summary

Completed a read-only Cortex projection inventory. The main active path is `parse_tool_result` -> projection formatter via `/v1/steps/read_formatted`. One clear stale production island was found: `resolve_for_llm` is not called by production code and exists only with tests. Several parser branches are compatibility/defensive and should be reviewed by the production-cleanup ticket rather than deleted blindly.

## Inventory

| Branch | Evidence | Classification | Reason |
| --- | --- | --- | --- |
| `tool-output.v1` artifact manifest parser | `novaic-cortex/novaic_cortex/step_result_projection.py:59-90`, `:129-130` | active | Current shell/device CLI contract emits `tool-output.v1`; parser converts artifacts/events to text manifest and no `display_files`. |
| `/v1/steps/read_formatted` projection selector | `novaic-cortex/novaic_cortex/api.py:1776-1812` | active | Runtime calls this API with explicit `history`, `current_tool_result`, or `display_perception`. Unsupported projection now fails closed. |
| History/current formatter excludes display media | `novaic-cortex/novaic_cortex/step_result_projection.py:247-264` | active | Required contract: shell/current non-display and historical context are text/manifest only. |
| Display perception formatter includes display files only for explicit display projection | `novaic-cortex/novaic_cortex/step_result_projection.py:267-279`, `:218-240` | active | Needed only for explicit display tool perception; non-data URLs become text placeholders unless bytes were already represented as data URL. |
| `tool-step-payload.v1` wrapper reading `llm_content` | `novaic-cortex/novaic_cortex/step_result_projection.py:122-123` | active/compatibility | Current shell output storage can wrap public LLM content separately from raw shell payload; this branch prevents raw shell payload projection. |
| Nested `result` unwrapping | `novaic-cortex/novaic_cortex/step_result_projection.py:125-127` | compatibility candidate | Supports older wrapper shapes. Needs downstream cleanup decision based on persisted historical data; not proven current-producer active in this inventory. |
| Unified `{text, files_created, display_files}` branch | `novaic-cortex/novaic_cortex/step_result_projection.py:132-147` | compatibility/active | Still needed by older display-style outputs and current parser tests; should stay unless current display path fully moves to `tool-output.v1` plus artifact manifests. |
| MCP `content` / `_mcp_content` array parser | `novaic-cortex/novaic_cortex/step_result_projection.py:149-186` | active/compatibility | Active for display tool outputs and historical MCP content. However raw `data` -> data URL conversion must remain gated by projection mode. |
| Dict JSON fallback | `novaic-cortex/novaic_cortex/step_result_projection.py:188-199` | defensive compatibility | Avoids crashes on unknown persisted shapes, but can still stringify large unknown dicts. This should be considered in production cleanup for bounded serialization or stricter accepted shapes. |
| `resolve_for_llm` byte-aware helper | `novaic-cortex/novaic_cortex/step_result_projection.py:330-415`; only references are `novaic-cortex/tests/test_resolve_for_llm.py` | stale production candidate | `rg \"resolve_for_llm\\(\"` found no production call sites. It still inlines base64 for small images (`:390-391`), which conflicts with the newer shell/display contract if accidentally reconnected. |

## Cleanup Candidates

- Strong candidate: remove or quarantine `resolve_for_llm` and its tests if no current API uses it. It is production code with only test references and includes a base64-inline path.
- Review candidate: nested `result` unwrapping should either be justified as persisted-data compatibility or removed.
- Review candidate: dict JSON fallback should be bounded or narrowed if it can project large unknown payloads into LLM history.

## Verification

Read-only inventory commands used:

```bash
nl -ba novaic-cortex/novaic_cortex/step_result_projection.py | sed -n '1,360p'
rg -n "parse_tool_result|format_for_history_llm|format_for_display_perception_llm|step_result_projection|projection=" novaic-cortex novaic-agent-runtime -g'*.py'
rg -n "llm_content|tool-output\\.v1|display_files|_mcp_content|data:image|base64|artifact|image_url|_placeholder|truncated" novaic-cortex/novaic_cortex novaic-cortex/tests -g'*.py'
rg -n "resolve_for_llm\\(" -g'*.py' .
```

## Code Changes

None. This ticket was inventory-only.
