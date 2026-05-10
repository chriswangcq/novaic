# Device tool shell cutover success check

## Status

success

## Results Checked

- R000

## Evidence

- LLM-facing schema source prints exactly `['shell', 'skill_begin', 'skill_end', 'display', 'sleep']`.
- Runtime context preparation no longer imports or calls `fetch_mounted_device_tool_schemas` / `merge_tool_schemas`.
- Guardrail search shows mounted device fetch/merge code remains only in the old compatibility module, not in `cortex_handlers.py`.
- Focused tests passed:
  - `novaic-agent-runtime`: `26 passed`
  - `novaic-cortex`: `21 passed`
  - `novaic-common`: `11 passed`

## Criteria Map

- Device tools are no longer mounted into LLM context as dynamic schemas: satisfied.
- Device capability remains executable through shell: satisfied by `devicectl hd shell-exec` round-trip test.
- Shell capability receives explicit Device URL dependency: satisfied by `NOVAIC_DEVICE_URL` capability env and sandbox allowlist.
- Tests prevent silent old-path reactivation: satisfied by the context-prepare smoke test that raises if mounted device schema fetch is called.

## Execution Map

- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`: removed mounted-device schema merge from prepare.
- `novaic-agent-runtime/task_queue/tool_surface_policy.py`: marked `hd_*` tools as schema-cutover shell capability tools.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`: passes `NOVAIC_DEVICE_URL` to shell capabilities.
- `novaic-cortex/novaic_cortex/sandbox.py`: exposes `devicectl` in the shell capability layer.
- Tests updated in Runtime, Cortex, and Common.

## Stress Test

- The test suite now fails if Runtime tries to fetch mounted device schemas while preparing LLM context.
- The Cortex shell capability test verifies the actual HTTP path and body emitted by `devicectl hd shell-exec`.

## Residual Risk

- Direct Runtime device executors and the mounted-device schema helper still physically exist as compatibility residue. They are not LLM-visible after this check, but they should be removed in the broader physical-cleanup phase to match the user's no-compatibility principle.
