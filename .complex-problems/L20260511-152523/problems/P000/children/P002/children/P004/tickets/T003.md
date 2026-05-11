# Pass Cortex internal key to shell capabilities

## Problem Definition

Shell capability commands are trusted runtime-injected tools, but they cannot call Cortex internal APIs because neither runtime nor the capability script forwards the Cortex internal key.

## Proposed Solution

Add `NOVAIC_CORTEX_INTERNAL_KEY` to the explicit shell capability env, allowlist it in Cortex shell capability materialization, and have `_cortex_post` attach `X-Internal-Key` when the key is present.

## Acceptance Criteria

- Runtime shell executor includes `NOVAIC_CORTEX_INTERNAL_KEY` in `capability_env`.
- Cortex shell capability allowlist preserves `NOVAIC_CORTEX_INTERNAL_KEY`.
- `_cortex_post` sends `X-Internal-Key` only for Cortex internal requests.
- Tests cover env propagation and request-header behavior.

## Verification Plan

- Add or update unit tests in runtime shell output contract tests.
- Add Cortex shell capability tests for allowlist/header behavior.
- Run targeted tests for these files.

## Risks

- Internal key should not be sent to business/device/blob services.
- Internal key should not be included in user-visible shell output unless a user explicitly prints their environment.

## Assumptions

- The shell sandbox is the trusted boundary for runtime-injected capability commands.
