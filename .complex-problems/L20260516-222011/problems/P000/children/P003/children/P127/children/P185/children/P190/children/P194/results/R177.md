# Runtime-to-factory multimodal request preservation result

## Summary

Audited and strengthened the runtime-to-factory LLM request boundary. Runtime passes prepared messages through `LLMBusiness` into `FactoryLLMClient.chat`, which posts `json=payload` to `/v1/chat/completions`. Added a focused regression test proving structured `image_url` content survives this boundary and base64 does not move into text fields.

## Done

- Mapped runtime LLM transport path:
  - `novaic-agent-runtime/task_queue/handlers/llm_handlers.py`
    - `handle_llm_call`
    - `_create_factory_client`
  - `novaic-agent-runtime/task_queue/contracts/llm_call.py`
    - `prepare_llm_call`
    - `PreparedLLMCall`
  - `novaic-agent-runtime/task_queue/business/llm.py`
    - `LLMBusiness.call`
  - `novaic-agent-runtime/task_queue/factory_client.py`
    - `FactoryLLMClient.chat`
- Added `novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py`.
- The new test captures the outbound Factory JSON payload and verifies:
  - `messages[0].content[0]` remains `{"type": "image_url", "image_url": {"url": ...}}`;
  - base64 payload does not appear in any `text` field.

## Verification

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py
```

Result: `10 passed in 0.09s`.

## Known Gaps

- This ticket proves runtime-to-factory preservation only. Factory/provider downstream conversion is P195.

## Artifacts

- `novaic-agent-runtime/task_queue/factory_client.py`
- `novaic-agent-runtime/task_queue/handlers/llm_handlers.py`
- `novaic-agent-runtime/task_queue/business/llm.py`
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py`
