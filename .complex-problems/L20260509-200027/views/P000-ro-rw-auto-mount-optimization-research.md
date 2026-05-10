# P000: RO/RW Auto Mount Optimization Research

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Current Cortex shell execution materializes `/cortex/ro` and `/cortex/rw` into a temporary filesystem for each shell command. This keeps the shell contract simple and disposable, but it can become slow as agent history, payloads, scope trees, and workspace files grow. The goal is to deeply research the current implementation and design better optimization options without prematurely changing code.

The research must respect the product principles already established:

- Agent identity is the primary boundary; same-agent subagents may share a team workspace.
- Shell should expose stable filesystem paths (`/cortex/ro`, `/cortex/rw`, `$RO`, `$RW`) rather than temp backing paths.
- Agent harness tools are being moved behind shell CLI surfaces where practical.
- AI-era engineering: code is cheap, confusing residue is expensive; prefer explicit contracts, small stable substrates, and clean boundaries.

## Success Criteria
- Audit current RO/RW materialization code paths and explain exactly where repeated work happens.
- Identify why automatic RO/RW mounting can become slow, with evidence from code.
- Compare credible optimization models for this system, including lazy RO, manifest/delta sync, persistent per-agent workspace cache, FUSE/virtual filesystem, CLI-native object reads, and hybrid designs.
- Recommend a staged architecture that preserves shell ergonomics while reducing per-command sync cost.
- Define correctness constraints: freshness, RW persistence, concurrent exec behavior, security/tenant boundaries, subagent sharing, and failure recovery.
- Produce implementable follow-up tickets or phases, but do not implement them in this research pass.

## Subproblems
- P001: Audit Current RO/RW Mount Path
- P002: Compare RO/RW Optimization Models
- P003: Recommend RO/RW Mount Optimization Plan

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R003: problems/P000/results/R003.md
- Check C003: problems/P000/checks/C003.md

## Follow-ups
- none
