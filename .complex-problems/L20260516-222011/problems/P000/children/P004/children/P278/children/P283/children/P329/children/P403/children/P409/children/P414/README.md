# Cortex handler and bridge residue classification

## Problem

`cortex_handlers.py` and `cortex_bridge.py` contain round/counter/archive hits around Cortex scope archive and context event APIs. They must be classified so Cortex bridge counters do not hide session identity fallback.

## Success Criteria

- Inspect Cortex handler and bridge guard hits.
- Confirm session generation is explicit at scope-end/archive boundaries.
- Classify `round_num` and Cortex counter defaults as non-session counters where safe.
- Patch and test any session identity fallback.
- Run focused Cortex handler/bridge tests.
