# Deployment script candidate scan artifacts

## Problem

Generate reproducible candidate lists for deployment/start/supervision/smoke/health scripts and configs without interpreting or changing them. The next classifier needs stable evidence files rather than ad hoc terminal memory.

## Success Criteria

- Candidate file list artifact is saved under the ledger tmp directory.
- Keyword scan artifact is saved under the ledger tmp directory.
- Obvious generated/cache/ledger directories are excluded from scans.
- No source code changes are made.
