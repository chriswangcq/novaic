# Current docs stale tool reference inventory

## Problem
The docs cleanup needs a precise inventory that separates stale active guidance from acceptable neutral/internal/historical references before editing many files.

## Description
Run a focused read-only scan over current docs excluding `docs/roadmap/tickets/**`, classify each hit family, and identify exact edit targets.

## Success Criteria
- Each docs hit family is classified as edit, acceptable residual, or historical exclusion.
- Patch target files are listed.
