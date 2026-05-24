# Add Release Controller CI quality gate

## Problem

NovAIC now has Release Controller-owned backend and LLM Factory deployment, but the quality gate inside that controller is still too thin: local developer unit tests are advisory, while Release Controller preflight only runs lightweight checks before building and deploying staging. The next correct step is to make CI quality enforcement an explicit Release Controller capability, so a pushed commit cannot become a staging release unless controller-run tests/guards pass, and prod promotion remains tied to a release that passed staging.

## Success Criteria

- Release Controller has a clear CI quality-gate model distinct from deploy smoke and direct manual scripts.
- Branch release plans run deterministic controller-owned quality gates before image build and before staging deployment.
- Gate failures block image build/deploy and are recorded as failed Release Controller runs.
- The default/sample configuration includes meaningful repo-level gates that can run in the controller worktree without relying on developer-local state.
- Tests cover quality-gate planning, execution ordering, and failure behavior.
- Documentation explains the development flow: local unit tests for fast feedback, Release Controller CI gate for authoritative staging admission, staging integration/smoke, and prod promotion from the passed release.
- Existing manual backend/factory deployment rejection remains intact.
