# T095 Result: Active Docs Final Residue Sweep

## Summary

Ran a final active-doc sweep beyond architecture/reference/runbooks, cleaned additional stale current-guidance wording, and classified remaining hits as intentional target-design constraints or historical phase records.

## Scope

Active docs under `docs/`, excluding `docs/roadmap`, `docs/archive`, and `docs/mcp-vmuse`.

## Commands Run

```bash
find docs -type f -name '*.md' | rg -v '^docs/roadmap/|^docs/archive/|^docs/mcp-vmuse/'
rg -n "TODO|FIXME|compat|fallback|legacy|migration|old[-_ ]path|direct[-_ ]tool|base64|back-compat|shim|temporary|sunset" $(cat /tmp/novaic-active-docs.txt)
```

## Changes

- `docs/cortex/boundary-contract.md`: changed legacy proxy surface wording to retired proxy surface wording.
- `docs/cortex/builtin-tools-and-skills.md`: removed legacy config wording from the source note.
- `docs/cortex/context-event-write-cutover-map.md`: added a status banner marking the file as historical cutover archaeology.
- `docs/entangled/protocol-layer-and-ws.md`: replaced client fallback wording with “stop using that sync path or log”.
- `docs/blob-service-architecture.md`: changed deleted-path compatibility branch wording to replacement-branch wording.
- `docs/vmcontrol/webrtc-unification.md`: changed legacy display protocol wording to retired display protocol wording.

## Findings

- Remaining scan hits are intentional no-fallback/no-compatibility constraints, historical phase ledgers, protocol names such as `S3-compatible`, or binary/base64 anti-pattern guidance.
- No unresolved active doc was found telling operators or developers to use an old path as the current path.

## Verification

- Final active-doc scan completed after cleanup.

## Result

Active docs final sweep closed additional current-guidance residue and classified the rest.
