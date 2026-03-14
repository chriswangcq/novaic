# 方案 4 详细技术设计：Gateway 返回完整过滤后的工具列表

> 目标：Tools Server 不再自行过滤，直接使用 Gateway 返回的、已按 disabled_tools + mounted_tools 过滤后的工具列表。

---

## 一、数据流与调用链路

### 1.1 当前数据流（改造前）

```
┌─────────────────────┐     GET /internal/subagents/{agent_id}/{subagent_id}/tools
│  Agent Runtime      │ ──────────────────────────────────────────────────────────►
│  (task_queue/client)│                                                              │
└─────────────────────┘                                                              │
                                                                                     ▼
┌─────────────────────┐     get_all_tools()     ┌──────────────────────────────────┐
│  Tools Server       │ ◄── BUILTIN_TOOLS       │  common.tools.definitions        │
│  api._get_tools_    │                         │  (novaic-shared-kernel)           │
│  for_context        │                         └──────────────────────────────────┘
│                     │
│                     │     GET /api/agents/{id}/tools-config
│                     │ ──────────────────────────────────────►  Gateway skills.py
│                     │     Response: { disabled_tools }       (agent_drive)
│                     │
│                     │     Filter: builtin_tools - disabled_tools
│                     │     Merge: builtin + external_tools
│                     ▼
│  Response: { tools, total, ... }
└─────────────────────┘
```

**问题**：Tools Server 只拿到 `disabled_tools`，拿不到 `mounted_tools`，无法过滤 VM/mobile 工具。

---

### 1.2 改造后数据流

```
┌─────────────────────┐     GET /internal/subagents/{agent_id}/{subagent_id}/tools
│  Agent Runtime      │ ──────────────────────────────────────────────────────────►
└─────────────────────┘                                                              │
                                                                                     ▼
┌─────────────────────┐     GET /internal/agents/{agent_id}/builtin-tools           │
│  Tools Server       │ ──────────────────────────────────────►  Gateway            │
│  api._get_tools_    │     (新 API)                              internal/agent    │
│  for_context        │                                                              │
│                     │     Response: { tools: [{name, description, inputSchema}] }  │
│                     │              (已按 disabled + mounted 过滤)                   │
│                     │ ◄──────────────────────────────────────                     │
│                     │                                                              │
│                     │     external_tools = manager.get_external_tools(context_key) │
│                     │     Merge: builtin (from Gateway) + external_tools           │
│                     ▼                                                              │
│  Response: { tools, total, ... }                                                    │
└─────────────────────┘                                                              │
                                                                                     │
                                                                                     ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Gateway: GET /internal/agents/{agent_id}/builtin-tools                            │
│  1. BUILTIN_TOOLS (common.tools)                                                   │
│  2. agent_drive.disabled_tools                                                     │
│  3. resolve_agent_runtime_context(agent_id) → binding, device, mounted_tools      │
│  4. Filter: disabled + mounted (VM/mobile 按 binding 过滤)                          │
│  5. Return filtered tools                                                          │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.3 调用链路（时序）

```
Agent Runtime                    Tools Server                      Gateway
     │                                │                                 │
     │  GET /subagents/{aid}/{sid}/tools                               │
     │ ─────────────────────────────► │                                 │
     │                                │  GET /internal/agents/{aid}/builtin-tools
     │                                │ ─────────────────────────────► │
     │                                │                                 │  resolve_agent_runtime_context
     │                                │                                 │  get disabled_tools (drive)
     │                                │                                 │  filter by disabled + mounted
     │                                │  { tools: [...] }                │
     │                                │ ◄───────────────────────────────│
     │                                │  get_external_tools(context_key)│
     │                                │  merge builtin + external       │
     │  { tools, total, ... }         │                                 │
     │ ◄─────────────────────────────│                                 │
```

---

## 二、改动点清单

| 模块 | 文件 | 改动类型 | 说明 |
|------|------|----------|------|
| **Gateway** | `gateway/api/internal/agent.py` | 新增 | 新增 `GET /internal/agents/{agent_id}/builtin-tools` |
| **Gateway** | `gateway/agent_binding.py` | 新增 | 新增 `TOOL_NAME_TO_MOUNTED` 映射（tool_name → 过滤规则） |
| **Gateway** | `gateway/api/internal/agent.py` | 新增 | 过滤逻辑：`_filter_builtin_tools_for_agent()` |
| **Tools Server** | `tools_server/api.py` | 修改 | `_get_tools_for_context` 改为调用新 API，不再调用 tools-config |
| **Gateway** | `common/tools/__init__.py` | 修改 | 导出 `MOBILE_TOOLS`（若 Gateway 当前未导入） |

---

## 三、改动逻辑详解

### 3.1 Gateway：tool_name → 过滤规则映射

需要在 Gateway 中建立 **tool_name → (device_type, category, op)** 的映射，用于判断某工具是否受 mounted 控制：

| 类型 | 示例 | 规则 |
|------|------|------|
| 非设备工具 | memory_save, chat_reply, subagent_list | 仅检查 disabled_tools |
| VM 工具（需 mounted 检查） | screenshot, mouse, keyboard, file_pull, shell_exec, clipboard_* | 需 Linux binding + mounted[cat] ∋ op |
| VM 工具（不检查 mounted） | browser_*, list_windows, system_snapshot | 需 Linux binding 即可 |
| Mobile 工具 | mobile_screenshot, mobile_file_pull | 需 Android binding + mounted[cat] ∋ op |

**实现**：在 `agent_binding.py` 新增 `TOOL_NAME_TO_MOUNTED`，key 必须与 `definitions.py` 中 `t["name"]` 完全一致：

```python
# tool_name -> (device_type, category, op)
# device_type: "linux" | "android"
# 若 rule 不存在，表示非设备工具，仅 disabled 过滤
TOOL_NAME_TO_MOUNTED: Dict[str, tuple] = {
    # VM - desktop (definitions: screenshot, mouse, keyboard)
    "screenshot": ("linux", "desktop", "screenshot"),
    "mouse": ("linux", "desktop", "mouse"),
    "keyboard": ("linux", "desktop", "keyboard"),
    # VM - file (definitions: file_pull, file_push)
    "file_pull": ("linux", "file", "pull"),
    "file_push": ("linux", "file", "push"),
    # VM - shell (definitions: shell_exec)
    "shell_exec": ("linux", "shell", "run_command"),
    # VM - clipboard
    "clipboard_get": ("linux", "clipboard", "clipboard_get"),
    "clipboard_set": ("linux", "clipboard", "clipboard_set"),
    # Mobile - 全部需 mounted 检查，与 MOBILE_TOOL_MAPPING + PATH_TO_MOBILE_MOUNTED 对应
    "mobile_screenshot": ("android", "screen", "screenshot"),
    "mobile_touch": ("android", "screen", "touch"),
    "mobile_input": ("android", "screen", "input"),
    "mobile_shell": ("android", "shell", "shell"),
    "mobile_file_push": ("android", "file", "push"),
    "mobile_file_pull": ("android", "file", "pull"),
    # ... 其余 mobile 工具按 PATH_TO_MOBILE_MOUNTED 补齐
}
```

**VM 工具不在此映射中**（如 browser_*, list_windows, system_snapshot）：有 Linux binding 即允许，不检查 mounted。

---

### 3.2 Gateway：过滤逻辑伪代码

```python
def _filter_builtin_tools_for_agent(agent_id: str) -> List[Dict]:
    all_tools = flatten(BUILTIN_TOOLS)  # 所有工具
    disabled = get_disabled_tools(agent_id)  # agent_drive
    resolved = resolve_agent_runtime_context(db, agent_id)
    device_type = resolved["device"]["type"] if resolved else None
    mounted = normalize_mounted_tools(resolved["mounted_tools"]) if resolved else {}

    result = []
    for t in all_tools:
        name = t["name"]
        if name in disabled:
            continue
        rule = TOOL_NAME_TO_MOUNTED.get(name)
        if rule is None:
            # 非 VM/mobile 工具，仅 disabled 过滤
            result.append(t)
            continue
        dev_type, cat, op = rule
        if dev_type == "linux":
            if device_type != "linux":
                continue  # 无 Linux binding，排除
            if op is None:
                result.append(t)  # 不检查 mounted
            elif op in mounted.get(cat, []):
                result.append(t)
        elif dev_type == "android":
            if device_type != "android":
                continue
            if op in mounted.get(cat, []):
                result.append(t)
    return result
```

---

### 3.3 Tools Server：_get_tools_for_context 改造

**原逻辑**：
```python
builtin_tools = get_all_tools()
resp = client.get(f"{gateway_url}/api/agents/{agent_id}/tools-config")
disabled = set(resp.json().get("disabled_tools", []))
builtin_tools = [t for t in builtin_tools if t["name"] not in disabled]
```

**新逻辑**：
```python
if agent_id and gateway_url:
    resp = await client.get(f"{gateway_url}/internal/agents/{agent_id}/builtin-tools")
    if resp.status_code == 200:
        raw = resp.json().get("tools")
        builtin_tools = raw if isinstance(raw, list) else []
    else:
        # Fallback: internal tools-config (no auth) + disabled filter
        config_resp = await client.get(f"{gateway_url}/internal/agents/{agent_id}/tools-config")
        if config_resp.status_code == 200:
            config = config_resp.json()
            disabled = set(config.get("disabled_tools") or [])
            builtin_tools = [t for t in builtin_tools if t["name"] not in disabled]
    # 若 builtin-tools 与 tools-config 均失败，保留 unfiltered get_all_tools()
else:
    builtin_tools = get_all_tools()
```

---

## 四、交叉验证

### 4.1 工具名一致性

| 来源 | 位置 | 用途 |
|------|------|------|
| definitions.py | BUILTIN_TOOLS["vm"], ["mobile"] | 工具定义，含 name |
| executor VM_TOOL_MAPPING | key | 路由到 VMUSE path |
| executor MOBILE_TOOL_MAPPING | key | 路由到 mobile path |
| agent_binding PATH_TO_MOUNTED | (family, op) | VM 路径 → category |
| agent_binding PATH_TO_MOBILE_MOUNTED | path | Mobile 路径 → category |
| **新增** TOOL_NAME_TO_MOUNTED | key | 过滤时 tool_name → (device_type, cat, op) |

**验证**：
- `TOOL_NAME_TO_MOUNTED` 的 key 必须与 definitions 中 `t["name"]` 一致
- VM 工具：`TOOL_NAME_TO_MOUNTED[name]` 的 (cat, op) 必须存在于 `PATH_TO_MOUNTED` 的 value
- Mobile 工具：`MOBILE_TOOL_MAPPING[name]` = (endpoint, _) → `PATH_TO_MOBILE_MOUNTED[endpoint]` = (cat, op) → `TOOL_NAME_TO_MOUNTED[name]` = ("android", cat, op)

### 4.2 执行时与列表时一致性

| 阶段 | 校验点 | 逻辑 |
|------|--------|------|
| 列表（新） | Gateway builtin-tools API | disabled + mounted 过滤 |
| 执行 | proxy_vm_tool | is_tool_mounted(mounted, path_family, path_op) |
| 执行 | proxy_mobile_tool | is_mobile_tool_mounted(mounted, path) |

**验证**：列表过滤与执行校验必须同源（都依赖 binding.mounted_tools），且映射一致。若列表允许某工具，执行时不应 403。

### 4.3 Internal API 鉴权

`GET /internal/agents/{agent_id}/builtin-tools` 为 internal 接口，仅服务间调用。需确认：
- 路由挂在 `internal_proxy_router` 下
- 无 user_id 校验（internal 由 nginx 或服务间信任）
- 与现有 `/internal/agents/*` 风格一致

### 4.4 Subagent 继承

当前 tools 请求为 `agent_id:subagent_id`，过滤仅用 `agent_id`。Subagent 与 Main Agent 共用同一 binding，因此：
- binding 以 agent 维度存在
- 所有 subagent 使用同一 agent 的 binding
- 无需按 subagent_id 区分

---

## 五、依赖与部署

| 依赖 | 说明 |
|------|------|
| Gateway 依赖 common.tools | 已有（skills.py 已用 BUILTIN_TOOLS） |
| Gateway 需 MOBILE_TOOLS | 若 common.tools 未导出，需在 definitions 中补充并导出 |
| Tools Server → Gateway | 使用 internal_async_client，调用 builtin-tools 与 tools-config（fallback） |
| 部署顺序 | 先部署 Gateway（新 API 向后兼容），再部署 Tools Server |

---

## 六、回滚策略

若新 API 异常，Tools Server 可 fallback：
```python
if resp.status_code != 200:
    # 先尝试 internal tools-config 做 disabled 过滤（无需 user auth）
    config_resp = await client.get(f"{gateway_url}/internal/agents/{agent_id}/tools-config")
    if config_resp.status_code == 200:
        disabled = set(config.get("disabled_tools") or [])
        builtin_tools = [t for t in get_all_tools() if t["name"] not in disabled]
    else:
        # tools-config 也失败时，使用 unfiltered get_all_tools()
        builtin_tools = get_all_tools()
```

**说明**：`builtin-tools` 不校验 agent 是否存在，对任意 `agent_id` 均返回 200（无 drive 时返回 filtered 结果）。执行时由 Gateway proxy 做 mounted 校验。

---

## 七、测试要点

1. **无 binding**：VM/mobile 工具不出现在列表中
2. **有 Linux binding，mounted 部分**：仅 mounted 的 VM 工具出现
3. **有 Android binding，mounted 部分**：仅 mounted 的 mobile 工具出现
4. **disabled_tools**：被 disabled 的工具不出现在列表
5. **执行一致性**：列表中的工具执行时不应 403
6. **列表外的工具**：若 LLM 因缓存等原因调用，执行时应 403（Gateway 校验保持不变）
