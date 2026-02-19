# Week 1 Task Order - API Team

## Team
API Team

## Mission
Make `gateway` independently buildable and stable as public API owner.

## Scope
- Create `novaic-gateway` repo
- Migrate gateway code and startup entrypoints
- Replace cross-repo source imports with API clients
- Convert service endpoints to environment-driven config
- Keep outward API behavior stable for Week 1 baseline

## Execution Plan (D1-D5)
- D1: Initialize repo, move gateway modules, enable basic app startup
- D2: Remove direct source-level dependencies on workers/runtime/tools repos
- D3: Define minimum stable API surface and config variables
- D4: Add CI pipeline (`lint`, `test`, `build`) and fix migration issues
- D5: Publish `v0.1.0-rc1` and release notes with known breaking changes

## Acceptance Criteria
- Repo can run independently with env-based downstream URLs
- No cross-repo source imports remain
- Core API smoke tests pass
- CI green on default branch

## Deliverables
- `novaic-gateway` repo
- environment variable spec (`README` or `docs/config.md`)
- API surface inventory
- `v0.1.0-rc1` tag

## Dependencies and Coordination
- Coordinate with Platform Team for shared package and contracts
- Coordinate with Runtime/Tools/Storage teams for downstream URL contracts

## Risk Escalation
- If API behavior changes break core workflows, freeze merge and escalate immediately
