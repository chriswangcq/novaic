# Cortex Shell Step and Payload Persistence Boundary

## Problem

Audit Cortex step/payload recording for shell results to confirm full details are recoverable through RO/payload references while normal LLM history uses bounded previews.

## Success Criteria

- Records scans for Cortex step write, payload ref, preview/head/tail, and RO step persistence logic.
- Cites code/test slices proving full output is stored outside normal history text when needed.
- Classifies payload refs and full-output files as intended or risky.
- Creates follow-up if durable shell history stores raw media bytes inline.
