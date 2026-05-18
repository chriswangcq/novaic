# PR-225  Residual App/Common/Docs Tail Cleanup

| 字段 | 值 |
| --- | --- |
| **Phase** | maintenance entropy cleanup |
| **Milestone** | clean current main path |
| **承诺** | Remove misleading old branches instead of preserving compatibility residue |
| **Status** | `[closed]` |
| **Depends on** | PR-224 |
| **Blocks** | — |
| **估时** | 0.25-0.5 d |
| **Owner** | wangchaoqun |

## 大工单

### 1. App resource hygiene

- 目标：App 打包输入目录不能携带本地 Python 生成物，也不能漂移出 `novaic-mcp-vmuse` 子仓库当前内容。
- 小工单：
  - 清理 `resources/novaic-mcp-vmuse` 与 `gen/apple/assets/novaic-mcp-vmuse` 下的 `__pycache__`、`.pyc`、`*.egg-info`。
  - 新增统一同步脚本，构建时从 `novaic-mcp-vmuse` 子仓库干净复制资源。
  - 增加 root CI guard，校验两个 App resource bundle 与子仓库内容一致，且不含生成物。
- 验收：`pytest -q scripts/ci/test_app_resource_hygiene.py`。

### 2. Active compatibility tail cleanup

- 目标：活代码不再保留“为了兼容旧路径”的分支或命名。
- 小工单：
  - 删除 `common.log_context.caller_var` 单字段镜像，统一使用 dict-valued `current()/scope()`。
  - 删除 DMG 构建脚本的过时参数处理。
  - 删除 `task_workers` 旧配置常量和 `use_legacy_vmuse` 配置开关。
  - 删除 VMControl `/api/vms` POST register legacy API。
  - 删除 VMControl `ssh_exec` Gateway 查询端口路径，调用方必须显式传 `ssh_port`。
- 验收：相关 grep guard 为空；`novaic-common` 单测通过；App Rust check 通过。

### 3. Historical docs noise cleanup

- 目标：历史票可以保留考古价值，但不能被 grep 或脚本误读为当前未闭合工作。
- 小工单：
  - PR-45 内部状态从 historical in-progress marker 改为 archived。
  - PR-18/19/24/42/44/45/49/51/53 历史票增加 archive banner，并将未完成 checkbox 改成非 checkbox 的 archived marker。
  - `tickets/README.md` 中 PR-88、PR-44 事故映射行、PR-01 review 行改成不会被工单扫描误判的 shape。
  - `HANDOVER.md` 从旧事故流水账改成当前后端架构交接摘要。
- 验收：目标历史票不再出现 unchecked / tilde 状态 marker；README 的非工单历史行不再以 `| PR-` 伪装成未闭合票。

## 结果 Review

- App resource bundle 现在由单脚本生成，避免 build path 与手工资源路径分叉。
- `caller_var`、obsolete flags、legacy VMUse switch、VM register API、Gateway SSH port lookup 均从活代码移除。
- 历史文档仍可追溯，但顶部明确为 archive，且 checklist 不再污染“未完成工单”扫描。

## 验证

- `pytest -q scripts/ci/test_app_resource_hygiene.py`
- `rg` active residue checks
- `novaic-common` targeted tests
- `novaic-app` targeted Rust check
