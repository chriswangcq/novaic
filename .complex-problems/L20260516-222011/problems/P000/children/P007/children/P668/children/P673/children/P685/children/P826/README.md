# CI guard topology alignment

## Problem

30+ CI lint scripts in scripts/ci/ check service boundaries, retired paths, and topology assumptions. These guards must reflect the current topology, not stale assumptions.

## Success Criteria

- CI guards that reference service boundaries or topology are identified.
- Guards checking for stale/retired paths are current.
- Running the relevant CI guards produces no false positives or stale failures.
