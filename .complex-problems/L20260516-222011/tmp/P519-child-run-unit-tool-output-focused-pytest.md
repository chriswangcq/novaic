# Run Unit Tool Output Focused Pytest

## Problem

Run pytest for the validated P519 unit/tool-output/task_queue focused target list.

## Success Criteria

- Pytest runs against exactly the P519 target list.
- The log, exit code, collected count, and final summary are recorded.
- Empty-suite and partial-run false positives are rejected.
- Failures are preserved for follow-up.
