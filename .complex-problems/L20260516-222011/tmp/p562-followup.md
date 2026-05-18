# P562 Child Scan Command Manifests

## Problem

P562 rolls up P566/P567/P568. P568 now has a reproducible command manifest, but P566 and P567 still only cite scan/slice output artifacts. Add command manifests for P566 and P567 so the parent P562 inventory has exact commands for all child scans.

## Success Criteria

- Adds a P566 manifest with exact commands and output paths for materialize/direct-file scan and slice artifacts.
- Adds a P567 manifest with exact commands and output paths for shell fallback/executor bypass scan and slice artifacts.
- Maps each command/artifact to the relevant child criteria and P562 parent criteria.
- Does not make production code changes; this is evidence documentation only.
