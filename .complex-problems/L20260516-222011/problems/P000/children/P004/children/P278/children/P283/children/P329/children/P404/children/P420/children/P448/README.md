# Final focused Cortex runtime boundary test rerun

## Problem

Final compatibility verification needs an explicit focused test rerun across all changed Cortex/runtime boundary suites after the cleanup stack is complete.

## Success Criteria

- Rerun focused Cortex tests for lifecycle, context event read model, context endpoints, step/payload projection, shell/tool-output contracts, and payload inspection.
- Rerun focused runtime tests for prepare path, materialized projection bridge, explicit contracts, no historical tool image injection, and shell output contract.
- Save test logs with exit status.
- Any failing test is captured as a follow-up problem instead of being ignored.
