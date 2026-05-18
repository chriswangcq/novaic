# P186 success check

## Summary

Success. The historical display/artifact projection branch now has explicit evidence that history receives bounded manifest/text projections, not raw media bytes or provider image messages. The result is narrow but complete for this problem; UI preview rendering is intentionally outside scope.

## Evidence

- `novaic-cortex/tests/test_tool_output_projection.py` verifies `tool-output.v1` image artifacts parse into manifest text with `display(file_url="...")` access hints and that display perception does not inline artifact images.
- `novaic-cortex/tests/test_step_result_projection.py` verifies history projection truncation and separates history from display perception projection.
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py` verifies old display/tool rounds request `history` projection while current display can request `display_perception`.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py` verifies generic and history-projected image-like tool messages do not become provider image messages, while explicit display perception remains the only allowed image injection path.
- Verification commands passed:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py` -> `15 passed in 0.07s`.
  - `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py` -> `23 passed in 0.09s`.

## Criteria Map

- Map history projection for display, artifact, payload, blob, and generic tool outputs: covered by the result's path audit plus Cortex/runtime tests over tool-output artifacts, display payloads, MCP image payloads, generic tool payloads, and projection routing.
- Prove historical display results use history/text projection rather than display perception: covered by `test_expand_messages_for_llm_uses_history_projection_for_old_round` and adjacent projection assertions in `test_pr71_no_tool_retry_context_cleanup.py`.
- Prove artifact manifests survive while raw bytes stay out of public context: covered by `test_tool_output_v1_artifacts_render_as_manifest_text`, display access hint assertions, and no-image-injection tests that preserve placeholders instead of raw data.
- Fix or split any historical projection branch that leaks raw media: no leaking branch was found after the P184/P185/P186 chain; the current tests encode the guardrails that would catch regression.

## Execution Map

- Result `R184` completed the ticket by auditing the projection paths and running focused Cortex/runtime test suites.
- No code write was needed in this ticket because the prior subproblems already established the separation between current display perception and historical manifest projection.

## Stress Test

- Plausible failure mode: a historical display step appears before a new system message or a later tool result and accidentally gets treated as current display perception, injecting image bytes into a future LLM call. The runtime tests cover old-round routing and image-injection denial for history/generic tool messages.
- Plausible failure mode: a `tool-output.v1` image artifact leaks raw bytes through its manifest. The Cortex tests assert artifact manifests include URI/display hints and avoid inline raw artifact images.

## Residual Risk

- Non-blocking: UI thumbnail/preview behavior is not covered here; this problem is about backend LLM/history projection only.
- Non-blocking: provider-specific image formatting is covered by sibling `P190`, not by this historical projection ticket.

## Result IDs

- R184
