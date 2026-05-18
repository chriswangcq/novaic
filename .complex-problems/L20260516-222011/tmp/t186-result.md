# End-to-end display screenshot regression result

## Summary

Audited the deterministic backend contract chain for shell screenshot artifact -> display perception -> runtime image message -> factory/provider request/log handling. The chain is covered by focused tests across runtime, Cortex, and Factory; no live device smoke was required for this contract-level regression.

## Done

- Coverage map:
  - Shell/device output contract:
    - `test_shell_output_contract.py` verifies terminal text is bounded and artifacts/raw output are not leaked into public text.
  - Cortex projection:
    - `test_tool_output_projection.py` and `test_step_result_projection.py` verify display perception image content and history manifest behavior.
  - Runtime context/multimodal assembly:
    - `test_no_historical_tool_image_injection.py` verifies display media becomes a user image message while the tool result becomes placeholder-only, including active-stack-after-display order.
  - Runtime-to-factory transport:
    - `test_factory_client_multimodal.py` verifies Factory request payload preserves structured `image_url`.
  - Factory provider/log handling:
    - `test_chat_routes.py` verifies OpenAI-compatible provider payload preservation and Anthropic conversion.
    - `test_log_routes.py` verifies backend detail body remains structured and redacted.

## Verification

- Runtime contract chain:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py
```

Result: `16 passed in 0.09s`.

- Cortex projection chain:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_step_result_projection.py
```

Result: `15 passed in 0.07s`.

- Factory provider/log chain:

```bash
pytest -q \
  novaic-llm-factory/tests/test_chat_routes.py \
  novaic-llm-factory/tests/test_log_routes.py
```

Result: `16 passed in 0.23s`.

## Known Gaps

- This is deterministic backend contract coverage, not a live HD screenshot smoke. Live device availability and UI display behavior are outside this ticket.

## Artifacts

- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`
- `novaic-llm-factory/tests/test_chat_routes.py`
- `novaic-llm-factory/tests/test_log_routes.py`
