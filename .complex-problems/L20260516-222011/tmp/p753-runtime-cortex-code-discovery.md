# Runtime Queue Cortex service-code residue discovery

## Problem

Discover semantic residue in Runtime, Queue, and Cortex code that could imply outdated ownership of tool dispatch, session FSM, context assembly, shell output, scope lifecycle, or workspace/file authority.

## Success Criteria

- Scans cover `novaic-agent-runtime`, `novaic-cortex`, and related runtime/queue tests.
- Findings distinguish active stale comments/names from intentional guard tests, auth encoders, and shell/display contract code.
- Exact remediation candidates are listed.
- No code is modified in this discovery child.
