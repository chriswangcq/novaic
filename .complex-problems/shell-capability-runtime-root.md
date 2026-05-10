# Shell capability runtime substrate

## Problem

The tool-shell boundary design requires interface/runtime style capabilities to move into shell-accessible commands while keeping only minimal harness primitives outside shell. The current sandbox exposes stable `/cortex/ro` and `/cortex/rw`, but it does not provide a reliable generic command substrate such as `agentctl`, `runtimectl`, or `cortex`.

This leaves the architecture only partially implemented: the agent can run shell, but shell is not yet a first-class capability surface for runtime/cortex operations.

## Success Criteria

- Fresh sandbox executions have stable commands on `PATH`: `agentctl`, `runtimectl`, and `cortex`.
- `agentctl --help`, `runtimectl --help`, and `cortex payload --help` work without materializing the full RO tree.
- Commands are generated inside each disposable sandbox and read auth/config from the stable shell environment rather than leaked ephemeral paths.
- Tests prove the commands are present, stable-path-safe, and do not require RO for help/smoke usage.
