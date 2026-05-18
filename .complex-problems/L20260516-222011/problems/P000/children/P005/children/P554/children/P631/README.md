# Legacy RW Scratch Layout Cleanup

## Problem

The old root-level `/rw/scratch` layout is classified as legacy residue around direct materialization. It should not remain as a default semantic path if the current model is subagent-aware LogicalFS-mounted RW layout.

## Success Criteria

- Scans all `/rw/scratch`, `scratch`, and related workspace layout usages.
- Classifies each hit as current intended scratch behavior, test fixture, or removable legacy layout.
- Removes or updates high-confidence legacy `/rw/scratch` assumptions and tests.
- Keeps any current scratch behavior explicitly justified and covered by tests.
