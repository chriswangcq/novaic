# Centered branch-driven release controller

## Problem

NovAIC should not depend on GitHub Actions as the long-term CI/CD control plane. Build a centered release-controller that can observe branches, run verification, build immutable images, publish to an internal registry, deploy namespace releases through the existing image-based deploy path, record rollback pointers, expose operational status, and replace manual bootstrap/GitHub Actions dependency as the primary release path.

The controller must be clear, explicit, and maintainable: branch-to-namespace rules should be configuration, release state should be durable, deploys should use immutable image refs, and prod promotion should be intentional rather than accidental. It must fit the current API-host Docker platform where prod/staging already coexist by namespace.

## Success Criteria

- Repository contains a documented release-controller design and implementation.
- Release-controller supports branch polling, deterministic branch-to-namespace mapping, verification commands, immutable image build/publish, deploy execution, release state recording, and rollback/promotion commands.
- Release-controller is containerized and deployable on the API host.
- Staging can be triggered from a branch change without GitHub Actions.
- Prod promotion can use a previously verified immutable image ref.
- Existing GitHub Actions path is demoted to optional/secondary docs, not the primary long-term path.
- Old confusing branch/deploy residue is cleaned or clearly archived without destroying current work.
- Deployment and verification evidence prove the controller is running or, if runtime deployment is blocked, record the smallest explicit follow-up blocker.
