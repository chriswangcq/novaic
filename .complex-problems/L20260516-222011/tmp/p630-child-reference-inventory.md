# Workspace Materialize Reference Inventory

## Problem

Before removing `Workspace.materialize()`, the repo needs a fresh reference inventory so deletion does not accidentally remove a current path or leave stale tests unclassified.

## Success Criteria

- Records exact scans for `Workspace.materialize`, `def materialize`, `.materialize(`, and broad `materialize(` hits in `novaic-cortex`.
- Classifies each hit as production API, test fixture, LogicalFS-intended materialization, or unrelated.
- Identifies the precise files that must be edited or deleted in the implementation child.
