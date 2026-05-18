# App backend startup graph audit

## Problem
Before editing backend startup scripts, map the current app backend script/config/resource/port graph and identify concrete inconsistencies.

## Success Criteria
- Current start-backends scripts and generated packaged variants are listed.
- Current service ports and vmcontrol/Cortex naming are mapped from source evidence.
- Backend binary/resource expectations are compared against committed resources.
- No code is edited in this audit step.
