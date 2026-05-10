# Phase 5D.2b success check

## Summary

Success. Result `R060` closes the bounded step-formatting and sandbox-contract guard problem with explicit evidence for public `projection` validation, internal-only `include_display` classification, sandbox backing-path rejection, and passing targeted tests.

## Evidence

- `R060` records the inspected public API, projection, schema, sandbox, and sandboxd wiring test files.
- `R060` records the targeted command:
  `PYTHONPATH="novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk" pytest -q novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py novaic-cortex/tests/test_resolve_for_llm.py novaic-cortex/tests/test_tool_schemas_limits.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py novaic-cortex/tests/test_sandboxd_wiring.py`
- Test result was `42 passed in 0.43s`.
- Static evidence showed `include_display` remains in low-level `step_result_projection.py` helpers and related internal tests, while public formatted-step API exposes `projection`.

## Criteria Map

- Guard coverage map is recorded for step formatting public API and sandbox path rejection: satisfied by `R060` static evidence bullets for `test_steps_read_formatted_rejects_unknown_projection`, explicit projection mode tests, shell schema contract, and ephemeral backing-path rejection.
- Relevant tests pass: satisfied by the targeted `42 passed` pytest run.
- Low-level `include_display` internals are explicitly classified separately from public API: satisfied by `R060` summary and verification notes that classify it as an internal rendering detail, not a public formatted-step input.

## Execution Map

- Searched and inspected formatted-step API guards, projection helpers, shell schema contract tests, sandbox mount behavior, and sandboxd wiring.
- Added or confirmed the sandbox behavior guard `test_shell_rejects_ephemeral_cortex_backing_paths_before_execution`, ensuring leaked temp backing paths are rejected before reaching sandboxd or local fallback handling.
- Ran the bounded target test suite for the relevant contract surface.

## Stress Test

- Plausible failure mode: an LLM copies a stale `/tmp/novaic-cortex-sandbox-*` path from old shell output. The sandbox behavior guard exercises exactly that command shape and proves it returns exit `-2`, stable path guidance, no stdout, no changed files, and no fall-through to the missing-sandboxd branch.
- Plausible failure mode: a caller uses the old public `include_display` concept. The public API guard rejects an unsupported projection and the explicit projection-mode tests prove display content only appears through the `display_perception` projection path.

## Residual Risk

- This check is intentionally scoped to `P066`; it does not claim lock/fallback boundary coverage or full Cortex test closure. Those are sibling/downstream problems `P067`, `P063`, and `P064`, so the residual risk is non-blocking for this bounded problem.

## Result IDs

- R060
