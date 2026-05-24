# P000: Centered branch-driven release controller

Status: followup
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

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

## Subproblems
- P001: Release-controller discovery and architecture design
- P002: Implement release-controller core service
- P003: Containerize and integrate release-controller deployment
- P004: Add release-controller tests and CI guards
- P005: Deploy release-controller to API host and verify
- P006: Migrate CI/CD docs and clean stale branches
- P018: Wire deployed release-controller branch polling
- P019: Enable autonomous branch polling and managed staging release path

## Results
- R017

## Latest Check
C020

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R017: problems/P000/results/R017.md
- Check C018: problems/P000/checks/C018.md
- Check C020: problems/P000/checks/C020.md

## Follow-ups
- P018: Wire deployed release-controller branch polling
- P019: Enable autonomous branch polling and managed staging release path
