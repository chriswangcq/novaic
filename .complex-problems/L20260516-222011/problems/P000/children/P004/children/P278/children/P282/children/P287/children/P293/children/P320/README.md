# Consolidate session residue scan classification

## Problem

Combine direct SQL and wrapper/compat scan findings into a final classification for P293. Ensure no risky production residue is hidden behind docs/tests/no-match evidence.

## Success Criteria

- The final classification references child scan results and lists any open risky/removable residue.
- If children found no active residue, explain why remaining matches are legitimate or inert.
- If children found residue, create or point to the cleanup follow-up before parent success.
