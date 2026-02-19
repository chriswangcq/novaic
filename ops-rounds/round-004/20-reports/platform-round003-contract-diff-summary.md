# Platform Contract Diff Summary (Round 003 -> Round 004)

## Scope
- baseline carried from Round 003:
  - `contracts/openapi/gateway-public.v1.yaml`
  - `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
  - `contracts/schema/task-message.v1.schema.json`
  - `contracts/schema/subagent-status.v1.schema.json`
- Round 004 additions for Gate B closure:
  - `contracts/openapi/storage-contracts.v1.yaml`
  - `contracts/schema/storage-artifact.v1.schema.json`

## Executable Evidence
- command:
  - `rg "storage|file-service|tool-result" contracts -g "*.yaml" -g "*.json"`
- result summary:
  - `contracts/openapi/storage-contracts.v1.yaml` 命中 storage artifact 路由与 schema 引用
  - `contracts/schema/storage-artifact.v1.schema.json` 命中 `file-service|tool-result` 类型枚举

- command:
  - `python3 - <<'PY' ... read storage-api.v1.schema.json and storage-artifact.v1.schema.json required ... PY`
- result summary:
  - `storage-api.v1.schema.json required = ['file_service', 'tool_result_service']`
  - `storage-artifact.v1.schema.json required = ['artifact_id', 'artifact_kind', 'file_url', 'checksum_sha256', 'size_bytes', 'created_at']`

## Field-Level Diff (Practical)
- storage baseline contract (service-level):
  - top-level groups: `file_service`, `tool_result_service`
- executable storage artifact contract (record-level):
  - canonical required fields:
    - `artifact_id`
    - `artifact_kind` (`file-service` | `tool-result`)
    - `file_url`
    - `checksum_sha256`
    - `size_bytes`
    - `created_at`

## Outcome
- Round 004 已从“仅服务分组约束”推进到“可执行记录级字段约束”。
- 后续由 Storage-A/B 与 API 将该 contract 对应到实际接口返回，并提供 CI/contract test 证据闭环。
