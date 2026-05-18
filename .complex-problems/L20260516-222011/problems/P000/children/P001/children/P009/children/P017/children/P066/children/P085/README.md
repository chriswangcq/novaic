# Classify and clean non-monitor App active residue

## Problem

The active-code residue audit closed App monitor cleanup, but `novaic-app` still has non-monitor fallback/legacy/base64/compatibility hits that are not classified in the ledger. These may be benign UI behavior or test guards, but P066 cannot close until each active hit is classified and stale residue is cleaned.

## Success Criteria

- Run a bounded scan over `novaic-app/src` for fallback, compat, legacy, migration/migrate, TODO/FIXME, base64/data URLs, and direct-tool residue.
- Classify each non-monitor hit as active risk, intentional UI behavior, guard/test fixture, benign adapter, or stale residue.
- Apply safe cleanup for stale comments/names where possible without broad UI refactors.
- Run focused App tests/lint or document explicit no-code-change verification for classified benign hits.
