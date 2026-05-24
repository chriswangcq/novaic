# Upgrade remote Release Controller and verify controller-only deployment

## Problem

After the controller-only commit is pushed, the API host must run a Release Controller image built from that commit before staging/prod deployment paths are exercised. The final state must prove that backend/factory releases go through the controller, manual deploy paths fail, and polling is enabled.

## Success Criteria

- API host Release Controller image is rebuilt/pushed/deployed from the controller-only commit.
- Staging is deployed through Release Controller and healthy.
- Prod remains in immutable promote/rollback pointer state, promoted to the current release if needed, and healthy.
- Manual backend/factory deploy commands fail locally before remote side effects.
- Release Controller health/status are clean and polling is enabled.
