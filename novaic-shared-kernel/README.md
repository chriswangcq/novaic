# novaic-shared-kernel

Week 1 bootstrap package owned by Platform Team.

## Goal

Provide an installable shared kernel package entry point for common backend
modules, and define a stable target for cross-repo import migration.

## Current State (v0.1.0-rc1)

- Package is installable with `pip install -e ./novaic-shared-kernel`.
- Exposes `common` namespace.
- Migrated core modules into package source:
  - `common.config`, `common.strict_config`
  - `common.exceptions`, `common.enums`
  - `common.db`, `common.http`, `common.utils.time`
- Keeps a transitional fallback bridge for unmigrated modules.

## Next Milestone

- Publish `v0.1.0rc2` after completing remaining module migration.
- Remove fallback bridge once all modules are package-native.
- Publish immutable internal package artifacts.
