# Child Problem: backend activity projection legacy labels

## Problem

`activity_projection.py` keeps direct-tool labels for old archived records. The map should be explicitly historical compatibility, not a generic active tool-label registry.

## Success Criteria

- Legacy direct-tool labels are behind explicit archived/historical naming.
- Current shell/desc behavior remains primary.
- Focused runtime activity projection tests pass.
