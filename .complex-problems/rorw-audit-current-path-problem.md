# Audit Current RO/RW Mount Path

## Problem

Establish the current facts: how shell execution creates temporary RO/RW directories, how it decides whether RO is needed, how it copies data, how it persists RW, and where repeated per-command work lives.

## Success Criteria

- Identify the exact code path from Runtime shell tool to Cortex shell execution.
- Explain RO/RW materialization and RW persistence mechanics.
- List confirmed bottlenecks and current mitigations with code references.
