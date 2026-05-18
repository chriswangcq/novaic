# P184 Check: shell projection is bounded terminal text

## Summary

Success. The result solves P184 under the stricter one-go standard: shell output creation, durable payload storage, and Cortex projection were mapped; long and media-like stdout are covered by focused tests; and the remaining display/media concerns are explicitly outside this child problem and already split into sibling problems.

## Evidence

- Runtime shell wrapper maps stdout/stderr through bounded terminal text helpers in `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`: `_preview_shell_stream`, `_shell_result_text`, and `_shell_result_output`.
- Runtime shell tests cover large output and media-like output:
  - `test_shell_large_output_is_bounded_in_text_and_raw_in_diagnostics`
  - `test_shell_media_like_stdout_stays_bounded_terminal_text`
- Cortex projection maps durable `tool-step-payload.v1` back to `llm_content`, not raw shell payload, in `novaic-cortex/novaic_cortex/step_result_projection.py`.
- Cortex tests cover durable raw stdout exclusion and media-like shell stdout remaining text-only:
  - `test_tool_step_payload_v1_projects_llm_content_not_raw_shell_payload`
  - `test_media_like_shell_step_payload_does_not_project_as_display_image`

## Criteria Map

- Shell wrapper and projection code are mapped: satisfied by the runtime and Cortex function map in R172 plus the line-level inspection above.
- Bounded/truncated public shell output is verified: satisfied by the 10k stdout test asserting bounded text and truncation metadata.
- Durable full output remains accessible through step/payload storage: satisfied by runtime tests asserting `durable_payload["raw"]["stdout"]` retains the complete large output while diagnostics excludes raw shell payload.
- Focused shell tests pass: satisfied by `26 passed` for runtime shell/tool contract tests and `8 passed` for Cortex projection tests.

## Execution Map

- Result ID `R172` recorded the audit and verification commands.
- No implementation work was needed during this check step.
- The audit kept P184 scoped to shell projection only; display/current media projection remains in P185/P186.

## Stress Test

- The plausible failure mode was historical: base64-like image bytes leaking into text context or being interpreted as media. The current tests explicitly feed `/9j/` plus 10k characters through shell output and assert:
  - text remains bounded,
  - no `data:image/` appears,
  - no display image item is produced,
  - the raw stdout is retained only in durable payload.

## Residual Risk

- Shell and Cortex have two truncation layers, so exact preview lengths can differ by layer. That is acceptable for P184 because the contract is bounded terminal text plus durable raw payload, not byte-identical terminal replay.
- Display/artifact media projection is intentionally not judged here and is covered by sibling tickets.

## Result IDs

- R172
