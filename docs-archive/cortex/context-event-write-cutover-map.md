# Cortex ContextEvent Write Cutover Map

> Status: historical cutover checklist. Current authoritative design lives in
> `docs/cortex/context-event-source.md`; this file is retained as implementation
> archaeology for the write-cutover phase.

This map is the Phase 3 checklist for moving Cortex writes from legacy files to the append-only ContextEvent stream. The target state is one authoritative event log per root scope:

```text
/ro/active/<root_scope_id>/context_events/events.jsonl
```

Legacy files may survive only as projections or debug artifacts during later phases. They must not remain a parallel source of truth.

## Write Boundary

- Event model: `novaic-cortex/novaic_cortex/context_events.py`
- Event store: `novaic-cortex/novaic_cortex/context_event_store.py`
- Event writer boundary: `novaic-cortex/novaic_cortex/context_event_writer.py`
- Projection/replay: `novaic-cortex/novaic_cortex/context_event_projection.py`

The writer takes a `ContextEventWriteContext` containing explicit user, agent, root scope, root path, and actor identity. Clock and id providers are injected into `ContextEventStore`.

## Path Map

| Current write path | Current owner | Legacy artifact | Target event | Phase child |
| --- | --- | --- | --- | --- |
| Root scope creation | `Workspace.create_scope`, API/runtime scope creation | `meta.json`, `steps/_index.jsonl`, parent `_index.jsonl` | `RootInitialized` | P024 |
| Wake/session start | queue/runtime calling scope creation | `meta.json`, `context.jsonl`, `steps/_index.jsonl` | `WakeStarted` | P024 |
| Input notification attachment | context append/batch callers | `context.jsonl` environment notification rows | `InputNotificationAttached` | P024 |
| System prompt insertion | context append/batch callers | `context.jsonl` system rows | `SystemPromptAdded` | P025 |
| Context append | `/v1/context/append`, `Workspace.append_context` | `context.jsonl` | `ContextMessageAppended` | P025 |
| Context batch | `/v1/context/batch`, `Workspace.append_context_batch` | `context.jsonl` | ordered `ContextMessageAppended` events | P025 |
| Assistant tool call observation | context append/batch callers | `context.jsonl` assistant rows with `tool_calls` | `AssistantToolCallRecorded` or `ContextMessageAppended` by message kind | P025/P026 |
| Tool step write | `/v1/steps/write`, `Workspace.append_step` | `steps/*.json`, `steps/_index.jsonl`, `payloads/*.json` | `ToolStepRecorded` | P026 |
| Skill begin | `/v1/context/skill_begin`, runtime `skill_begin` | child scope dir, parent `steps/_index.jsonl`, child `meta.json` | `SkillScopeOpened` | P027 |
| Skill end | `/v1/context/skill_end`, runtime `skill_end` | `summary.md`, `meta.json` phase flip | `SkillScopeClosed` | P027 |
| Wake archive/finalize | scope archive paths | archived `meta.json`, `summary.md`, `/ro/scopes/_index.jsonl` | `WakeArchived` | P024/P028 |

## Non-Goals For Phase 3.1

- Do not cut endpoint behavior over yet.
- Do not delete legacy files yet.
- Do not introduce migration or compatibility readers for old data.

## Cleanup Gate

Phase 3 is not complete until P028 confirms every remaining legacy write is either deleted or explicitly projection/debug-only.
