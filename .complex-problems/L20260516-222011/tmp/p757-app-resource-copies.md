# App resource copy residue discovery

## Problem

Scan app-bundled resource/generated copies that mirror Sandbox or VMuse code for stale residue that could ship even if source repos are clean. This belongs under P757 because generated/resource copies have previously duplicated active VMuse code and can preserve removed imports or media behavior.

## Success Criteria

- Relevant app resource/generated copies are discovered and scanned with bounded commands.
- Suspicious hits are classified as generated mirror, stale copied residue, or unrelated app resource vocabulary.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.
