# Enforce Explicit SubAgent Sender Identity

## Problem Definition

The intended model is that subagents inside one agent share the agent workspace like a team. They do not need internal isolation, but every outbound IM side effect must carry the current subagent identity so replies, subagent-to-subagent messages, and child spawns remain auditable and routable.

## Proposed Solution

- Add a small `agentctl` helper that requires `NOVAIC_SUBAGENT_ID` for outbound IM and subagent spawn operations.
- Use that helper for `agentctl im reply`, `agentctl im send`, and `agentctl subagent spawn`.
- Remove Business API fallback defaults for `sender_subagent_id`; validate non-empty sender ids in reply/send routes.
- Add tests that use one agent/workspace with different `NOVAIC_SUBAGENT_ID` values and verify the posted sender/parent ids differ.
- Add tests proving missing `NOVAIC_SUBAGENT_ID` fails before posting outbound side effects.

## Acceptance Criteria

- No outbound CLI path silently uses `"agent"` or `"main"` as a fallback sender.
- Business internal IM APIs reject empty sender ids.
- Existing shell capability behavior remains intact.
- Targeted tests pass.

## Verification Plan

- Run Cortex shell capability tests.
- Run Business environment internal API tests.
- Run Runtime shell-output/tool boundary tests if affected.
- Search for stale default sender fallbacks.

## Risks

- Tests or internal callers that relied on implicit defaults must be updated to pass sender ids explicitly.

## Assumptions

- Runtime always has the current subagent id in `deps["subagent_id"]` for real shell tool calls.
- Same-agent subagents are allowed to read team context; this ticket only hardens outbound identity/署名.
