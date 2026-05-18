# Cortex step storage and projection ref contract

## Problem

Cortex workspace step writes and context projections persist tool results for later lookup. This layer must keep `step_ref` stable for step lookup and preserve actual/externalized `payload_ref` metadata without corrupt JSONL, hidden fallback, or ambiguous index entries.

## Success Criteria

- Map Cortex `write_step`, step index, context projection, and step read code around `step_ref`, `payload_ref`, and artifacts.
- Document how step index entries should represent stable step identity versus actual payload storage.
- Run focused Cortex tests for step index, context writes, corrupt JSONL fail-closed behavior, and artifact metadata.
- Fix or split any ambiguous duplicate-key behavior.
