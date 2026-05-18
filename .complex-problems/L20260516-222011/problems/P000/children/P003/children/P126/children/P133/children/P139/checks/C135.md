# ContextEvent pure projection success check

## Summary

Success. R121 maps the pure projection module with line-level source pointers, runs the dedicated projection suite, and explicitly scopes remaining display/shell/provider behavior to sibling problems. The one-go result is acceptable because this slice is a pure function plus one focused test file.

## Evidence

- Source map includes projection loop, replay validation, all relevant event handlers, stack folding, tool result metadata, and content selection.
- Dedicated command passed:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_projection.py
```

- Test result:

```text
29 passed in 0.07s
```

## Criteria Map

- Projection invariants for stream/root/sequence validation are documented:
  - Satisfied by R121 mapping of `context_event_projection.py:68-90`.
- Event handlers for wake, skill, system, context messages, notifications, assistant tool calls, and tool results are mapped:
  - Satisfied by R121 `Done` section covering event handler line ranges.
- The roles of `step_ref`, `payload_ref`, orphan tool result marking, and folded summary messages are documented:
  - Satisfied by R121 pointer behavior, orphan marking, and skill summary mapping.
- Projection tests are run and any active issue is fixed or split:
  - Tests passed. No pure projection issue was found.

## Execution Map

- Inspected `novaic-cortex/novaic_cortex/context_event_projection.py`.
- Inspected `novaic-cortex/tests/test_context_event_projection.py`.
- Ran the full focused projection test file.
- Recorded R121 with source pointers and explicit known gaps.

## Stress Test

- Plausible failure mode: externalized payloads lose stable lookup refs and force callers to chase blob refs as tool-call join keys.
  - Covered by `test_project_context_events_uses_stable_step_ref_when_payload_is_externalized`.
- Plausible failure mode: stale child-skill or old-wake messages remain in LLM context.
  - Covered by stale wake/sibling/descendant suppression tests.
- Plausible failure mode: tool result appears without matching assistant tool call and is silently treated as normal.
  - Covered by orphan tool result marking test.
- Plausible failure mode: notification projection fetches full user message body too early.
  - Covered by notification hint test that projects only an instruction to use `agentctl im read`.

## Residual Risk

- Non-blocking: `_tool_result_content` can fall back to stable JSON for observations without `preview`, `summary`, or `head`; whether any active tool sends large observations into this fallback belongs to the step-result/shell/display projection sibling problems.
- Non-blocking: Provider-native image construction is outside this pure projection layer.

## Result IDs

- R121
