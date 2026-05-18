# Test skip TODO and fixture residue scan

## Problem

Tests may contain stale skips, TODO/FIXME markers, compatibility fixtures, or old assertions that keep deprecated behavior acceptable.

## Success Criteria

- Focused scans cover active test directories for skip, xfail, TODO, FIXME, compat, fallback, and legacy markers.
- Hits are classified as intentional coverage, stale acceptance of old behavior, or harmless fixture text.
- Any tiny stale test residue is cleaned directly when safe.
- Risky or broad test rewrites are routed to explicit child/follow-up work.
