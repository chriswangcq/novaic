# RW Scratch Usage Inventory

## Problem

Root `/rw/scratch` appears in Workspace initialization and many tests. Before editing, classify which hits encode the old global scratch layout and which are generic arbitrary `/rw` path fixtures.

## Success Criteria

- Records exact scans for `/rw/scratch`, `RW_SCRATCH`, `/rw/subagents`, and `initialize_layout` across Cortex and LogicalFS.
- Classifies every relevant hit into current subagent-aware contract, generic RW fixture, removable legacy layout, or out-of-scope lower-layer test.
- Produces an exact edit target list for cleanup.
