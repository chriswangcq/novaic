# CortexBridge prepare_for_llm endpoint contract map

## Problem

`CortexBridge.prepare_for_llm` is the runtime client boundary for the ContextEvent-backed prepare endpoint. It must call the correct Cortex API with explicit tenant fields and not silently fall back to materialized context reads.

## Success Criteria

- `cortex_bridge.py` `prepare_for_llm` is mapped with line pointers for endpoint path and payload fields.
- The return/passthrough shape is documented.
- Any bridge fallback to `read_context` for prepare is classified and fixed or split if active.
- Focused bridge/handler tests are identified and run.
