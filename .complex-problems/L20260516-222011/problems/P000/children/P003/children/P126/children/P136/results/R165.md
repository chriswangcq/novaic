# Tool result step_ref and payload_ref map result

## Summary

Closed the split investigation for the tool-result `step_ref` / `payload_ref` contract. The split children mapped the runtime wrapper, Cortex durable storage, formatted read/display projection, and cross-layer regression coverage. The resulting contract is: `step_ref` is the stable lookup identity across runtime and Cortex; final `payload_ref` is the actual stored payload identity and may become an external blob ref; public context stays text/manifest-only unless an explicit current display perception projection is requested.

## Done

- P176 mapped runtime tool handlers and confirmed the public/durable split in runtime result dictionaries.
- P177 mapped Cortex step write/index/payload-manifest behavior and confirmed Cortex normalization is the final authority for actual payload refs.
- P178 mapped formatted step reads and display projection, proving `step_ref` lookup resolves the correct final payload while media is injected only through display perception.
- P179 audited regression coverage and remaining ambiguous branches, classifying suspicious fallbacks as active-safe rather than stale.
- Focused runtime and Cortex regression suites were run across the child problems.

## Verification

- Child success checks:
  - P176: C175
  - P177: C176
  - P178: C177
  - P179: C178
- Representative passing suites:
  - P176 runtime wrapper suite: `39 passed in 0.16s`.
  - P177 Cortex suite: `41 passed in 0.43s`; runtime bridge slice: `13 passed in 0.11s`.
  - P178 Cortex projection suite: `14 passed in 0.34s`; runtime projection suite: `26 passed in 0.15s`.
  - P179 cross-layer suites: Cortex `80 passed in 0.55s`; runtime `62 passed in 0.19s`.

## Known Gaps

- No correctness gap remains for this contract.
- Some active-safe fallback code still looks compatibility-like at a glance. It is covered and intentionally retained because it supports explicit payload-ref lookup or historical event replay; deleting it is a separate policy decision, not required to close this mapping problem.

## Artifacts

- P176 result R161 and check C175.
- P177 result R162 and check C176.
- P178 result R163 and check C177.
- P179 result R164 and check C178.
- Production contract files:
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-agent-runtime/task_queue/contracts/react_actions.py`
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - `novaic-cortex/novaic_cortex/workspace.py`
  - `novaic-cortex/novaic_cortex/api.py`
  - `novaic-cortex/novaic_cortex/context_event_projection.py`
  - `novaic-cortex/novaic_cortex/context_event_writer.py`
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
