# Cross-layer context projection regression suite

## Problem

Projection correctness crosses Cortex and agent-runtime. Separate local tests can pass while the integrated flow still leaks or drops media. A final cross-layer regression suite is needed after child fixes to prove the whole contract holds.

## Success Criteria

- The focused Cortex projection tests pass.
- The focused agent-runtime context tests pass.
- At least one integrated or near-integrated test covers shell screenshot manifest output followed by display/current media projection and later historical replay.
- The final check explicitly verifies no raw base64 appears in text history for display/tool results.
- Residual risks are documented with concrete evidence pointers, not broad confidence claims.
