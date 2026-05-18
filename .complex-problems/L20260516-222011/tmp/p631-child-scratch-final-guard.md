# RW Scratch Final Guard

## Problem

The cleanup needs a final skeptical pass to ensure root `/rw/scratch` is no longer advertised as the preferred/default scratch contract while legitimate arbitrary RW paths and lower-layer tests remain intentional.

## Success Criteria

- Post-change scans classify all remaining `/rw/scratch` hits.
- Focused tests pass.
- Any remaining root `/rw/scratch` hit is explicitly justified or converted into a follow-up.
