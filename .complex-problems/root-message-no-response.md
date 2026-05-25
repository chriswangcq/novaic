# Message sent but no response

## Problem

The user reports that sending a message currently produces no response in the NovAIC app. Diagnose where the message path is stuck, design the smallest correct fix, implement it, verify it locally and/or against the deployed environment, deploy through the Release Controller if backend runtime changes are needed, and close the loop with evidence.

## Success Criteria

- Identify the failing stage in the message pipeline with concrete evidence.
- Implement the fix in the correct service or frontend boundary without adding fallback or hidden dual paths.
- Add focused regression coverage or an equivalent guard for the failure mode.
- Verify the fix with relevant tests and deployed service checks.
- Push the fix to GitHub and, when deployment is required, release through the Release Controller.
