# Week 1 Task Order - Desktop Team

## Team
Desktop Team

## Mission
Make desktop app and vmcontrol independently buildable with minimal observability baseline.

## Scope
- Create `novaic-app-vm` repo
- Migrate `novaic-app` and `vmcontrol` related components
- Remove parent-directory build assumptions
- Switch dependencies to versioned artifacts
- Add startup diagnostics and process observability baseline

## Execution Plan (D1-D5)
- D1: Initialize repo and migrate app/vmcontrol code
- D2: Remove monorepo relative path assumptions from build/runtime scripts
- D3: Configure artifact-driven backend dependency input
- D4: Add startup diagnostics (port checks, process start logs, failure reasons)
- D5: Build `rc` installer and run clean-machine startup validation

## Acceptance Criteria
- App repo builds without root monorepo scripts
- vmcontrol process is started and monitored by app in independent repo
- Startup failure provides actionable diagnostics
- CI passes for build and smoke tests

## Deliverables
- `novaic-app-vm` repo
- build and packaging docs
- startup diagnostics report
- `rc` installer artifact

## Dependencies and Coordination
- Coordinate with API Team for gateway URL contract
- Coordinate with Platform Team for shared config conventions

## Risk Escalation
- If installer cannot complete cold-start validation, block release and escalate
