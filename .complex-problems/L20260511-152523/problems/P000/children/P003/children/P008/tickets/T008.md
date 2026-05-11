# Verify live repaired agent loop path

## Problem Definition

After deployment, production must be checked for the exact old stall signatures and for basic repaired shell/context behavior.

## Proposed Solution

Inspect production queue/session state and logs after deployment, then run a direct Cortex shell capability smoke that exercises `agentctl im read` through the deployed shell capability script with internal auth.

## Acceptance Criteria

- No new post-deploy `missing or invalid X-Internal-Key`, `Tool message missing step_ref`, or `no active root scope` recurrence appears in runtime/Cortex logs.
- Direct shell capability smoke returns successfully and does not produce the old 401.
- Queue/session state is understood after restart; if a stale active state remains, record it as a follow-up instead of pretending recovery is complete.

## Verification Plan

- Query production queue DB for session/saga state.
- Grep post-deploy logs for old signatures.
- Call Cortex `/v1/internal/shell` on production with `agentctl im read --limit 1` and explicit capability env.

## Risks

- A direct smoke may not fully simulate UI dispatch/LLM provider behavior.
- Existing stale session may require a recovery event if no new user message has arrived.

## Assumptions

- Production internal key can be read on the server from deployed `services.json` for local-only smoke.
