# Remove Legacy Tool Surface Residue

## Problem Definition

The shell CLI migration is correct on the active path, but stale product metadata and a help-only shell command still create ambiguity. This violates the "code generation is cheap, residue is expensive" principle: future agents or maintainers can misread old metadata as supported direct tools.

## Proposed Solution

Make a focused physical cleanup:

- Remove `subagent_list` and `subagent_history` from Common builtin tool metadata.
- Remove HD direct tool metadata export/mount path from Common and Business.
- Remove the `runtimectl` placeholder from Cortex sandbox capability commands and tests.
- Expand HD shell CLI tests so every `devicectl hd` proxy path is exercised.
- Tighten shell schema and prompt text to enumerate all HD CLI commands explicitly.
- Update guard tests to assert the old metadata does not reappear.

## Acceptance Criteria

- `BUILTIN_TOOLS` active names are only current supported metadata tools, with no `subagent_list`, `subagent_history`, or direct `hd_*`.
- `common.tools` no longer exports stale `HD_TOOLS`.
- Business builtin-tool filtering no longer imports or mounts `HD_TOOLS`.
- Cortex sandbox no longer installs `runtimectl`.
- `devicectl hd` round-trip test covers all HD proxy commands.
- Runtime/Common/Cortex/Business targeted tests pass.

## Verification Plan

- Inspect active schema/executor inventories after changes.
- Run Common tool definition tests.
- Run Business prompt/tool metadata tests.
- Run Cortex shell capability tests and schema tests.
- Run Runtime tool boundary tests.
- Search for stale direct metadata strings after cleanup.

## Risks

- Removing product metadata may require updating tests that assumed the old UI tool catalog.
- Removing `runtimectl` requires updating help/PATH tests.
- HD metadata removal should not remove the shell CLI `devicectl hd` implementation.

## Assumptions

- Backward compatibility for direct metadata names is not required.
- Host desktop device operations should be exposed to agents only through shell CLI commands.
