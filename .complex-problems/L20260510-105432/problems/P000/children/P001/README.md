# Audit generic versus Cortex-specific sandbox pieces

## Problem

Before extracting, identify which parts of `novaic-cortex` shell execution are truly business-agnostic and stable enough for common infrastructure.

## Success Criteria

- Each candidate is classified as common infrastructure or Cortex-specific.
- The target common module names and public APIs are listed.
- Non-candidates are explicitly protected from extraction.
