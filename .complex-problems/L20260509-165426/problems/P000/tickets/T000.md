# Implement agentctl IM commands

## Problem Definition

`agentctl` is now installed in shell and receives runtime context, but it cannot execute IM operations. Direct LLM-facing IM tools therefore cannot be removed yet.

## Proposed Solution

Implement `agentctl im` subcommands inside the generated sandbox command script:

- `agentctl im read [--notification-id ID ...] [--limit N]`
- `agentctl im reply --message TEXT | --message-file PATH`
- `agentctl im send --target ID --message TEXT | --message-file PATH`
- `agentctl im history/search/context`

The command should use:

- `NOVAIC_BUSINESS_URL` for Environment API calls;
- `NOVAIC_API` plus `NOVAIC_USER_ID`/`NOVAIC_AGENT_ID`/`NOVAIC_SCOPE_ID` for Cortex meta reads/updates/counters;
- `NOVAIC_SUBAGENT_ID` for sender identity;
- `NOVAIC_WAKE_SCOPE_PATH` for exact Cortex meta targeting.

## Acceptance Criteria

- Read command returns Environment read JSON and records observed message ids in Cortex meta.
- Reply command blocks when current input ids are unobserved.
- Reply command increments the Cortex `im_reply` counter and blocks when over cap.
- Reply command supports `--message-file`.
- Commands print bounded JSON responses to stdout and return nonzero on command/validation failures.
- Tests use a local fake HTTP server from within the sandbox to verify read and reply behavior.

## Verification Plan

- Add focused Cortex sandbox tests for `agentctl im read` and `agentctl im reply`.
- Run shell capability tests and sandbox sync tests.

## Risks

- Generated script complexity can grow. Mitigation: keep command parser small and add tests.
- This only makes shell commands capable; a later schema cutover is still required to remove direct tools.

## Assumptions

- Business internal Environment endpoints are reachable from the shell process using `NOVAIC_BUSINESS_URL`.
