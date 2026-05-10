# SubAgent IM Identity Binding Success Check

## Summary

Success. The design and implementation now make outbound IM identity explicit at the shell execution boundary: same-agent subagents may share the sandbox, but outbound side effects must be signed by the current `NOVAIC_SUBAGENT_ID`, and missing identity fails closed.

## Evidence

- Runtime evidence: `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py` verifies shell capability env carries the current `subagent_id` as `NOVAIC_SUBAGENT_ID`.
- Cortex evidence: `novaic-cortex/tests/test_shell_capability_runtime.py` verifies the same agent/workspace can execute as `sub-alpha` and `sub-beta`, and outbound `agentctl im reply`, `agentctl im send`, and `agentctl subagent spawn` post different `sender_subagent_id` / `parent_subagent_id` values.
- Cortex failure evidence: `novaic-cortex/tests/test_shell_capability_runtime.py` verifies those outbound commands fail with `NOVAIC_SUBAGENT_ID is required` when the env var is absent and do not post HTTP side effects.
- Business API evidence: `novaic-business/tests/test_environment_internal_api.py` verifies missing sender ids produce 422, blank sender ids produce 400, and no messages are appended.
- Residue evidence: `rg` scan found no active-code fallback to `"agent"` or `"main"`; only explicit test fixtures still use `"main"`.
- Test evidence:
  - `novaic-cortex`: 25 passed.
  - `novaic-business`: 30 passed.
  - `novaic-agent-runtime`: 18 passed.

## Criteria Map

- 明确设计 -> same-agent subagents share a team workspace; identity is injected per shell exec through `NOVAIC_SUBAGENT_ID`.
- No silent fallback in `agentctl im reply` / `agentctl im send` / `agentctl subagent spawn` -> `_current_subagent_id()` is required and all three outbound paths use it.
- Business internal IM API requires non-empty sender -> `ImReplyRequest` no longer defaults `sender_subagent_id`; reply/send routes strip and validate it.
- Different subagents in same workspace produce different sender/parent identities -> covered by Cortex per-exec identity test.
- Missing subagent id fails outbound operations -> covered by Cortex parameterized failure test.
- Related Cortex / Business / Runtime tests pass -> all targeted suites passed.

## Execution Map

- T000 / R000 -> implemented the explicit identity contract in Cortex shell CLI, Business internal IM API validation, and Runtime shell env contract tests.
- Verification covered the three dependency boundaries: Runtime injection, Cortex CLI side-effect body, and Business API rejection of implicit identity.

## Stress Test

- Failure mode: a shared sandbox command accidentally sends an IM as `"agent"` or `"main"` because env is missing. Result: fixed by fail-closed `_current_subagent_id()` and Business API requiring explicit sender ids.
- Failure mode: two subagents reuse one agent workspace and produce ambiguous audit logs. Result: fixed by per-exec `NOVAIC_SUBAGENT_ID`, tested with `sub-alpha` and `sub-beta` in the same workspace.
- Failure mode: a caller bypasses the CLI and posts directly to Business without sender. Result: Business API rejects missing/blank sender ids.
- Failure mode: Runtime forgets to pass current subagent id to shell. Result: covered by shell-output contract test.

## Residual Risk

- Non-blocking: direct database mutation or unrelated legacy test fixtures can still mention `"main"` as sample data, but active outbound code paths are hardened by CLI and Business validation.
- Non-blocking: this ticket does not add per-subagent sandbox isolation by design; same-agent subagents are treated as one team boundary.

## Result IDs

- R000

## Blocking Gaps

- none
