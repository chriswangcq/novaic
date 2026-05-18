# Agentctl CLI Coverage Audit

## Problem

`agentctl` is the shell-first interface for IM, subagent, and agent/runtime-facing actions that used to be direct harness tools. It must be registered, discoverable, and covered by tests so agents can perform these actions through shell without hidden direct-tool assumptions.

## Success Criteria

- Locate `agentctl` implementation and command registration/help surfaces.
- Verify intended IM/subagent/media/payload-adjacent commands are reachable through shell docs or schema.
- Run focused tests or cheap local help checks for `agentctl` command availability.
- Fix misleading or missing coverage if found, or record a precise blocker/follow-up.
