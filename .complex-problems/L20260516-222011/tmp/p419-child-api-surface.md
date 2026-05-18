# Problem: Cortex API surface cleanup

## Problem

Cortex API endpoints may retain old compatibility paths or projection bypasses even after core lifecycle cleanup.

## Goal

Inventory and verify API endpoints that touch context, scope lifecycle, steps, payloads, and internal tools.

## Success Criteria

- API surface inventory saved and classified.
- No live API bypass remains unclassified.
- Focused API tests/guards pass.
