# Round 001 Repo Boundaries (Platform)

## Target repos and ownership

| target_repo | owner_team | source_path_mapping | notes |
|---|---|---|---|
| `novaic-app` | `Desktop Team` | `novaic-app/**` | Desktop/UI runtime only. |
| `novaic-backend` | `Runtime Team` | `novaic-backend/**` | Runtime orchestration and backend services. |
| `novaic-gateway` | `API Team` | `novaic-gateway/**` | API gateway and external API surface. |
| `novaic-mcp-vmuse` | `Tools Team` | `novaic-mcp-vmuse/**` | Tool runner and MCP integration. |
| `novaic-shared-kernel` | `Storage-A/B Team` | `novaic-shared-kernel/**`, `contracts/**`, `compatibility.yaml` | Shared contracts and compatibility baseline. |
| `novaic-control-plane` | `Platform Team` | `novaic-control-plane/**` | Round governance, dispatch, evidence model. |

## Boundary rules

1. Each repo owns only its mapped source paths and internal CI policy.
2. Cross-repo interaction must happen through versioned contracts from `novaic-shared-kernel`.
3. Service repos must not import files directly from sibling repos by relative path.
4. Any contract change requires a consumer impact note in the team report.

## Compatibility guardrails

- Shared compatibility baseline is tracked in `compatibility.yaml`.
- Contract artifacts that affect multiple repos are anchored under `contracts/**`.
- Split execution evidence must be replayable using non-author commands.
