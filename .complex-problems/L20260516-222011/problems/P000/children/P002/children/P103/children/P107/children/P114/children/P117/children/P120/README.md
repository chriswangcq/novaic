# Test and Schema Stable Path Residue Classification

## Problem

Tests and schema descriptions may intentionally mention `novaic-cortex-sandbox-*` as a negative guard, but those mentions must be classified and not accidentally teach old path usage.

## Success Criteria

- Search test and schema files for `novaic-cortex-sandbox` mentions.
- Confirm each hit is a negative warning, guard implementation, or test fixture.
- Add or adjust tests if a public schema warning lacks coverage.
