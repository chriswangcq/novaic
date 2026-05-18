# Deployment script candidate classification

## Problem

Classify the scan artifacts into active scripts/configs, test-only files, docs/historical references, and ignored/generated residue. Produce a concise evidence-backed classification that P676 can use for remediation.

## Success Criteria

- Scan artifacts from the candidate-scan child are read and summarized.
- High-signal active deployment/start candidates are identified with file paths.
- Test-only/historical/generated candidates are separated.
- No source code changes are made; this is classification only.
