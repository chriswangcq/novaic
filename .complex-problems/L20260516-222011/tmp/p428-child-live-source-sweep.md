# Problem: ContextEvent live source residue sweep

## Problem

Live Cortex source may still contain fallback or compatibility paths that bypass ContextEvent projection/payload contracts.

## Goal

Search relevant `novaic-cortex/novaic_cortex` source files for live fallback/direct-inlining residue and classify/fix any real hit.

## Success Criteria

- Search covers ContextEvent, workspace step/payload, API lifecycle, and projection source files.
- Live hits are fixed or split.
- No live unclassified source residue remains.
