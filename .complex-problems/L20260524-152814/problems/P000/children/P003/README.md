# Clean stale workspace path residue safely

## Problem

The working tree contains many stale problem-package paths and temporary files from earlier construction phases. Some may be useful history, some may be obsolete residue, and unrelated user changes must not be destroyed.

## Success Criteria

- Stale local residue is inventoried with path groups and disposition.
- Safe-to-delete residue is removed or archived only when it is not active product code and not needed for the current ledger.
- Current ledger files are preserved.
- Unrelated modified user files are left untouched unless explicitly identified as stale residue for this cleanup.
- Final `git status --short` is explained, including any remaining unrelated dirty files.
