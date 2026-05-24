# Configure and document the CI/CD quality gate flow

## Problem

Even after the code supports quality gates, the project needs a clear default contract: local unit tests are fast feedback, Release Controller gates are authoritative staging admission, staging smoke/integration happens after deploy, and prod promotion uses the already accepted immutable release. This child updates sample config, docs, and repository guards so the intended flow is explicit and hard to regress.

## Success Criteria

- `novaic-release-controller/config.sample.json` includes meaningful default quality gates that run in the controller worktree.
- Docs describe the canonical development and CI/CD flow from local tests through staging admission and prod promotion.
- Docs distinguish quality gates, image build/import checks, staging smoke/integration checks, and prod smoke.
- Repository guard tests/lints verify that quality gates are documented and sample config remains aligned with the controller model.
- Manual backend/factory deploy paths remain documented as rejected internal executor paths.
