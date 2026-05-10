# Shell CLI Residue Cleanup Result

## Summary

Removed the previously audited residue from the active/product metadata surface and tightened test coverage around the shell CLI path. The live LLM/Runtime boundary stays small, while stale metadata and the help-only `runtimectl` placeholder are gone.

## Done

- Removed `subagent_list` and `subagent_history` from `RUNTIME_TOOLS` / `BUILTIN_TOOLS`.
- Removed `HD_TOOLS` from `common.tools.definitions` and stopped exporting it from `common.tools`.
- Removed Business host-desktop direct metadata mounting; host desktop capabilities stay behind `devicectl hd`.
- Updated Business subagent list API comment so it no longer claims to back a direct LLM tool.
- Removed `runtimectl` from Cortex sandbox capability command installation and help tests.
- Expanded Cortex shell capability tests to round-trip every HD proxy command:
  - `devicectl hd screenshot`
  - `devicectl hd mouse`
  - `devicectl hd keyboard`
  - `devicectl hd shell-exec`
  - `devicectl hd clipboard-get`
  - `devicectl hd clipboard-set`
  - `devicectl hd file-pull`
  - `devicectl hd file-push`
- Tightened shell schema / prompt text to enumerate the complete HD CLI surface instead of using an ellipsis.
- Added a Common guard test proving `HD_TOOLS` is no longer exported.

## Verification

Inventory after cleanup:

```text
llm ['display', 'shell', 'skill_begin', 'skill_end', 'sleep']
builtin_active ['display', 'sleep']
runtime_metadata ['sleep']
HD_TOOLS removed: ImportError
executors ['display', 'shell', 'skill_begin', 'skill_end', 'sleep']
```

Targeted tests:

```text
novaic-common:
16 passed in 0.06s
10 passed in 0.02s

novaic-business:
14 passed in 0.54s

novaic-cortex:
21 passed in 8.26s

novaic-agent-runtime:
20 passed in 0.15s
```

Residue search after cleanup only finds intentional policy names, prompt text, and negative assertions; no `HD_TOOLS`, `runtimectl`, direct `subagent_list/subagent_history` metadata definition, or HD direct metadata definition remains in active source.

## Known Gaps

- none

## Artifacts

- `novaic-common/common/tools/definitions.py`
- `novaic-common/common/tools/__init__.py`
- `novaic-common/tests/test_tool_definitions_contract.py`
- `novaic-business/business/internal/agent.py`
- `novaic-business/business/internal/subagent.py`
- `novaic-business/business/prompt_defaults.py`
- `novaic-cortex/novaic_cortex/sandbox.py`
- `novaic-cortex/tests/test_shell_capability_runtime.py`
- `novaic-cortex/tests/test_tool_schemas_limits.py`
