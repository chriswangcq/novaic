# PR-164 — Cortex Observation and Payload Integration

> Historical note: updated by PR-193. Cortex remains the working trace and payload/ref home, but the user-facing Agent Monitor is now Entangled activity projection, not a Cortex HTTP projection endpoint.

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-cortex`, `novaic-agent-runtime`, `novaic-business`, `novaic-common`, docs |
| Depends on | PR-163 |
| Theme | Work trajectory / perception record |

## Goal

Make Cortex the durable work trajectory for agent perception/action: observation percepts, LLM reasoning, tool actions, replies, interpretations, and scope summaries.

Large or sensitive tool results should not be blindly embedded into Cortex. They should become observation summaries plus payload refs; the agent can inspect tails/heads or request explicit interpretation when useful.

## Required Process

1. Analyze current Cortex event/scope/result model and runtime write sites.
2. Create small tickets for observation, payload ref, and interpretation slices.
3. Implement one small ticket at a time.
4. For each small ticket: unit tests, smoke test, deploy plan/result, Git commit/merge evidence.
5. Confirm Activity Timeline can project user-visible work without raw debug payloads.

## Planned Small Tickets

- [x] [PR-164A — Tool result observation payload write path](PR-164A-tool-result-observation-payload-write-path.md) — deployed in `novaic-common` commit `97f2a94`, `novaic-agent-runtime` commit `05a3149`, and `novaic-cortex` commit `351ee68`.
- [x] [PR-164B — Explicit payload inspection tools](PR-164B-explicit-payload-inspection-tools.md) — deployed in `novaic-common` commit `2cdffba`, `novaic-agent-runtime` commit `fc18d7c`, and `novaic-cortex` commit `60fe590`.
- [x] [PR-164C — Reasoning and action trace projection](PR-164C-reasoning-action-trace-projection.md) — deployed in `novaic-cortex` commit `c7349b4` and `novaic-app` commit `3887182`.

## Current-State Analysis

Completed 2026-05-02 before PR-164A implementation.

Current live path after PR-163:

- Runtime executes native tools in `task_queue/handlers/tool_handlers.py` and assigns a stable `result_id` for each tool call.
- Runtime `react_actions._build_save_results_tasks` writes each tool call as a Cortex step through `context.append(write_as_step=True)`.
- Cortex `Workspace.write_step` persists the whole step JSON under `steps/` and indexes `result_id`.
- The stored tool step currently carries raw result text in `step.result`. This makes Cortex usable for `read_formatted`, but violates the new architecture rule that Cortex should store default work trajectory, not raw payload bodies.
- Cortex `steps/read_formatted` already acts as the LLM-facing resolver. It finds the step by `tool_call_id` / `result_id`, parses the stored result, and returns provider-shaped `_mcp_content`.
- LLM `reasoning_content` is preserved in assistant messages for replay/debug. It is not yet modeled as a first-class trace projection.
- Agent Monitor already uses product-level execution metadata for normal display, but Cortex itself does not yet expose a clean observation/action/reasoning projection contract.

Conclusion: PR-164A should fix the write shape first. Tool result payloads must be externalized behind a payload ref; the Cortex step should contain a bounded observation percept plus `payload_ref`. Existing LLM result expansion should keep working by resolving the payload ref instead of reading `step.result`.

## Progress Notes

- PR-164A completed the first write-shape cutover: Runtime no longer writes raw `step.result`; Cortex externalizes payloads and rejects inline result payloads for new tool steps.
- PR-164B added explicit `payload_read` and `payload_search` tools. Payload inspection is now a visible tool action and its result flows back through the same Cortex observation/payload path; no auto-summary was introduced.
- PR-164C added Cortex `/v1/trace/project`, projecting provider-authored reasoning, assistant tool-call actions, tool observations, and scope summaries without creating monitor-only generated summaries. App monitor display now covers `payload_inspected`.

## Closure

Closed 2026-05-02. PR-164A, PR-164B, and PR-164C are all deployed; later PR-166 tightened the user-facing projection and removed the backend raw diagnostic payload branch.

## Boundary Invariants

- Cortex owns work trajectory, not external domain truth.
- Raw tool payload is stored by the responsible domain and referenced from Cortex.
- Summary happens only when explicitly requested by the agent or by a deterministic display budget, not as hidden memory inference.
- `summary.md` remains scope-close summary, not a second memory channel.

## Done Criteria

- [x] Observation writes are covered by tests.
- [x] Payload refs are resolvable, bounded, and safe to display.
- [x] Reasoning content is preserved where available and separated from generated summaries.
- [x] No raw MCP/HTTP/debug blobs leak into normal Agent Monitor.
