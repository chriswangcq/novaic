# Round and stack-depth default classification

## Problem

The widened guard also found stack depth and round number defaults in wake finalization and recovery paths. They are not session generation, but they are control-plane defaults and need conscious classification.

## Success Criteria

- Classify `stack_depth_at_finalize`, `round_num`, and retry/count defaults as safe or patch them with explicit validation where they affect control flow.
- Ensure wake finalize and recovery behavior remains covered by focused tests.
- Final matrix clearly separates session generation authority from harmless display/audit counters.
