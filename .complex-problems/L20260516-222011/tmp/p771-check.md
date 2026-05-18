# App backend script and launch wiring discovery check

## Summary

Success. The script/launch discovery met its scoped criteria and found concrete stale launch wiring candidates. The one-go result is accepted because it was read-only, bounded, cited exact files/lines, and did not blur discovery with remediation.

## Evidence

- `R752` cites scan artifact `.complex-problems/L20260516-222011/tmp/p771-backend-script-scan.txt`.
- `R752` identifies `sync-vmuse-resource.sh` as source-to-app copy synchronization rather than runtime FastMCP startup.
- `R752` identifies stale/incomplete backend graph wording in local and packaged `start-backends.sh`.
- `R752` identifies a concrete `PORT_CORTEX=19996` / `vmcontrol` port conflict candidate.
- `R752` confirms no scripts or launch files were modified in this discovery child.

## Criteria Map

- Relevant script and launch helper files discovered: satisfied by the candidate file list and inspected scripts.
- High-signal startup/contract references classified: satisfied by classifications for VMUSE sync, backend subset startup, worker `--cortex-url`, Blob/Gateway/Queue startup, and packaged script startup.
- Remediation candidates listed or absence recorded: satisfied by three explicit candidate groups in `R752`.
- No scripts/launch files modified: satisfied by `R752`; only ledger artifacts were written.

## Execution Map

- The ticket ran bounded searches over `novaic-app/scripts`, `novaic-app/package.json`, and `novaic-app/src-tauri`.
- It inspected targeted slices of package scripts, local backend startup, VMUSE sync, DMG build, app service config, and packaged backend startup scripts.
- It recorded result `R752` without implementation work.

## Stress Test

- Plausible failure mode: script hits for `main.py` could imply active stale FastMCP runtime. `R752` checks that `main.py` appears in a source-tree presence test for copy synchronization, not service startup.
- Plausible failure mode: backend workers could be started against a wrong service endpoint. `R752` finds exactly that risk: `--cortex-url` is pointed at port `19996`, while app resource config assigns `19996` to `vmcontrol`.
- Plausible failure mode: packaged scripts could diverge from source scripts. `R752` checks both resource and generated packaged scripts and finds they share the same incomplete subset message.

## Residual Risk

- This child did not implement fixes. The stale backend graph/port contract candidates must be closed in the remediation phase.
- It did not inspect frontend monitor behavior; that is covered by a separate child.

## Result IDs

- R752
