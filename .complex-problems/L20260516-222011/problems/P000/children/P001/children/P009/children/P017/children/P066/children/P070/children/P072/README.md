# Cortex common active PR history comment cleanup

## Problem

During `P070`, active Cortex/Common implementation files still showed PR-era history comments and migration breadcrumbs. Some may be harmless explanatory context, but active code should prefer current contract comments over old PR archaeology.

## Success Criteria

- Active implementation comments in `novaic-cortex/novaic_cortex` and `novaic-common/common` are scanned for PR/migration/history residue.
- Small high-confidence comment cleanups are applied where they do not remove current behavior explanation.
- Remaining PR/history references are classified as tests, module-level design records, or legitimate current-contract references.
- Focused tests or import/scan checks verify the cleanup.
