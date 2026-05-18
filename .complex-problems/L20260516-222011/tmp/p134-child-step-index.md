# Workspace tool step normalization and index map

## Problem

Tool steps are materialized in `steps/*.json` and indexed in `steps/_index.jsonl`. This path must reject inline raw results, externalize raw payloads, preserve stable step refs, and expose compact index metadata.

## Success Criteria

- `normalize_step`, `write_step`, and `write_step_projection` are mapped with source pointers.
- Tool steps are verified to reject inline `result` and require an observation percept.
- Raw `payload` writes are verified to require `payload_ref`, externalize if needed, and mirror actual `payload_ref` into observation.
- Step index entries are verified to include `step_ref`, `payload_ref`, duration/tool/status, and artifact marker where applicable.
