# Static Residue Guard Design

## Problem

Define static residue guard terms and scan scope for risky queue/session/FSM legacy or imperative paths.

## Success Criteria

- Guard terms and path scope are explicit.
- Scan command is defined without executing broad destructive actions.
- Expected legitimate hit categories are listed so P512 can classify them consistently.
