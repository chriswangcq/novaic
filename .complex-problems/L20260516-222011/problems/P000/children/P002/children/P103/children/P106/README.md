# Devicectl CLI Coverage and Artifact Contract Audit

## Problem

`devicectl` is the shell-first device interface. Media-producing commands such as HD screenshots must return terminal text plus blob artifact manifests rather than inline base64, while non-media commands should remain concise terminal receipts.

## Success Criteria

- Locate `devicectl` implementation, command registration, and tests.
- Verify HD screenshot and related device commands are reachable through shell schema/help.
- Verify screenshot/file-producing commands follow the blob artifact contract and do not emit base64 in normal stdout.
- Run focused device CLI/unit tests or safe local help checks.
- Fix bounded gaps found.
