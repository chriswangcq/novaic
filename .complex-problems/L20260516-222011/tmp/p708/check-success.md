# Device/devicectl and artifact-display boundary classification check

## Summary

Status: success.

The cited result `R735` and closed children satisfy `P708/T713`. The work did not stop at a one-go claim: it split discovery, remediation, and verification into separate child problems, patched the stale active surfaces found by the audit, and ran focused contract tests plus route/resource checks.

## Evidence

- `P721/R707/C751`: inventoried Device/devicectl entrypoints and launch/control surfaces.
- `P722/R725/C770`: mapped shell output, Blob/artifact manifests, display projection, LLM request construction, and Cortex/Runtime history.
- `P723/R731/C776`: remediated active issues by updating the VMuse protocol doc, removing the unused VMuse `windows.py` base64 import, syncing bundled resources, and removing the stale Device Service screenshot route.
- `P724/R734/C779`: verified the final contract with scans and focused tests.
- Additional verification recorded in `R735`: shell/Cortex projection tests `62 passed`; runtime display/history/factory tests `17 passed`; Device focused tests `6 passed`; app resource hygiene tests `2 passed`; route check confirmed `/api/vmcontrol/vms/{vm_id}/screenshot` is absent.
- Final spot scan before this check did not show the removed route or `windows.py` base64 import in the active target files; remaining hits were ledger evidence, tests, auth/cursor encoders, provider/client protocol code, or lower-level VMuse/VmControl media transports.

## Criteria Map

- Device/devicectl entrypoints and launch references inventoried: satisfied by `P721`.
- Boundaries explicit: satisfied by `P722` and the updated documentation in `P742`; current boundary is Device captures/controls hardware, devicectl is shell-facing CLI, Blob stores bytes, shell returns terminal text/manifests, display projects current-round media to the model, and Cortex/Runtime history stores references/manifests.
- Active stale docs/code claims or small contract violations patched: satisfied by `P723`, `P742`, `P743`, and `P744/P746`.
- Large screenshot/artifact output behavior verified as Blob/manifest-only where relevant: satisfied by `P724/P748` focused tests and scans.
- Residual hits classified and follow-ups identified if needed: satisfied by `P747`; residual lower-level media protocols are intentional byte-producing layers, not direct LLM-history exposure paths.

## Execution Map

- The problem was not solved as a single broad pass. It was decomposed into device discovery, artifact/display discovery, remediation, and verification, with further sub-splits for doc cleanup, VMuse cleanup, Device route analysis, route removal, scan verification, and test verification.
- Implementation touched only scoped files: VMuse doc, VMuse windows source and synced resource copies, and Device Service route definition.
- Verification covered both static classification and runtime-relevant unit/contract tests.

## Stress Test

- Checked for the common failure mode where code is written but the old route remains active: the Device router no longer registers the stale `/api/vmcontrol/vms/{vm_id}/screenshot` path.
- Checked for generated resource drift: `sync-vmuse-resource.sh` was run and resource hygiene tests passed.
- Checked for base64 leakage regression at the contract level: shell/Cortex projection, runtime display/history, and factory multimodal tests passed.
- Checked the audit did not over-delete low-level transports: VmControl/VMuse byte-producing protocol layers remain, which is correct because they sit below shell/display projection.

## Residual Risk

No P708-specific blocking residue remains. The main residual risk is operational: true end-to-end screenshot/display behavior still depends on deployed services and live host-device availability, which is outside this local contract audit. Lower-level media protocol code still contains base64 by design, so future regressions should be guarded by the existing shell/display/history tests rather than by a naive global `base64` ban.
