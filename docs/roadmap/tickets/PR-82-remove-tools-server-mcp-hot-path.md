# PR-82 — Remove Tools Server / MCP registry from the active Runtime path

| Field | Value |
|---|---|
| **Ticket** | PR-82 |
| **Status** | `[code]` |
| **Opened** | 2026-04-28 |
| **Owner** | __ |
| **Severity** | P0 architecture cleanup — old tool-server/MCP registry concepts are still visible in active Runtime commands and wake cleanup, which conflicts with the current embedded tool-dispatch model. |
| **Depends on** | PR-78 preferred; can run before PR-79 if rename scope is kept narrow. |
| **Blocks** | A clean "Cortex minimal structure + Runtime embedded tools" mental model. |
| **Invariant** | LLM tools are exposed in the OpenAI `tools[]` payload and executed by Agent Runtime. There is no separate production Tools Server / MCP registry hot path. |

## Background

The current backend direction is:

```text
LLM tools[] -> Agent Runtime tool dispatcher -> Business/Cortex/Device calls as needed
```

But active Runtime still exposes old terms and paths:

- `novaic-backend tools-server`
- `--tools-server-url`
- `TOOLS_SERVER_URL`
- `MCP_CREATE`
- `MCP_DESTROY`
- `wake_finalize` step `destroy_mcp`

Even if most of this is effectively legacy, keeping it in active entrypoints makes future debugging harder. It suggests there is another tool architecture besides the current Runtime-dispatched tool surface.

## Goal

Remove Tools Server / MCP registry from the active backend hot path.

This ticket is not about Cortex summaries or LLM behavior. It is pure architecture cleanup.

## Non-Goals

- Do not redesign tool execution.
- Do not introduce a new tool registry service.
- Do not touch LLM prompt wording except where it explicitly mentions Tools Server / MCP.
- Do not remove unrelated MCP-like third-party projects unless they are active Runtime dependencies.

## Implementation Checklist

### 1. Runtime CLI and config cleanup

- [x] Remove `tools-server` command from `novaic-agent-runtime/main_novaic.py` if no longer supported.
- [x] Remove `run_tools_server()` or move it to an explicitly retired script outside active backend startup.
- [x] Remove deprecated `--tools-server-url` arguments from active Runtime/Gateway commands if they are ignored.
- [x] Remove `ServiceConfig.TOOLS_SERVER_URL` / split repo fields if no active code needs them.
- [x] Update `scripts/start.sh` and service startup docs so no active topology references a Tools Server process.

### 2. Queue topic and handler cleanup

- [x] Remove `MCP_CREATE` from active topic definitions if unused by live sagas.
- [x] Remove `MCP_DESTROY` from `wake_finalize`.
- [x] Delete or quarantine `task_queue/handlers/mcp_handlers.py`.
- [x] If a cleanup operation is still genuinely required, rename it to the real current concept and make it optional.

### 3. Wake finalize cleanup

- [x] Ensure `wake_finalize` closes Runtime lifecycle without depending on MCP/Tools cleanup.
- [x] Ensure failure of any retired cleanup cannot block setting main subagent sleeping / sub-subagent completed.
- [x] Ensure logs no longer say "destroy_mcp" on normal wake close.

### 4. Documentation cleanup

- [x] Update architecture docs that still imply a separate Tools Server.
- [x] Keep historical references only in retired/historical docs with clear wording.

## Unit Test Requirements

- [x] Runtime saga test: `wake_finalize` no longer schedules an `MCP_DESTROY` task.
- [x] Topic registry test: active task topics do not include `MCP_CREATE` / `MCP_DESTROY`, unless explicitly marked retired and unreachable.
- [x] Config test: active service config has no `TOOLS_SERVER_URL` dependency.
- [x] CLI test or smoke command: `novaic-backend --help` no longer advertises `tools-server`.

## Smoke Test Requirements

- [ ] Start local backend stack without any Tools Server process.
- [ ] Send a simple chat message.
- [ ] Verify the agent replies via `chat_reply`.
- [ ] Verify the wake closes normally.
- [ ] Verify logs contain no `MCP_CREATE`, `MCP_DESTROY`, `destroy_mcp`, or `Tools Server` on the happy path.

## Deployment Checklist

- [ ] Merge code in affected subrepos.
- [ ] Update parent repo submodule pointers if subrepos changed.
- [ ] Deploy affected services:
  - [ ] runtime / queue workers
  - [ ] gateway only if CLI/config was touched there
  - [ ] common config if changed
- [ ] Restart workers cleanly.
- [ ] Capture two production evidence snippets:
  - [ ] service startup logs show no Tools Server requirement.
  - [ ] one normal wake finalize log shows no MCP cleanup step.

## GitHub / Commit Checklist

- [ ] Commit subrepo changes in each affected submodule.
- [ ] Commit parent repo docs/submodule pointer changes.
- [ ] PR description links this ticket.
- [ ] PR description includes unit test output.
- [ ] PR description includes smoke test output.
- [ ] PR description includes deployment evidence before marking `[x]`.

## Acceptance Criteria

- `rg -n "Tools Server|TOOLS_SERVER_URL|MCP_CREATE|MCP_DESTROY|destroy_mcp" novaic-agent-runtime novaic-common novaic-gateway scripts docs` finds only retired historical notes or explicit migration text.
- Normal wake lifecycle does not schedule or log MCP registry cleanup.
- Tool execution still works through OpenAI `tools[]` + Runtime dispatcher.

## Rollback

Revert this PR if tool execution stops working or wake finalize no longer closes sessions. Rollback should not require restoring old data, because this ticket should not migrate persistent state.
