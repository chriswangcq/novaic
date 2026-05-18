# Problem: Cortex bridge surface cleanup

## Problem

Runtime bridge clients may still call old Cortex endpoints, full-payload reads, or compatibility paths.

## Goal

Inventory and verify runtime bridge usage of Cortex API.

## Success Criteria

- Runtime bridge call sites are inventoried.
- Calls use current explicit endpoints/projection modes.
- Focused runtime bridge tests/guards pass or gaps are split.
