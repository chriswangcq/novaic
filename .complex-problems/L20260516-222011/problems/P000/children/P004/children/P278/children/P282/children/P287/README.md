# Problem: Session repository state mutation inventory

## Problem

Inspect SessionRepository and SessionLedgerRepository write paths to identify all code that mutates session state, input events, pending projections, and outbox rows.

## Success Criteria

- List mutation methods and their target tables/effects with file references.
- Identify whether writes are grouped in explicit transactions.
- Flag any state mutation outside session ledger/repository boundaries.
