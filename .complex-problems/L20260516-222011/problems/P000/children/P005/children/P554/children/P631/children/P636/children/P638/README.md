# Workspace Default RW Layout Cleanup

## Problem

Workspace initialization still creates `/rw/scratch` as a default directory. That is the production layout residue to remove before tests can stop treating it as canonical.

## Success Criteria

- Removes `/rw/scratch` from `Workspace.initialize()` default layout.
- Updates direct initialization assertions to match the current default layout.
- Runs focused Workspace initialization tests.
