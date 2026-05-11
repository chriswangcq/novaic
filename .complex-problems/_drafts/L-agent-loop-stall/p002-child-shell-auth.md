# Shell capability Cortex internal auth repair

## Problem

Runtime-injected shell capability commands such as `agentctl im read` call Cortex internal endpoints, but the capability script does not attach `X-Internal-Key`, and runtime does not pass the Cortex internal key into the shell capability environment. This causes deterministic 401 failures from Cortex `/v1/meta/read`.

## Success Criteria

- Runtime shell execution passes `NOVAIC_CORTEX_INTERNAL_KEY` through the explicit capability env when configured.
- Cortex shell capability scripts allow that env key and use it only for Cortex internal requests.
- Regression tests prove `agentctl`/Cortex capability requests carry `X-Internal-Key` without leaking into unrelated business/device calls.
