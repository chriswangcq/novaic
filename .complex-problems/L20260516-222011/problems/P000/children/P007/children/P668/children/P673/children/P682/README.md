# Entrypoint discovery scan artifacts

## Problem

Locate backend worker/service entrypoint files and launch commands from repository source, scripts, package metadata, app resources, and deployment/config files. Produce reproducible scan artifacts so later classification is evidence-based and not memory-based.

## Success Criteria

- Repository scans capture candidate Python modules, shell scripts, package scripts, app resources, service configs, and deploy/worker launch commands.
- Candidate artifacts are saved under `.complex-problems/L20260516-222011/tmp/` with the commands used.
- High-noise outputs are summarized with stable pointers instead of pasted wholesale.
- No production code is changed in this discovery-only child.
