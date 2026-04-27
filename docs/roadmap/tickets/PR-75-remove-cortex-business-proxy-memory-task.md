# PR-75 — Remove BusinessProxy memory/task surfaces from Cortex

| Field | Value |
|---|---|
| **Ticket** | PR-75 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P1 ownership drift — Cortex still proxies business memory/task/notebook/search commands that are not scope-tree or context-assembly responsibilities. |
| **Blocks** | PR-76 |
| **Blocked by** | PR-74 preferred |
| **Invariant** | Cortex owns scope lifecycle and LLM context assembly only; business memory, user profile, tasks, notebooks, and search belong outside Cortex. |

## Intent

Remove the remaining Cortex-owned business proxy surface.

The current `BusinessProxy` and `novaic_cortex.cli` command routes make Cortex look like the owner of memory, task, notebook, and search semantics. That confuses the architecture and creates backdoors for old memory/task behavior to leak into the LLM path.

## Required Behavior

- Delete or hard-disable Cortex `/v1/proxy/{command}` routes for `memory`, `task`, `notebook`, and `search`.
- Delete or move Cortex CLI commands that proxy `memory save/recall/delete/list` and `task create/start/complete/progress/delete/list`.
- Cortex tests should no longer assert business proxy behavior.
- If a replacement CLI is required, it must live in the owning service/package, not in Cortex.
- LLM tool assembly must not depend on these proxy routes.

## Acceptance Criteria

- Cortex source no longer contains active `BusinessProxy` memory/task/notebook/search routing.
- `/v1/proxy/memory` and `/v1/proxy/task` are unavailable from Cortex after deploy.
- Existing Cortex scope/context APIs remain healthy.
- Runtime LLM calls still expose only the tools actually supplied by the runtime tool registry.

## Engineering Checklist

### Unit Tests

- `[ ]` Remove or rewrite tests that expect Cortex business proxy success.
- `[ ]` Add contract test that Cortex API does not register business proxy routes.
- `[ ]` Add CLI test or command discovery test that Cortex CLI no longer exposes memory/task business commands.
- `[ ]` Run full Cortex test suite after route deletion.

### Smoke Tests

- `[ ]` Deployed Cortex health check passes.
- `[ ]` Calling old `/v1/proxy/memory` and `/v1/proxy/task` returns `404` or the chosen explicit removal response.
- `[ ]` A normal agent-root prepare/read path still works.
- `[ ]` A normal LLM tool call path using `shell`, `chat_reply`, `skill_begin`, and `skill_end` is unaffected.

### Deployment

- `[ ]` Deploy Cortex and any CLI packaging changes.
- `[ ]` Run `./deploy status`.
- `[ ]` Capture online evidence for old proxy route removal and normal context API health.

### GitHub / Commit

- `[ ]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[ ]` Commit message should reference `PR-75`.
- `[ ]` Push the branch and include route-removal evidence, tests, smoke, and deploy output in the PR description.

## Out of Scope

- Deleting Business-owned memory/task implementations.
- Redesigning user profile.
- Changing the `shell` tool itself.
