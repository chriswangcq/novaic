# Unified shell boundary and tool output contract design

## Summary

The proposed target shape is a **minimal harness + shell capability plane + explicit display perception plane**.

Outside shell, the Agent Runtime should expose only primitives that are truly about the agent loop itself:

1. `shell`: the agent's general environment operation surface.
2. `display`: explicit model-visible perception for visual/file resources.
3. `skill_begin` / `skill_end`: Cortex context-stack structure.
4. `sleep`: scheduler/yield semantics.

Everything else that is an environment operation should move behind shell-facing capabilities: IM read/reply/search/history/context, subagent coordination, device APIs, blob/payload/file APIs, queue/runtime inspection APIs, and future interface tools.

The durable tool output contract should be **bounded text by default plus artifact/resource URIs**. Raw images, audio, large logs, screenshots, and bulky JSON should live in file/blob/payload storage and enter LLM context only as compact manifests. `display` remains outside shell because it is not an interface API; it is intentional perception.

## Done

- Created a ledger-backed design problem and ticket.
- Incorporated the prior file/display architecture and tool optimization audit conclusions.
- Defined the shell-inside/shell-outside boundary.
- Defined a concrete `ToolOutputV1` envelope.
- Defined storage/context/display/monitor projection rules.
- Defined operational flows for IM, screenshots/device, subagents, payloads, and shell large output.
- Defined invariants, failure modes, safety model, migration phases, and non-goals.
- Did not change runtime code.

## Verification

- The design explicitly lists the shell-outside primitives and shell-inside capability families.
- The design preserves the user's core principle: the agent is the subject; user/device/files/blob/subagents are environment resources.
- The design keeps `display` outside shell as the perception primitive, without adding the previously discussed current-turn perception authorization mechanism.
- The design makes `ToolOutputV1` the durable contract and treats `_mcp_content` as a provider/model projection, not the source of truth.
- The design is compatible with the existing file/display direction: history gets manifests, not raw base64.
- Verification is design-level only; no production test suite was run because no runtime code was changed.

## Known Gaps

- This is not yet an implementation plan with code-level tickets.
- Some exact command names under shell, such as `agentctl im read`, are design examples rather than final CLI names.
- Security policy details such as exact token scopes, audit schema, and permission prompts need implementation-phase design.

## Artifacts

- Root problem: `.complex-problems/tool-shell-boundary-system-design-root.md`
- Ticket: `.complex-problems/tool-shell-boundary-system-design-ticket.md`
- Result/design: `.complex-problems/tool-shell-boundary-system-design-result.md`

## 1. North Star

The runtime should stop treating every capability as an equal "LLM tool". There are different categories:

- **Agent loop structure**: lifecycle, context stack, scheduler yield.
- **Environment operation**: read messages, send replies, spawn workers, inspect files, call device APIs, inspect payloads.
- **Perception**: intentionally look at an image/file/video-like resource.
- **Storage/resource**: bytes, logs, screenshots, payloads, blobs, files.

The agent is the subject. The environment is what the agent acts on. The user is part of the environment. Shell is the agent's general manipulator for environment operations. Display is the agent's visual perception. Cortex skill lifecycle is the agent's self/context structure.

That leads to the core rule:

```text
Harness primitives are few and structural.
Environment interfaces live behind shell.
Large outputs become resources.
Perception is explicit through display.
History stores manifests, not raw sensory bytes.
```

## 2. Final Boundary

### 2.1 Outside Shell

Only these remain first-class harness tools:

| Tool | Reason it stays outside shell |
| --- | --- |
| `shell` | General environment execution and capability surface. It is the bridge into the world. |
| `display` | Explicit model-visible perception. It can return visual content to the model, so it is not just an environment API. |
| `skill_begin` | Structural operation on Cortex context stack; not an environment side effect. |
| `skill_end` | Structural operation on Cortex context stack and durable summary folding; not an environment side effect. |
| `sleep` | Scheduler/yield primitive for the agent loop; not an environment API. |

This set is intentionally small. It should be boring, stable, and hard to misuse.

### 2.2 Inside Shell

These should move behind shell-facing commands/APIs:

| Family | Examples | Shell-facing shape |
| --- | --- | --- |
| IM interface | `im_read`, `im_reply`, `im_history`, `im_search`, `im_context`, `im_send` | `agentctl im read`, `agentctl im reply`, `agentctl im history` |
| Subagent interface | `subagent_spawn`, `im_send` to subagent, status, cancel | `agentctl subagent spawn`, `agentctl subagent send`, `agentctl subagent status` |
| Device interface | screenshot, click, type, shell, app state | `device screenshot --out ...`, `device click ...`, `device state ...` |
| Blob/file resource | upload/download/list/stat | `blob put/get/stat`, normal filesystem commands |
| Payload/Cortex data read | read/search/summarize/qa payloads | `cortex payload read/search`, or shell-native `rg/head/jq` over mounted payload files |
| Runtime inspection | session state, queue state, outbox, workers | `runtimectl sessions`, `runtimectl workers`, `runtimectl outbox` |
| Business/environment APIs | product events, business messages, connectors | `agentctl env ...` or domain CLIs with explicit contracts |

The exact command names are not the design essence. The design essence is that they become **environment operations** with filesystem/CLI/API semantics, instead of special harness-level LLM tools.

## 3. Why `display` Is Still Outside Shell

`display` is different from `blob get` or `cat image.png`.

`blob get` retrieves bytes. `display` turns a resource into model-visible perception. It is closer to "look at this" than "call this API".

This distinction matters:

- shell can create, fetch, move, inspect, and reference resources;
- display is how the model intentionally perceives a resource;
- Cortex history should record that the resource existed and maybe that the agent looked at it;
- Cortex history should not replay visual bytes every round.

So the intended pattern is:

```text
shell/device captures screenshot -> returns artifact URI
agent decides it needs to see it -> calls display(uri)
display returns ephemeral visual perception for this turn
history stores manifest + "displayed artifact X", not raw image bytes
```

## 4. Why `skill_begin/end` And `sleep` Stay Outside Shell

`skill_begin` and `skill_end` are not environment actions. They modify the agent's own working context structure:

- open a scoped work container;
- fold detailed work into `summary.md`;
- maintain LIFO stack invariants;
- create durable self-continuity.

If these went inside shell, a shell command would be allowed to mutate the context stack underneath the agent's reasoning loop. That is the wrong direction.

`sleep` is also not an environment API. It is a scheduler/yield primitive. Putting it in shell makes it look like `sleep 5`, but agent sleep semantically means "yield the loop and let the harness resume later".

## 5. Tool Output Contract

The durable contract should be `ToolOutputV1`.

```json
{
  "version": "tool-output.v1",
  "ok": true,
  "text": "Short bounded human/model-readable summary.",
  "artifacts": [
    {
      "id": "artifact:step-ref:...:screen",
      "uri": "blob://device-screenshot/...",
      "name": "desktop.png",
      "modality": "image",
      "mime_type": "image/png",
      "size_bytes": 138320,
      "sha256": "...",
      "summary": "Host desktop screenshot.",
      "source": {
        "tool": "device screenshot",
        "step_ref": "step-ref:...",
        "round_id": "round-..."
      },
      "access": {
        "display": {
          "tool": "display",
          "args": {
            "file_url": "blob://device-screenshot/..."
          }
        },
        "shell": {
          "command": "blob get blob://device-screenshot/... --out desktop.png"
        }
      },
      "projection": {
        "current_turn": "manifest_only",
        "history": "manifest_only",
        "monitor": "thumbnail_allowed"
      },
      "retention": {
        "class": "session_artifact",
        "expires_at": null
      }
    }
  ],
  "events": [
    {
      "type": "im.reply.sent",
      "id": "event:...",
      "summary": "Reply accepted by environment."
    }
  ],
  "diagnostics": {
    "duration_ms": 823,
    "truncated": false
  }
}
```

### Required Output Rules

- `text` is always bounded.
- `artifacts[]` carries bytes by URI, not inline base64.
- Large stdout/stderr becomes payload/file/blob artifacts with previews.
- `_mcp_content` is a projection for a provider/model call, not durable truth.
- Current-turn visual perception is produced by `display`, not by replaying historical tool results.
- Historical context renders artifacts as compact manifests and access hints.

## 6. Projection Model

The same tool result has different projections:

| Consumer | Projection |
| --- | --- |
| Current LLM turn | bounded `text`; `display` may produce ephemeral visual content only for explicit display calls |
| Future LLM history | compact manifest: name, type, summary, URI, access hint |
| Cortex durable store | full `ToolOutputV1` manifest plus payload refs; no raw sensory bytes unless stored as blob/file |
| Monitor UI | rich render: thumbnails, screenshots, files, status badges |
| Shell/filesystem | concrete files, payload refs, blob URIs, command outputs |

This removes the hidden coupling where a UI-friendly screenshot or a tool result accidentally becomes future prompt bloat.

## 7. Shell Capability Plane

Shell should evolve from "POSIX command runner only" into "the agent's operational plane".

There are two implementation-compatible shapes:

### 7.1 CLI Shape

Provide commands inside the shell environment:

```bash
agentctl im read --limit 20
agentctl im reply --message-file reply.md
agentctl subagent spawn --task-file task.md
device screenshot --out screenshot.png --emit-artifact
cortex payload read "$REF" --head 2000
runtimectl sessions --agent "$AGENT_ID"
blob get "$URI" --out file.bin
```

Each command returns `ToolOutputV1` or plain text that shell wraps into `ToolOutputV1`.

### 7.2 Filesystem Shape

Expose environment state as mounted files and command-friendly directories:

```text
/agent/inbox/events.jsonl
/agent/outbox/
/agent/subagents/
/agent/payloads/
/agent/blobs/
/agent/runtime/
/agent/devices/
```

The agent can use normal `rg`, `jq`, `cat`, `head`, and redirection. Mutations go through command files or CLIs with explicit side-effect semantics.

The best long-term shape may combine both: filesystem for inspection, CLI for side effects.

## 8. Core Flows

### 8.1 IM Read And Reply

Target design:

```text
new user message -> Queue/FSM appends inbox event
context says "new inbox event available"
agent uses shell: agentctl im read
agent computes reply
agent uses shell: agentctl im reply --message-file reply.md
shell output returns event id + status as ToolOutputV1
```

This means `im_read` and `im_reply` become environment operations. They are still audited and bounded, but they no longer occupy harness primitive space.

Important invariant: an IM reply should be an idempotent environment side effect with an idempotency key. Failure should return a structured error event, not silently consume the agent's context budget.

### 8.2 Device Screenshot

Target design:

```text
shell: device screenshot --emit-artifact
-> text: "Captured screenshot"
-> artifact: blob://... image/png
agent: display(blob://...)
-> ephemeral perception
history: "Agent displayed screenshot artifact X"
```

No raw screenshot bytes in future context. Monitor UI can show thumbnail from artifact URI.

### 8.3 Subagent

Target design:

```text
shell: agentctl subagent spawn --task-file task.md
-> event subagent.spawned + subagent_id
shell: agentctl subagent send --id ... --message-file ...
shell: agentctl subagent inbox --id ...
```

Subagent management is environment coordination, not core harness structure. If a subagent result matters, it should appear as an inbox event or artifact.

### 8.4 Payload And Large Logs

Target design:

```text
shell command produces large stdout
runtime stores full stdout as payload/blob/file
tool output includes preview + payload/artifact URI
agent reads slices with shell/cortex payload read/search
```

This keeps large context in files and payloads, not in prompt.

## 9. Safety And Audit Model

Moving environment operations into shell does not mean "anything goes". It means the shell capability plane needs explicit controls:

- scoped environment tokens injected into shell;
- operation-level audit log;
- idempotency keys for side effects;
- per-command schema and validation;
- bounded output contract;
- permission classes: read-only, write, external side effect, destructive;
- redaction for secrets and private payloads;
- durable outbox for side-effect publication where needed;
- replayable command records for debugging.

Shell becomes the common operational substrate, not an untyped escape hatch.

## 10. Invariants

- Only `shell`, `display`, `skill_begin`, `skill_end`, and `sleep` are harness primitives.
- Any environment IO outside `display` must be reachable through shell capability commands/files.
- `display` is read-only perception and must not become a generic side-effect API.
- `ToolOutputV1` is the durable result contract.
- Historical Cortex context never expands artifact bytes by default.
- Raw base64 images/audio are not durable step content.
- Monitor rendering does not imply LLM context rendering.
- Large stdout/stderr must have preview plus resource reference.
- Side-effecting shell capabilities must be auditable and idempotent.
- Context-stack mutation is only through `skill_begin`/`skill_end`.

## 11. Failure Modes And Handling

| Failure Mode | Required Handling |
| --- | --- |
| Shell command times out | Return bounded error text plus diagnostic event; do not inject partial huge output. |
| IM reply fails or cap reached | Return structured error with reason and recovery hint; preserve unsent reply as artifact if needed. |
| Artifact URI expired | Return manifest with stale status and suggested recovery command. |
| Display cannot decode file | Return text diagnostics and file metadata; do not retry indefinitely. |
| Subagent spawn succeeds but worker dies | Subagent status command reports dead/recovering; pending messages remain in inbox/outbox. |
| Large output exceeds policy | Store as payload/file; context receives preview and read/search hints. |
| Permission denied | Return explicit permission error event; no fallback to hidden privileged path. |
| Context stack unclosed | Harness finalization archives skill state structurally; shell cannot mutate stack directly. |

## 12. Migration Phases

This turn does not implement these phases, but the design should migrate in this order:

### Phase 0: Contract Freeze

- Write `ToolOutputV1` schema.
- Define artifact manifest fields.
- Define projection policies: current turn, history, monitor, shell.
- Mark `_mcp_content` as projection-only.

### Phase 1: Shell Capability Substrate

- Add a minimal `agentctl` / `runtimectl` / `device` command surface.
- Make commands return `ToolOutputV1`.
- Add audit/idempotency for side-effect commands.

### Phase 2: Resource-First Outputs

- Normalize device screenshot and file tools into artifacts.
- Normalize shell large stdout/stderr.
- Normalize blob/payload/file references.

### Phase 3: Move Interface Tools Behind Shell

- IM tools become shell commands.
- Subagent tools become shell commands.
- Payload/blob/runtime inspection becomes shell commands/files.
- Keep compatibility wrappers only during migration, then delete them.

### Phase 4: Display Hardening

- Make `display` output explicitly ephemeral.
- Historical display results become manifest-only.
- Monitor UI renders thumbnails independently.

### Phase 5: Harness Surface Enforcement

- Add tests/guards that no environment IO tool remains outside shell.
- Add context-bloat guards: no historical base64, no unbounded stdout.
- Remove old compatibility branches.

## 13. Non-Goals

- Do not implement code in this design step.
- Do not add the "current-turn perception authorization" idea yet.
- Do not move `display` into shell.
- Do not move `skill_begin`/`skill_end` into shell.
- Do not pretend shell is just POSIX; the design intentionally makes it the capability plane.

## 14. Final Position

This design is more radical than "optimize screenshot output". It turns the harness into a small structural kernel and moves environment operations into a scriptable, inspectable, file-friendly capability plane.

That matches the user's direction:

```text
AI era:
code is cheap;
branch residue is expensive;
hidden state is dangerous;
files are flexible;
shell adapts;
display perceives;
context stack remains structural.
```

The design is internally coherent as long as we keep the hard line:

```text
shell = operation
display = perception
skill = context structure
sleep = scheduling yield
artifact URI = durable resource
ToolOutputV1 = contract
```
