# 方案 4 分批开发任务清单

> 按依赖关系拆分，可派多名 subagent 分批执行。每批完成后可验证，再进入下一批。

---

## 批次总览

| 批次 | 任务 | 依赖 | 可并行 |
|------|------|------|--------|
| **Batch 1** | A. TOOL_NAME_TO_MOUNTED 映射 | 无 | 1 人 |
| **Batch 2** | B. Gateway builtin-tools API | A | 1 人 |
| **Batch 3** | C. Tools Server 改造 | B | 1 人 |
| **Batch 4** | D. 验证与测试 | A,B,C | 1 人 |

---

## Batch 1：TOOL_NAME_TO_MOUNTED 映射

**负责人**：Subagent 1  
**文件**：`novaic-gateway/gateway/agent_binding.py`  
**参考**：`docs/DESIGN-GATEWAY-RETURNS-FILTERED-TOOLS.md` 3.1 节

### 任务内容

1. 在 `agent_binding.py` 新增 `TOOL_NAME_TO_MOUNTED: Dict[str, tuple]`
2. 补齐所有需 mounted 检查的工具：
   - **VM**：screenshot, mouse, keyboard, file_pull, file_push, shell_exec, clipboard_get, clipboard_set（共 8 个）
   - **Mobile**：与 `PATH_TO_MOBILE_MOUNTED` 一一对应，从 `MOBILE_TOOL_MAPPING`（executor）反推 tool_name
3. 格式：`"tool_name": ("linux"|"android", category, op)`
4. 交叉核对：key 与 `novaic-shared-kernel/.../definitions.py` 中 `t["name"]` 一致

### 验收

- `TOOL_NAME_TO_MOUNTED` 覆盖所有 VM mounted 工具 + 所有 mobile 工具
- 无新增依赖，可独立提交

---

## Batch 2：Gateway builtin-tools API

**负责人**：Subagent 2  
**文件**：`novaic-gateway/gateway/api/internal/agent.py`  
**依赖**：Batch 1 完成

### 任务内容

1. 新增 `_filter_builtin_tools_for_agent(agent_id: str) -> List[Dict]`：
   - 拉平 `BUILTIN_TOOLS`
   - 从 `agent_drive` 取 `disabled_tools`
   - 从 `resolve_agent_runtime_context` 取 `device_type`, `mounted_tools`
   - 按设计文档 3.2 节逻辑过滤
2. 新增路由 `GET /internal/agents/{agent_id}/builtin-tools`：
   - 调用 `_filter_builtin_tools_for_agent`
   - 返回 `{"tools": [...], "total": N}`
   - 每个 tool 含 `name`, `description`, `inputSchema`
3. 确认 Gateway 的 `common.tools` 可访问 `BUILTIN_TOOLS`（含 vm + mobile）；若无则补充 `MOBILE_TOOLS` 导出

### 验收

- `curl` 或单元测试可调用新 API
- 无 binding 时 VM/mobile 工具被过滤
- 有 binding + mounted 时仅返回允许的工具

---

## Batch 3：Tools Server 改造

**负责人**：Subagent 3  
**文件**：`novaic-tools-server/tools_server/api.py`  
**依赖**：Batch 2 完成（Gateway 新 API 已部署或本地可测）

### 任务内容

1. 修改 `_get_tools_for_context`：
   - 当 `agent_id` 存在时，调用 `GET {GATEWAY_URL}/internal/agents/{agent_id}/builtin-tools`
   - 成功时：`builtin_tools = resp.json().get("tools", [])`
   - 失败时：fallback 到 `get_all_tools()` + 原有 tools-config 过滤
2. 保持 `external_tools` 合并逻辑不变
3. 保持返回结构 `{context_key, tools, total, builtin_count, external_count}` 不变

### 验收

- 有 agent 时，builtin 工具来自 Gateway 新 API
- 无 agent 或 API 失败时，行为与改造前一致
- 现有 `GET /internal/subagents/{aid}/{sid}/tools` 测试通过

---

## Batch 4：验证与测试

**负责人**：Subagent 4  
**依赖**：Batch 1、2、3 均完成

### 任务内容

1. **交叉验证**（按设计文档 4 节）：
   - 工具名与 definitions、PATH_TO_MOUNTED、PATH_TO_MOBILE_MOUNTED 一致
   - 列表过滤与 proxy 执行校验逻辑一致
2. **场景测试**：
   - 无 binding → VM/mobile 工具不出现在列表
   - Linux binding + 部分 mounted → 仅 mounted 的 VM 工具 + browser 等
   - Android binding + 部分 mounted → 仅 mounted 的 mobile 工具
   - disabled_tools → 被 disabled 的工具不出现在列表
3. **执行一致性**：列表中的工具调用时不应 403
4. 补充/更新单元测试（若需要）

### 验收

- 上述场景均通过
- 无回归

---

## 并行策略（可选）

若希望加速：

- **Batch 1** 与 **Batch 2 中 common.tools 检查** 可并行（不同人）
- **Batch 2** 的 `_filter_builtin_tools_for_agent` 与路由可同一人顺序完成
- **Batch 3** 必须在 Batch 2 可测后进行
- **Batch 4** 必须在 Batch 3 完成后进行

---

## 部署顺序

1. 部署 Gateway（Batch 1 + 2）
2. 部署 Tools Server（Batch 3）
3. 执行 Batch 4 验证
