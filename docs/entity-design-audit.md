# Entity Design Audit — 复用、解耦、联动

> 基于 `gateway/entity/defs.py` 全量实体，按"三职合一"问题、关系缺失、复用机会三个维度审计。
> 优先级：P0 阻塞业务 / P1 架构债 / P2 长期优化

---

## 一、全局实体关系现状

```
users (1)
  ├─ user-preferences (1:1)
  ├─ refresh-tokens (1:N)
  ├─ agents (1:N)
  │    ├─ agent-binding (1:1) → devices
  │    ├─ agent-tools (1:1)          ← 职责过宽，见§3
  │    ├─ agent-state (1:1)
  │    ├─ agent-skills (N:M) → skills
  │    ├─ agent-notebook (1:N)
  │    ├─ agent-memory (1:N, namespaced)
  │    ├─ agent-task-history (1:N)
  │    ├─ agent-tasks (1:N)
  │    ├─ subagents (1:N)
  │    ├─ messages (stream)
  │    └─ execution-logs (stream)
  │         └─ log-payloads (1:1)
  ├─ devices (1:N)
  │    └─ vm-users (1:N)
  ├─ skills (1:N)
  └─ api-keys (1:N)
       └─ models/candidate_models (1:N)  ← 三职合一，待拆分
```

---

## 二、问题分类矩阵

| 实体 | 问题类型 | 优先级 | 说明 |
|------|------|------|------|
| `candidate_models` | 三职合一 | P1 | 元数据+关联+启用状态混合，已有方案（model-entity-refactor.md） |
| `agent-tools` | 职责过宽 | P1 | Personality/Profile/Drive/BootstrapMD/Tools 五个领域挤一张表 |
| `agents` | 隐式关联 | P1 | `model_id` 直接存 UUID，没有关联 `candidate_models` 的 FK 约束 |
| `user-preferences` | 隐式关联 | P1 | `default_model` / `audio_model` 存 UUID string，无 FK，删模型不级联 |
| `agent-skills` | 缺 FK 约束 | P2 | `skill_id` 有 index 但无 `REFERENCES skills(id) ON DELETE CASCADE` |
| `vm-users` | 密码明文 | P0 | `password` 字段明文存储，无 `hidden=True` 保护 |
| `devices` | 类型膨胀 | P2 | linux/android/host_desktop 三种设备类型字段挤一张表 |
| `subagents` | 状态机外泄 | P2 | `status`/`wake_at`/`timeout_at` 状态机字段散落主表 |
| `agent-notebook` / `agent-task-history` / `agent-tasks` | 重叠 | P2 | 三个实体都在记录"Agent 做了什么"，语义有重叠 |
| `execution-logs` + `log-payloads` | 正确拆分 | ✅ | 1:1 分离大 payload，设计合理 |
| `messages` | 职责扩展 | P2 | `claimed_by`/`processed` 是 Queue 字段，混在消息实体里 |

---

## 三、逐实体问题详述

### 3.1 `agent-tools`（P1 — 职责过宽）

**现状**：一张表承载了 5 个独立领域：

| 领域 | 字段 |
|------|------|
| Personality | `personality`, `communication_style` |
| User Profile | `user_profile`, `user_active_hours` |
| Drive/状态机参数 | `proactiveness`, `min/max_rest_minutes`, `relationship_level`, `interaction_count` |
| Bootstrap MD | `soul_md`, `heartbeat_md`, `memory_md`, `user_md`, `behavior_guide_md` … |
| Tools Config | `enabled_tool_categories`, `disabled_tools`, `custom_instructions` |

**问题**：  
- 前端每次 `agent-tools` 订阅同步整张 1KB+ 的记录  
- `_bootstrap_get/save_action` 在 `agent-tools` 里 pick 字段，是变相的"虚拟子表"  
- `growth_log`/`drive_config` 是 JSON blob，无法单独订阅

**重构方案**：
```
agent-persona (form, 1:1 agent)
  personality, communication_style, custom_instructions

agent-profile (form, 1:1 agent)
  user_profile, user_active_hours, relationship_level, interaction_count
  no_response_streak, last_proactive_at

agent-drive (form, 1:1 agent)
  proactiveness, min_rest_minutes, max_rest_minutes
  growth_log, drive_config

agent-bootstrap (form, 1:1 agent)
  soul_md, heartbeat_md, memory_md, user_md
  behavior_guide_md, capability_list_md, sub_subagent_guide_md
  active_hours_start, active_hours_end, active_hours_timezone

agent-tools-config (form, 1:1 agent)
  enabled_tool_categories, disabled_tools
```

---

### 3.2 `agents.model_id`（P1 — 隐式关联无 FK）

**现状**：
```python
F.text("model_id"),   # 存的是 candidate_models.model_id (string "gpt-4o")
                      # 不是 candidate_models.id (UUID)
```

**问题**：  
- `model_id` 是 provider model string（如 `"gpt-4o"`），不是 `candidate_models.id`  
- 删模型时 `agents.model_id` 不级联，成孤悬引用  
- `build_llm_config_for_agent_via_factory` 用这个字段但逻辑散在 `factory_client.py`

**重构方向**（依赖 model-entity-refactor 完成后）：
```
agents.selected_model_id → available-models.id  (FK, ON DELETE SET NULL)
```

---

### 3.3 `user-preferences.default_model / audio_model`（P1 — 无 FK）

**现状**：
```python
F.text("default_model", default="gpt-4o"),  # string "gpt-4o"，无 FK
F.text("audio_model"),                       # 同上
```

**问题**：用户删了 api_key → `candidate_models` 级联删除 → `user-preferences.default_model` 成孤悬  
**重构**：迁移到 `available-models` 后，`default_model` 应改为 → `available-models.id` FK

---

### 3.4 `agent-skills`（P2 — 缺约束）

**现状**：
```python
F.text("skill_id", nullable=False, index=True),  # 无 REFERENCES skills(id)
```

**问题**：删除 `skills` 表记录时 `agent-skills` 行不级联清理，导致僵尸关联

**修复**（一行）：
```python
F.text("skill_id", nullable=False, index=True, ref="skills(id) ON DELETE CASCADE"),
```

---

### 3.5 `vm-users.password`（P0 — 安全漏洞）

**现状**：
```python
F.text("password", nullable=False, default=""),  # 明文！无 hidden=True
```

**问题**：`store.list("vm-users", ...)` 的 WS 推送会把密码明文发到前端  
**立即修复**：
```python
F.text("password", nullable=False, default="", hidden=True),
```

---

### 3.6 `devices`（P2 — 类型膨胀）

**现状**：linux/android/host_desktop 三种设备的专有字段挤在一张表里，`android_*` 字段对 linux 设备全是 null。

**重构方向（长期）**：
```
devices (base)
  id, user_id, type, name, status, memory, cpus, ports, pc_client_id

device-linux (form, 1:1 device, type='linux')
  backend, os_type, os_version, image_path, data_path, cloud_init_complete

device-android (form, 1:1 device, type='android')
  avd_name, device_serial, managed, system_image
```

---

### 3.7 `messages`（P2 — Queue 字段泄漏）

**现状**：`claimed_by`、`claimed_at`、`processed` 是消息队列控制字段，混入了消息实体。前端会看到这些字段但永远不需要它们。

**解法**：
- 这些字段加 `hidden=True`，不推送到前端
- 或长期拆为独立的 `message-queue` 实体（Gateway 内部，不注册到 Entangled）

---

### 3.8 `agent-notebook` vs `agent-task-history` vs `agent-tasks`（P2 — 语义重叠）

| 实体 | 实际用途 |
|------|------|
| `agent-notebook` | Agent 自己写的 memo/记忆条目 |
| `agent-task-history` | Agent 完成任务的历史记录（只读） |
| `agent-tasks` | 待办任务列表（可读写，带优先级） |

**结论**：三者语义不同，但 `agent-task-history` 和 `agent-tasks.status=completed` 有重叠。  
**建议**：`agent-task-history` 废弃，`agent-tasks` 加 `completed_at` 即可替代。

---

## 四、联动关系缺失清单

| 应建立的联动 | 现状 | 影响 |
|------|------|------|
| 删 api-key → 更新 user-preferences.default_model | ❌ 孤悬 | 用户选择的默认模型失效无感知 |
| 删 agent → 清理 agent-binding | ✅ ON DELETE CASCADE | 正确 |
| 删 skill → 清理 agent-skills | ❌ 无 FK | 僵尸关联 |
| 删 device → agent-binding | ✅ ON DELETE CASCADE | 正确 |
| 删 candidate_models → agents.model_id | ❌ 孤悬 string | Agent 跑时找不到模型 |

---

## 五、优先级排列

| 优先级 | 实体/问题 | 工作量 | 备注 |
|------|------|------|------|
| **P0 立即** | `vm-users.password` 加 `hidden=True` | 5 分钟 | 安全漏洞 |
| **P0 立即** | `messages` Queue 字段加 `hidden=True` | 5 分钟 | 前端不需要 |
| **P1 近期** | `agent-skills` 加 FK 约束 | 30 分钟 | 防僵尸关联 |
| **P1 近期** | Model 三实体拆分 | 2 天 | 见 model-entity-refactor.md |
| **P1 中期** | `agents.model_id` 迁移到 FK | 依赖 model 重构 | |
| **P1 中期** | `user-preferences` default_model 迁移 | 依赖 model 重构 | |
| **P2 长期** | `agent-tools` 五领域拆分 | 3 天 | 解耦大 |
| **P2 长期** | `devices` 类型表拆分 | 2 天 | 清爽但非阻塞 |
| **P2 长期** | `agent-task-history` 废弃 | 1 天 | agent-tasks 覆盖 |
| **P2 长期** | `subagents` 状态机独立 | 2 天 | 长期扩展性 |

---

## 六、可立即执行的 P0 修复（不破坏任何业务）

### 6.1 vm-users.password 隐藏
```python
# defs.py DEVICES → vm-users
F.text("password", nullable=False, default="", hidden=True),
```

### 6.2 messages Queue 字段隐藏
```python
# defs.py MESSAGES
F.text("claimed_by", hidden=True),
F.text("claimed_at", hidden=True),
F.int_("processed", default=0, hidden=True),
```

### 6.3 agent-skills FK 约束
```python
# defs.py AGENT_SKILLS
F.text("skill_id", nullable=False, index=True, ref="skills(id) ON DELETE CASCADE"),
```
