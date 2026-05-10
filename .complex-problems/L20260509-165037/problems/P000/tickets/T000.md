# Add explicit capability environment transport

## Problem Definition

Shell commands need scoped runtime/business context, but the shell request currently only carries command and timeout. Passing hidden globals or reading process environment inside Cortex would violate the explicit dependency boundary.

## Proposed Solution

Add an explicit `env`/capability environment field to the Runtime → Cortex shell request path:

- Runtime constructs a small allowlisted context from known payload/dependency fields.
- `CortexBridge.shell_exec()` sends it in the internal shell request.
- Cortex API accepts the env mapping and forwards it to `Cortex.tool_shell()`.
- `Cortex.tool_shell()` passes it to `Sandbox.exec()`.
- `Sandbox.exec()` filters it through a local allowlist before adding it to process environment.

## Acceptance Criteria

- Capability env includes Business URL, Queue URL, user id, agent id, subagent id, current scope id, wake scope path, and reply cap where available.
- Unknown env keys are dropped at the sandbox boundary.
- Existing shell calls without env still work.
- Tests cover bridge payload and sandbox allowlist behavior.

## Verification Plan

- Add Runtime unit tests for `CortexBridge.shell_exec(..., capability_env=...)`.
- Add Cortex sandbox tests for allowed/dropped env keys.
- Run focused Runtime/Cortex tests.

## Risks

- Passing too much env would create hidden inputs. Mitigation: allowlist only.
- Passing secrets into shell would widen blast radius. Mitigation: do not pass internal service keys in this ticket.

## Assumptions

- Business internal endpoints are reachable by URL from the Cortex shell environment in deployed topology.
