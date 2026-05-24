# Discover and design release-controller architecture

## Problem Definition

The controller must sit on top of the existing namespace-aware Docker deployment substrate without duplicating service discovery, nginx, or backend deployment logic. We need a concrete design before writing service code.

## Proposed Solution

Inspect the current deploy script, Docker platform, namespace runtime, docs, and live host assumptions. Write a design document defining controller responsibilities, branch rules, run lifecycle, state files, commands, safety gates, API surface, deployment shape, and non-goals.

## Acceptance Criteria

- Design document exists in `docs/architecture`.
- Design explicitly maps branches to namespace behavior.
- Design defines durable state and release pointer files.
- Design states prod safety/promotion rules.
- Design explains how the controller calls existing image deploy paths.
- Design records what remains outside the controller.

## Verification Plan

Review the design against current `deploy`, Docker Compose packages, runbook, and current prod/staging runtime assumptions. Run a grep sanity check for required sections and branch rules.

## Risks

- Over-designing a controller that replaces already-working deploy logic would increase risk.
- Under-specifying prod rules could create accidental prod deployment paths.

## Assumptions

- Existing `./deploy services-image` and `./deploy factory-image` remain the only deployment authority for backend releases.
