# Sandbox Wire Base64 and Mount Residue Classification

## Problem

Classify sandbox stdout/stderr base64 encoding and mount/path terms to ensure base64 is wire/protocol-only and not public LLM history, and mount paths do not expose uncontrolled host paths.

## Success Criteria

- Records exact scans for base64, stdout, stderr, mount, host path, ro/rw, logicalfs, and blob terms.
- Classifies wire encoding and mount/path hits.
- Runs focused tests or cites service/SDK tests proving behavior.
- Creates follow-up if risky mount or public base64 residue remains.
