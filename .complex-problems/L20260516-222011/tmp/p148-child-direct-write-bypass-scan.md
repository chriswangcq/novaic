# Direct workspace write bypass scan

## Problem

Non-test code should not bypass `normalize_step`/`write_step_projection` with ad hoc step or context writes that can persist raw payload data. A repository-wide scan is needed to catch any remaining active bypass paths.

This belongs under `P148` because projection call-site correctness includes proving old direct write branches are gone or safely scoped.

## Success Criteria

- Repository scan maps all non-test `write_step`, `write_step_projection`, direct `steps/*.json`, and `_index.jsonl` write sites.
- Any non-test direct write is either removed, routed through the workspace boundary, or explicitly justified as non-tool-step behavior.
- Tests or source evidence cover the remaining active paths.
