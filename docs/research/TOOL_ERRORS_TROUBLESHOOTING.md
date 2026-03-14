# 工具错误排查指南

## 受限/失败工具常见原因

### 1. 需要 MCP 客户端 (browser_get_tabs, browser_close_tab, browser_switch_tab, directory_snapshot)

**原因**: 这些工具依赖 VM 内的 novaic-mcp-vmuse 服务。当：
- VM 未启动
- VM 内未安装/未运行 novaic-mcp-vmuse
- vmcontrol 无法连接到 VM 的 VMUSE 端口

**排查**:
- 确认 Agent 已配置 VM 且 VM 已启动
- 检查 vmcontrol 日志: `{DATA_DIR}/logs/vmcontrol.log`
- VM 内需运行 novaic-mcp-vmuse（通常由 cloud-init 或 setup 自动部署）

**解决**: 启动 VM 并完成 VM 设置，确保 vmcontrol 能访问 `/api/vmuse/{agent_id}/browser/*` 和 `/api/vmuse/{agent_id}/context/*`

---

### 2. TRS 存储服务错误

**原因**: Tool Result Service (TRS) 不可用或存储失败。工具执行成功后需将结果推送到 TRS，若 TRS 报错则工具显示失败。

**排查**:
- 检查 Tool Result Service 是否运行: `{DATA_DIR}/logs/tool-result-service.log`
- 检查 `TOOL_RESULT_SERVICE_URL` 配置
- 检查 storage-b (novaic-storage-b) 的 tool_results.db 是否可写

**解决**: 确保 Tool Result Service 正常启动，DATA_DIR 有写权限

---

### 3. 应用未安装 (launch_app firefox)

**原因**: VM 内未安装 Firefox。launch_app 在 VM 内执行，依赖 VM 内已安装的应用。

**排查**:
- 在 VM 内执行 `which firefox` 或 `firefox --version`
- 不同发行版安装: `apt install firefox-esr` (Debian/Ubuntu) 或 `dnf install firefox` (Fedora)

**解决**: 在 VM 内安装所需应用，或改用已安装的应用名（如 `chromium`、`code`）

---

### 4. 执行失败 (subagent_cancel)

**原因**: subagent_cancel 调用 Gateway API 取消子任务。可能原因：
- 目标 subagent 不存在或已非 running 状态
- Gateway/RO 返回错误

**排查**:
- 检查 Gateway 日志
- 确认 target_subagent_id 有效且 status 为 running
- 子任务已完成/失败/已取消时，再次 cancel 会返回 "SubAgent is not running"

**解决**: 仅在子任务仍在运行时调用 cancel；若已结束则无需 cancel

---

## 添加 A2 Agent 到 Gateway DB

```bash
cd novaic-gateway
NOVAIC_DATA_DIR=~/Library/Application\ Support/com.novaic.app python scripts/add_agent_a2.py
```

或指定 data-dir:
```bash
python scripts/add_agent_a2.py --data-dir ~/Library/Application\ Support/com.novaic.app
```

可选参数:
- `--name A2`  Agent 显示名称（默认 A2）
- `--agent-id xxx`  使用已存在的 agent ID，仅补充 main subagent
