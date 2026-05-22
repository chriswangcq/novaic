# Classify SQLite state owners and stale residue

## Problem

Current SQLite files include both active state and likely residue. Before migration or cleanup, each file and major code path must be classified with evidence so that cleanup does not delete current state and future agents do not follow stale paths.

## Success Criteria

- Every SQLite file under `/opt/novaic/data` and `/opt/novaic/llm-factory/data` is classified as active, projection/cache, migrate candidate, archive/delete residue, or defer.
- Evidence includes size, mtime, tables, row counts, runtime process owner, startup path, and code references.
- `business.db` and `device.db` receive explicit disposition decisions.
- Any retained residue is labeled or documented so it no longer appears to be a current state owner.
