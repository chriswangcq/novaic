# Migration-like and compatibility-named source audit

## Problem

Migration-like files, compatibility-named modules, or boundary scripts can retain old behavior or misleading names after runtime cleanup.

## Success Criteria

- Inventory migration-like, compatibility-named, legacy-named, and fallback-named source files excluding ledger artifacts.
- Classify retained files as live current boundary, guard script, non-live docs, or unresolved risk.
- Remove or rename misleading live compatibility code if found.
