# Disable automatic Release Controller branch polling

## Problem
The live Release Controller currently runs autonomous branch polling, so pushes to main can trigger staging CI/CD without an explicit agent/operator release action. For the current agent-driven workflow, CI/CD should be a centralized service flow, but it should start only from explicit Release Controller API requests.

## Success Criteria
- Live Release Controller has autonomous polling disabled and reports polling.enabled=false/running=false.
- Repository docs describe explicit trigger-based staging CI/CD as the normal path.
- Repository guards fail if sample config or docs reintroduce autonomous polling as the normal backend/factory release path.
- Existing Release Controller unit/CI guard tests pass.
- A subsequent push to main does not auto-start a new release run.
