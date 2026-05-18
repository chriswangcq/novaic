# Agentctl IM CLI Contract Audit

## Problem

Agent-facing IM read/reply/history/search operations should be reachable through `agentctl im ...` from shell and documented in the shell tool surface.

## Success Criteria

- Locate `agentctl im` implementation and command registration.
- Verify read/reply/history/search commands or their intended equivalents exist.
- Verify shell tool schema/docs mention the IM commands agents should use.
- Run focused tests or safe help checks; fix bounded gaps found.
