# Inventory shell capability CLIs

## Problem Definition

The command surfaces for `agentctl`, `cortex`, and `devicectl` are generated from `novaic-cortex/novaic_cortex/shell_capabilities.py`. We need an evidence-backed inventory before changing behavior.

## Proposed Solution

Inspect the shell capability implementation, help text, command dispatchers, and tests. Classify each command by output type and identify commands that can emit screenshots, files, base64, or other large payloads through stdout.

## Acceptance Criteria

- Command inventory includes `agentctl`, `cortex`, and `devicectl`.
- Risks are tied to file/function evidence.
- Confirmed repair targets are listed for the next child problems.

## Verification Plan

- Use `rg`, `sed`, and focused code review over shell capabilities and related tests.
- Record inventory in the result body.

## Risks

- Some command behavior may depend on remote services; classify based on code paths and proxy contracts where local execution is not possible.

## Assumptions

- `shell_capabilities.py` is the active source for shell-exposed CLI commands.
