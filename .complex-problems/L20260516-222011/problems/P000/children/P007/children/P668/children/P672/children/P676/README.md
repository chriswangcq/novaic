# Active deployment script stale-role remediation

## Problem

Using the classified active script set, inspect scripts for stale process names, misleading worker roles, unclear diagnostics, or old runtime assumptions. Apply low-risk fixes and verify script syntax/guards.

## Success Criteria

- Active scripts from discovery are inspected for stale role/process assumptions.
- Concrete low-risk stale or misleading script issues are fixed, or absence of fixable issues is evidenced.
- Relevant syntax/static guard checks are run for changed scripts.
- Residual risks outside local repository control are recorded.
