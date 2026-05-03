# PR-193B — Runtime Agent Activity Projection Write Path

Status: closed

## Analyze

Runtime already owns the moments where Cortex receives durable trace data: assistant LLM responses, tool observations, and skill summaries. The Monitor projection should be materialized on that write path so the App can receive Entangled deltas without polling Cortex.

## Small Work Orders

1. Add a Runtime projection writer that appends/upserts public Agent Activity rows through Business internal entity APIs.
2. Materialize assistant reasoning/tool-call action records when LLM responses are appended to Cortex.
3. Materialize tool observation records when tool steps are written to Cortex.
4. Materialize scope summary records when `skill_end(report=...)` closes a scope.
5. Upsert a participant projection for every emitted record.

## Tests

- Runtime unit tests for assistant message projection.
- Runtime unit tests for tool observation projection.
- Runtime unit tests for skill summary projection.
- BusinessClient entity upsert/append API tests if needed.

## Acceptance

New Agent Monitor records arrive as Entangled entity writes during normal runtime execution. No read-side query to Cortex is needed for live monitor updates.

## Closure

Closed 2026-05-03. Runtime projects assistant reasoning, tool-call actions, tool observations, and `skill_end(report=...)` summaries to Business entity upserts.
