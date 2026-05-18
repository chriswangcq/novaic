# Child Problem: Cortex display step-result projection contract

## Problem

Audit Cortex/step-result formatting paths used by display to verify current-round display perception can expose media to runtime, while history/default projections expose bounded text and placeholders only.

## Success Criteria

- Records scan commands for step result formatting, projection mode handling, and display-specific projection code.
- Reads relevant Cortex/runtime bridge slices with line references.
- Classifies current perception and history projection behavior.
- Forwards any path that can replay display image bytes as ordinary text to P554.

