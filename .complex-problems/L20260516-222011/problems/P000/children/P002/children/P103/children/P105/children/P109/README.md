# Agentctl Subagent CLI Contract Audit

## Problem

Subagent spawning/coordination should be reachable through `agentctl subagent ...` from shell so direct harness subagent tools are not required for normal agent work.

## Success Criteria

- Locate `agentctl subagent` implementation and command registration.
- Verify spawn and message/coordination command coverage matches the intended shell-first surface.
- Verify shell tool schema/docs mention the subagent commands agents should use.
- Run focused tests or safe help checks; fix bounded gaps found.
