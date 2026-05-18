# Cortex Context Event Source Cutover Design

Status: target design for the full cutover. Old Cortex context history may be reset during deployment; no pre-cutover data migration or compatibility reader is required.

## 1. Goal

Cortex context source of truth moves from DFS workspace files to an append-only context event stream.

Current source model:

```text
context.jsonl + steps/_index.jsonl + steps/*.json + meta.json + summary.md
  -> ContextEngine DFS scan
  -> prepared LLM messages
```

Target source model:

```text
ContextEvent stream
  -> LLM context projection
  -> workspace RO/debug projection
  -> monitor/activity projection
```

Files may still exist after the cutover, but only as derived projections for shell, RO inspection, activity views, and debugging. They must not be treated as the authoritative source for LLM context semantics.

## 2. Non-goals

- No migration of old historical context data.
- No permanent dual-read path where DFS files and ContextEvents are co-equal truth.
- No hidden fallback that returns empty or stale context when event replay/projection fails.
- No raw IM message body injection during context assembly. Environment notifications remain hints; the agent must explicitly read message bodies through the IM capability.

## 3. Source Identity

The event stream key is:

```text
tenant_id = user_id
agent_id
root_scope_id = agent-root scope id
```

Every event belongs to exactly one root stream:

```json
{
  "schema_version": 1,
  "event_id": "ctxevt_...",
  "stream_id": "user_id/agent_id/root_scope_id",
  "root_scope_id": "agent-root-main-...",
  "seq": 42,
  "idempotency_key": "optional stable key",
  "occurred_at": "2026-05-10T15:40:00+08:00",
  "actor": "runtime|cortex|agent|system",
  "type": "ToolStepRecorded",
  "payload": {}
}
```

Rules:

- `seq` is monotonic per stream and assigned by Cortex at append time.
- `event_id` is globally unique.
- `idempotency_key` dedupes retries. Same key with same canonical event body returns the existing event. Same key with different body is rejected.
- Append is serialized per `(user_id, agent_id, root_scope_id)`.
- Core transition/projection logic receives explicit clock/id providers in tests.

## 4. Event Types

### 4.1 Session and wake

`RootInitialized`

```json
{
  "root_scope_id": "...",
  "subagent_id": "main-...",
  "scope_name": "agent root: main-..."
}
```

`WakeStarted`

```json
{
  "wake_scope_id": "...",
  "wake_scope_path": "/ro/active/.../steps/0001_scope_...",
  "session_generation": 7,
  "trigger_type": "user_message|system_wake|recovery",
  "scope_name": "user conversation",
  "message_ids": ["..."]
}
```

`WakeArchived`

```json
{
  "wake_scope_id": "...",
  "reason": "normal|forced|watchdog|recovery",
  "remaining_stack": ["scope-a", "scope-b"]
}
```

### 4.2 Prompt/context messages

`SystemPromptAdded`

```json
{
  "scope_id": "wake-id",
  "message": {
    "role": "system",
    "content": "...",
    "_message_type": "SYSTEM_MESSAGE"
  }
}
```

`ContextMessageAppended`

```json
{
  "scope_id": "wake-or-skill-id",
  "message": {
    "role": "assistant|system|user",
    "content": "..."
  },
  "message_kind": "system_prompt|assistant|notification_hint|manual"
}
```

`InputNotificationAttached`

```json
{
  "scope_id": "wake-id",
  "notification_id": "...",
  "source_kind": "im_message"
}
```

Projection renders this as the existing environment-notification system message. It does not fetch the IM body.

### 4.3 Skill scopes

`SkillScopeOpened`

```json
{
  "scope_id": "research-1",
  "parent_scope_id": "wake-id",
  "skill_name": "research",
  "name": "research task"
}
```

`SkillScopeClosed`

```json
{
  "scope_id": "research-1",
  "report": "exact skill_end report",
  "remaining_stack": ["wake-id"]
}
```

Rules:

- LIFO validation happens before append.
- `report` is exact persisted content.
- Closed non-empty scopes become folded context messages.
- Blank closed scopes are structural and may expose child folds.

### 4.4 Tool and payload facts

`AssistantToolCallRecorded`

```json
{
  "scope_id": "wake-or-skill-id",
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": []
  }
}
```

`ToolStepRecorded`

```json
{
  "scope_id": "wake-or-skill-id",
  "call_id": "shell:1",
  "tool": "shell",
  "status": "completed|failed|timeout",
  "observation": {},
  "payload_ref": "step-ref:...",
  "artifacts": []
}
```

Payload bytes may live in the existing payload/blob layer. The event stores the stable reference and the LLM projection uses the explicit observation/preview contract.

## 5. Projection Model

### 5.1 LLM context projection

Input: ordered ContextEvents for one root stream.

Output:

```json
{
  "root_scope_id": "...",
  "applied_seq": 42,
  "messages": [],
  "stack": [],
  "estimated_tokens": 1234
}
```

Semantics:

- Replay builds an in-memory scope tree from events.
- Only one newest unanchored open sibling is active at a level; older open siblings are stale residue and suppressed until archived/recovered.
- Closed non-empty scopes render as `[Skill '<name>' completed]\n<report>`.
- Blank structural closed scopes recurse into child folds.
- Tool result messages are inserted according to assistant tool calls and `call_id`.
- Primary system prompts are hoisted ahead of folded history.
- Budget compaction remains a projection pass, not a source mutation.

### 5.2 Workspace RO/debug projection

The existing workspace shape may be generated for tools and human inspection:

```text
/ro/active/<root>/meta.json
/ro/active/<root>/context_events/*.jsonl
/ro/active/<root>/steps/_index.jsonl
/ro/active/<root>/steps/<scope>/meta.json
/ro/active/<root>/steps/<scope>/summary.md
```

After cutover, these files are projection/debug files. Code must not use them as LLM context source truth.

### 5.3 Monitor/activity projection

Monitor timelines are derived from the same events:

- wake started/archived
- assistant message recorded
- tool started/completed
- skill opened/closed
- forced recovery/finalize

This prevents monitor and prompt context from explaining different histories.

## 6. API Ownership

### Write APIs

These APIs append ContextEvents as the authoritative operation:

- `/v1/context/append`
- `/v1/context/batch`
- `/v1/steps/write`
- `/v1/context/skill_begin`
- `/v1/context/skill_end`
- wake/session init Runtime path
- `/v1/scope/append_input`

Projection files can be updated synchronously after append, or by a projector worker, but the append is the source fact.

### Read APIs

These APIs read event projections:

- `/v1/context/prepare_for_llm`
- `/v1/context/status`
- context debug/read endpoints
- payload/tool step lookup where applicable

Legacy DFS read helpers must either be deleted or marked internal debug verification only.

## 7. Cutover Policy

Old historical context data can be deleted.

Deployment reset rule:

```text
For every agent root:
  delete old context.jsonl/steps/meta-derived history if needed
  initialize a fresh ContextEvent stream with RootInitialized
  start future wakes from ContextEvents only
```

No old-data migration means:

- No compatibility reader for old `summary.md` as source.
- No fallback to old `steps/_index.jsonl` as source.
- Existing tests that depend on direct DFS source setup must be rewritten to create events or use event-aware helpers.

## 8. Failure and Repair

Required behavior:

- If projection is behind, `prepare_for_llm` may replay synchronously from events or fail loudly. It must not return empty context silently.
- If projection files are corrupt, delete and replay from ContextEvents.
- If ContextEvent stream is corrupt, fail the session and require recovery; do not infer facts from projections.
- If duplicate idempotency key appears with different body, reject append.

Observability:

- `context_event_append_total`
- `context_event_duplicate_total`
- `context_projection_replay_total`
- `context_projection_lag`
- `context_projection_repair_total`
- `context_projection_failure_total`

## 9. Construction Plan

### Phase 1: Event store substrate

- Add event envelope and typed payloads.
- Add append/read replay API.
- Add stream sequence/idempotency tests.
- Keep old code untouched except for substrate tests.

### Phase 2: Projection/replay

- Build pure replay from events to:
  - active stack
  - LLM messages
  - folded summaries
  - tool result placement
  - notification hints
- Add projection tests matching existing DFS behavior.

### Phase 3: Write cutover

- Route context append/batch, step write, skill begin/end, wake init, and input notification attachment through ContextEvents.
- Projection files become derived output.
- Remove direct source writes where possible.

### Phase 4: Read cutover

- Make `prepare_for_llm` and `context_status` read from event projection.
- Delete or quarantine `ContextEngine` DFS-as-source path.
- Keep explicit debug rebuild only if it is clearly named and not used by normal runtime.

### Phase 5: Cleanup and verification

- Delete stale DFS source docs/comments/tests or rewrite them as projection docs.
- Add reset/no-compat deployment notes.
- Run full Cortex and Runtime tests.
- Audit for old source-truth terms: `ContextEngine`, `StepTreeBuilder`, direct `summary.md` source reads, direct DFS source tests.

## 10. Hard Invariants

- ContextEvents are the only source of truth for context semantics.
- Projections are rebuildable and disposable.
- One root stream has one total order.
- Every mutation is idempotent or rejected.
- LIFO skill stack is derived from events and enforced before append.
- Notification events carry notification ids, not hidden message bodies.
- No permanent feature flag keeps old DFS source semantics alive.
