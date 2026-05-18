# normalize_step observation contract audit

## Problem

`normalize_step` is the first gate before tool results become workspace step files. It must reject legacy inline raw `result` fields and require a structured observation/percept shape so raw CLI output, base64, or large JSON cannot sneak into `steps/*.json` as the canonical result.

This child belongs under `P142` because step indexing can only be trusted if the normalized step object has already removed unsafe legacy result fields.

## Success Criteria

- Source pointers map the `normalize_step` implementation and its validation branches.
- Tests or direct evidence prove inline `result` input is rejected for new step writes.
- Tests or direct evidence prove missing/invalid observation input is rejected.
- Residual historical compatibility, if any, is explicitly scoped away from new write paths.
