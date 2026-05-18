# VMuse remove deleted main imports

## Problem
After deleting `novaic_mcp_vmuse.main`, source `cli.py` and package comments still reference `.main`, so the console script can fail and the deleted FastMCP entry is still advertised.

## Success Criteria
- Source `cli.py` no longer imports `.main`, `mcp`, or `SKILLS_DIR` from deleted `main.py`.
- Source package comments no longer describe `main.py`/FastMCP as an available entry point.
- A focused scan finds no `.main import` references in source VMuse.
