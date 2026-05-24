# Release Controller Root Not Success Check 2

## Summary

The release-controller is deployed and can poll branch heads through its control-plane API, but the root problem is not fully successful yet. The remaining gap is autonomy: the service should own periodic branch polling and the API host should have the managed worktree needed for non-dry-run staging releases.

## Evidence

- R017 proves the controller package, deploy path, CI guards, API-host deployment, docs migration, and local branch cleanup are in place.
- R018 proves the deployed controller exposes `/v1/polls/once` and can dry-run plan `main -> staging` from branch heads.
- The deployed config still has `dry_run_default=true`.
- Branch polling is currently operator-triggered by `/v1/polls/once`; there is no service-owned background loop using `poll_interval_seconds`.
- The API-host worktree requirement is documented, but the checkout itself has not been bootstrapped and verified for non-dry-run command execution.

## Criteria Map

- Repository contains a documented design and implementation: satisfied.
- Supports branch polling and deterministic branch-to-namespace mapping: partially satisfied; API poll-once exists, but autonomous service polling is missing.
- Supports verification commands, immutable build/publish, deploy execution, state recording, rollback/promotion: satisfied in code and dry-run evidence, but non-dry-run staging path still needs managed worktree proof.
- Containerized and deployable on the API host: satisfied.
- Staging can be triggered from a branch change without GitHub Actions: partially satisfied; branch heads can be polled manually, but the controller does not yet run its own polling loop.
- Prod promotion can use a previously verified immutable image ref: satisfied in implementation and guard coverage.
- GitHub Actions demoted to optional/secondary docs: satisfied.
- Old confusing branch/deploy residue cleaned or archived: satisfied locally by branch cleanup.
- Deployment and verification evidence prove the controller is running: satisfied.

## Execution Map

- Reviewed R017 and R018.
- Compared the deployed behavior against the root success criteria.
- Identified one follow-up needed to close the autonomy gap.

## Stress Test

- A manually callable poll endpoint would still require some other scheduler or human to replace GitHub Actions, which violates the centered controller goal.
- Enabling non-dry-run without a managed checkout would move risk from GitHub Actions to an under-specified host path, which is not a clean long-term release path.

## Residual Risk

- Until the follow-up closes, the release-controller is a safe deployed control plane but not yet the complete primary CI/CD orchestrator.

## Result IDs

- R017
- R018
