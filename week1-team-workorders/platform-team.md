# Week 1 Task Order - Platform Team

## Team
Platform Team

## Mission
Build the Week 1 foundation for multi-repo delivery:
- `shared-kernel` package
- contract baseline
- compatibility matrix
- reusable CI templates

## Scope
- Create and initialize `novaic-shared-kernel`
- Move shared code (`common`) into installable package structure
- Create `contracts/` skeleton and initial service contract files
- Define and publish `compatibility.yaml`
- Provide CI templates for Python, Rust, and frontend repos

## Execution Plan (D1-D5)
- D1: Create repo skeleton, package metadata, versioning strategy, branch protection
- D2: Move shared modules, fix imports, publish internal package `v0.1.0-rc1`
- D3: Create `contracts/` directory with baseline OpenAPI/JSON schema placeholders
- D4: Create CI templates (`lint`, `test`, `build`) and usage docs
- D5: Publish Week 1 compliance report across all repos

## Acceptance Criteria
- `novaic-shared-kernel` can be installed by package manager
- `compatibility.yaml` exists and is consumed in CI by at least 5 repos
- CI templates are adopted by at least 6 repos
- No repo depends on monorepo relative shared code paths

## Deliverables
- `novaic-shared-kernel` repo
- `contracts/` baseline files
- `compatibility.yaml`
- CI templates + onboarding doc
- Week 1 compliance report

## Dependencies and Coordination
- Works with all teams for import migration
- Supports API Team and Runtime Team first for unblock

## Risk Escalation
- If shared package import breakage blocks 2+ repos for over 4 hours, escalate same day
