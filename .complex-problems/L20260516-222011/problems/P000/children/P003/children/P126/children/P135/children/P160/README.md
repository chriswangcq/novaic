# Runtime Cortex prepare handler contract map

## Problem

The runtime Cortex handler and bridge translate a saga action into a Cortex `prepare_for_llm` call and return a prepared snapshot. That response shape must be explicit and stable, otherwise later handlers may fall back to local continuity fields.

## Success Criteria

- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py` and `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` are mapped around `prepare_for_llm`.
- The response fields returned to the saga are documented, including messages, tools, active stack metadata, and any compatibility fields.
- Any fallback to `read_context` or local continuity inside the prepare handler/bridge is classified and fixed or split if it can affect provider messages.
- Focused handler/bridge tests are identified and run.
