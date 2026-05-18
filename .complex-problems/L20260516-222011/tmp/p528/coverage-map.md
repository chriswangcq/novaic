# P528 Coverage Map

## Selected Coverage Areas

- Unit task queue tests: every selected `tests/unit/task_queue/test_*.py` file from P513.
- Shell/tool-output contract: `test_shell_output_contract.py`, `test_tool_output_contract.py`, `test_tool_handlers_display_chat_history.py`, `test_tool_handlers_failure_event.py`.
- Retry/replay/idempotency: `test_retry_policy_and_idempotency.py`, `test_high_concurrency_retry_replay.py`, `test_dedup_guard_failure_path.py`.
- Saga worker boundary: `test_saga_worker_boundary.py`.
- Multimodal/history injection/user content: `test_factory_client_multimodal.py`, `test_no_historical_tool_image_injection.py`, `test_user_content.py`.
- Explicit dependency boundary: `test_queue_explicit_dependencies.py`.
