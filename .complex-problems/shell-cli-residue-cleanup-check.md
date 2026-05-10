# Shell CLI Residue Cleanup Success Check

## Summary

The residue cleanup is complete. Direct active tool surfaces remain minimal, stale product metadata is removed, the help-only `runtimectl` placeholder is gone, and HD shell CLI coverage now exercises every proxy command.

## Evidence

- Inventory shows LLM schemas are `display`, `shell`, `skill_begin`, `skill_end`, and `sleep`.
- Inventory shows Runtime executors are `display`, `shell`, `skill_begin`, `skill_end`, and `sleep`.
- Inventory shows `BUILTIN_TOOLS` active names are now only `display` and `sleep`.
- Inventory shows `RUNTIME_TOOLS` metadata is now only `sleep`.
- Import check confirms `common.tools.HD_TOOLS` is removed.
- Residue search no longer finds `runtimectl`, `HD_TOOLS`, or direct HD metadata definitions in active source.
- Targeted tests passed in Common, Business, Cortex, and Runtime.

## Criteria Map

- Active LLM schemas remain only final outside-shell tools: satisfied by inventory and Runtime/Cortex/Common tests.
- Runtime direct executors remain only final outside-shell tools: satisfied by inventory and Runtime tests.
- `BUILTIN_TOOLS` no longer contains `subagent_list` or `subagent_history`: satisfied by Common inventory and guard test.
- HD direct metadata is no longer exported or mounted: satisfied by removal of `HD_TOOLS` export and Business host-desktop mount branch.
- `runtimectl` is removed: satisfied by sandbox command set and updated Cortex tests.
- `devicectl hd` tests round-trip every HD proxy command: satisfied by expanded Cortex shell capability test.
- Prompt/schema/help text accurately advertises shell CLI surface: satisfied by updated shell schema/prompt strings and tests.
- Targeted tests pass: satisfied.

## Execution Map

- T000 -> R000: one focused cleanup pass removed stale metadata/placeholders, strengthened tests, and verified the resulting boundary.

## Stress Test

- If a future code path tries to import `HD_TOOLS` from `common.tools`, it now fails rather than silently reviving direct HD metadata.
- If a future LLM prompt tries to advertise old direct subagent metadata, Common guard tests catch `subagent_list` and `subagent_history`.
- If `devicectl hd` proxy mappings drift, the all-subcommand round-trip test checks concrete endpoint paths and request bodies.
- If `runtimectl` is reintroduced as a placeholder, the command path/help tests would need explicit updates, making the decision visible.

## Residual Risk

- The repo still has many pre-existing uncommitted changes from the broader shell/FSM migration. This cleanup did not attempt to revert or normalize unrelated work.
- VM/mobile direct metadata remains by design outside this ticket; this ticket specifically closed the audited residuals for subagent metadata, HD host desktop metadata, and `runtimectl`.

## Result IDs

- R000

## Blocking Gaps

- none
