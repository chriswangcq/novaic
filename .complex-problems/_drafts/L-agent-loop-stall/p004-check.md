# Shell internal auth check

## Summary

The shell internal-auth repair satisfies P004: runtime now passes an explicit Cortex internal key to the capability env, and the generated capability script uses it only for Cortex internal POSTs.

## Evidence

- Runtime unit test confirms `NOVAIC_CORTEX_INTERNAL_KEY` is present in `capability_env`.
- Cortex test confirms `_capability_env` allowlists only the Cortex key from the tested inputs.
- End-to-end generated `agentctl im read` test confirms `/v1/meta/read` receives `X-Internal-Key: secret`, while `/internal/environment/.../im/read` receives no `X-Internal-Key`.

## Criteria Map

- Runtime passes key -> proven by `test_shell_success_uses_explicit_tool_output_contract`.
- Cortex allowlist preserves key -> proven by `test_capability_env_allows_cortex_internal_key`.
- Header attached only to Cortex internal request -> proven by `test_agentctl_cortex_internal_calls_attach_internal_key`.

## Execution Map

- `T003` / shell-auth repair -> code and tests completed.

## Stress Test

- If business calls accidentally received the key, the generated-script test would show the header on the business path; it asserts the business path header is empty.
- If the allowlist dropped the key, the explicit allowlist test would fail.

## Residual Risk

- A user can still manually print environment variables from shell; this is inherent to placing a trusted capability secret in the shell process. The contract is explicit and limited to the sandbox capability env.

## Result IDs

- R001

## Blocking Gaps

- none
