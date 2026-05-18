# App backend startup graph remediation

## Problem
Apply the concrete backend startup graph fixes identified by the audit without creating source/generated divergence.

## Success Criteria
- Startup script variants and generated copies are synchronized or clearly marked dev-only.
- Port naming conflict is removed or clarified in code/config.
- Script expectations match committed resources.
- `bash -n` and targeted config scans pass.
