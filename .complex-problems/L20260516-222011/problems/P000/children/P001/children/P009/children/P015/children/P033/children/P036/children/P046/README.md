# Child Problem: frontend ActivityTimeline legacy detection

## Problem

`ActivityTimeline.tsx` still has scattered raw direct IM token matching. It should centralize legacy tokens and name helper functions as archived compatibility.

## Success Criteria

- Raw direct IM tokens are centralized.
- Helper names and comments clearly say legacy archived direct IM.
- Current shell/agentctl detection remains primary.
- Focused ActivityTimeline tests pass.
