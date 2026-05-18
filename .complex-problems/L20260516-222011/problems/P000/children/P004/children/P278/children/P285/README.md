# Problem: Session compatibility and legacy residue audit

## Problem

Search for legacy session compatibility branches, old active-session APIs, direct saga creation bypasses, environment or global hidden inputs, and duplicate worker/session configuration that could keep old logic alive after the FSM migration.

## Success Criteria

- List searched residue patterns and matching files.
- Classify each match as active required path, safe legacy/documentation, risky compatibility branch, or removable residue.
- Create or recommend concrete cleanup follow-ups for risky/removable residue.
