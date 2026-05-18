# Queue/runtime stale entrypoint cleanup and verification

## Problem

Using queue/runtime role maps, search for stale duplicate entrypoints, retired worker names, misleading old comments, or unreferenced launch surfaces in queue-service and agent-runtime code. Apply low-risk cleanup where evidence is strong.

## Success Criteria

- Stale/duplicate queue/runtime entrypoint candidates are searched with evidence.
- Low-risk stale residues are removed or clarified; risky leftovers are recorded as residual risk.
- Focused tests, compile/import checks, or guard scans pass for changed files.
