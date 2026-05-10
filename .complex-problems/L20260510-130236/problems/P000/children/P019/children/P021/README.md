# Add Generic LogicalFS Live File Authority

## Problem

LogicalFS currently provides materialization/view primitives, but it does not yet own a generic live file authority for realtime `RO` / `RW` reads and writes. The current authority lives in Cortex and knows Cortex persistence details. This belongs under T019 because the final architecture requires LogicalFS, not Cortex, to be the live file boundary.

## Success Criteria

- `novaic-logicalfs` exposes a business-independent live file authority contract for logical path reads, writes, list, delete, append, and move operations.
- The authority accepts explicit owner/layout inputs instead of reading agent/Cortex state implicitly.
- The authority can be backed by a generic object store adapter without importing `novaic-cortex`.
- Unit tests in `novaic-logicalfs` prove path mapping, directory listing, tree moves, append behavior, and invalid path rejection.
- The implementation is not merely copied under a new name with Cortex semantics still embedded.
