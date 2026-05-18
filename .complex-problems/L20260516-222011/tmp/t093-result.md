# T093 Result: Active Architecture Docs Residue Scan

## Summary

Scanned active architecture docs for stale migration/legacy/fallback/compatibility wording, cleaned safe current-guidance wording, and classified remaining hits as intentional principles or historical phase records.

## Scope

- `docs/architecture/*.md`

## Commands Run

```bash
find docs/architecture -type f -name '*.md' | sort
rg -n "TODO|FIXME|compat|fallback|legacy|migration|old[-_ ]path|direct[-_ ]tool|base64|back-compat|shim|temporary|sunset" $(cat /tmp/novaic-architecture-docs.txt)
```

## Changes

- `docs/architecture/attention-points.md`: changed `WatchdogSync` from compatibility wrapper wording to retired guard wrapper wording, and changed the old `tools_server` alias reference to retired wording.
- `docs/architecture/message-wake-principles.md`: changed “main-agent fallback” to “main-agent default route”.
- `docs/architecture/generic-fsm-substrate.md`: changed stale compatibility-helper wording to dual-path-helper wording.
- `docs/architecture/generic-worker-substrate-plan.md`: changed compatibility path/plumbing wording to dual-path/retired-entrypoint wording.
- `docs/architecture/runtime-fsm-worker-dsl-status.md`: changed compatibility/legacy branch wording to dual-path/retired branch wording.

## Findings

- Remaining hits are mostly final-state principles that prohibit fallback/compatibility branches, or historical phase/cleanup records inside design ledgers.
- No active architecture doc was found instructing the runtime to keep an old compatibility branch as current behavior.

## Verification

- Focused architecture-doc rescan completed after cleanup.

## Result

Architecture documentation stale current-guidance wording was cleaned where safe. Remaining residue terms are classified as intentional constraints or historical records.
