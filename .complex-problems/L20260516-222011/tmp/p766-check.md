# App resource copy residue discovery check

## Summary

Success. Result R747 solves P766 because it discovered relevant app resource/generated copies, classified copied VMuse FastMCP direct media residue versus unrelated third-party bundled resource vocabulary, and listed exact copied cleanup targets without modifying product code.

## Evidence

- R747 records the scan artifact `.complex-problems/L20260516-222011/tmp/p766-app-resource-scan.txt`.
- R747 lists the two relevant app copy roots under `resources` and `gen/apple/assets`.
- R747 records source/copy SHA-256 comparisons for `main.py`, `cli.py`, and `http_server.py`.
- R747 lists exact app-copy remediation files.

## Criteria Map

- Criterion: Relevant app resource/generated copies are discovered and scanned with bounded commands.
  Evidence: R747 Done items 1-2 and scan artifact.
- Criterion: Suspicious hits are classified as generated mirror, stale copied residue, or unrelated app resource vocabulary.
  Evidence: R747 Verification classifies VMuse FastMCP copies as stale copied residue and Android/QEMU hits as unrelated third-party vocabulary.
- Criterion: Exact remediation candidates are listed, or absence is explicitly recorded.
  Evidence: R747 Known Gaps lists source-mirrored copied files in both app resource trees.
- Criterion: No product code is modified in this discovery child.
  Evidence: R747 Known Gaps states no product code was modified.

## Execution Map

- Ticket T757 was classified one_go because this was a bounded copied-resource discovery task.
- Execution scanned copied resources, filtered noisy third-party hits, and compared source/copy hashes.
- Result R747 recorded exact cleanup targets.

## Stress Test

- Plausible failure mode: broad scans over app resources could drown in Android/QEMU third-party hits and hide NovaIC copied residue.
- Check result: R747 identifies the relevant VMuse copy roots separately and classifies Android/QEMU hits as unrelated.
- Plausible failure mode: source cleanup could later leave bundled copies stale.
- Check result: R747 explicitly lists both app copy trees that must be synchronized during remediation.

## Residual Risk

- Medium but non-blocking for P766. Discovery is complete, but remediation must ensure source VMuse and copied app resources are cleaned together.

## Result IDs

- R747
