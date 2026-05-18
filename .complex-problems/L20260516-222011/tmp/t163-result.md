# Runtime prepare-context regression coverage audit completed

## Summary

Audited the focused runtime regression coverage for stale local continuity, `context.read` projection re-entry, no-wake replay, context-read ordering/by-id behavior, and historical tool-image injection. No additional production gap was found in this audit; the prior source-mapping children already added the missing guard coverage.

## Coverage Map

- Prepare-context authority:
  - `test_pr85_llm_context_smoke_guardrails.py` proves `handle_cortex_prepare_llm_context` uses `bridge.prepare_for_llm` as provider-message authority, rejects incomplete Cortex snapshots, and does not use `context.read` projection as fallback.
  - `test_runtime_explicit_contracts.py` proves `CortexBridge.prepare_for_llm` calls `/v1/context/prepare_for_llm` and LLM payload builders consume the explicit prepared messages/tools snapshot.
- Context ordering and by-id reads:
  - `test_context_read_ordering.py` proves `context.read` does not scan unread message rows and preserves scoped notification ordering.
  - `test_context_read_by_ids.py` proves by-id context read exposes notification hints without fetching message bodies or mutating receipts.
- No-wake replay:
  - `test_pr113_no_wake_im_replay.py` proves retired wake replay markers are absent from hot runtime code and `context.read` does not fetch raw message bodies.
- Historical tool-image injection:
  - `test_no_historical_tool_image_injection.py` proves generic/historical tool image payloads do not become user image messages, display perception is the only image-injection projection, and non-display tools cannot preserve media into public tool content.
- Wake child scope / root prepare boundary:
  - `test_pr67_wake_child_scope.py` proves prepare reads the wake child for notification hints but prepares the agent root snapshot for LLM context.

## Verification

Command:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py \
  novaic-agent-runtime/tests/test_context_read_by_ids.py \
  novaic-agent-runtime/tests/test_context_read_ordering.py \
  novaic-agent-runtime/tests/test_pr113_no_wake_im_replay.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/test_pr67_wake_child_scope.py
```

Result: `47 passed in 0.22s`.

## Covered Regression Modes

- Stale local `messages`/`tools` continuity cannot override prepared Cortex messages/tools.
- `context.read` projection cannot re-enter the provider-message path as an authority fallback.
- No-wake replay markers and raw message body replay paths are guarded against hot-code reintroduction.
- Context-read by-id/order behavior remains notification-oriented rather than history-body replay.
- Historical or generic tool image content cannot be converted into LLM user image input; only explicit display perception can do that.

## Not Covered By This Focused Slice

- Live deployed service E2E, real browser/monitor UI rendering, and real provider request transport are intentionally outside this unit/integration slice.
- Real blob/display artifact availability is covered elsewhere; this audit only checks stale-context and historical-media re-entry contracts.

## Artifacts

- No additional code changes were required in this leaf.
