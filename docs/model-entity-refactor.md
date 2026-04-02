# Model 实体规范化重构方案

> 状态：待实施 / 当前 `candidate_models` 扁平实现维持可用

---

## 一、现状问题

当前 `candidate_models` 表（EntityDef name=`"models"`）三职合一：

| 职责 | 字段 | 问题 |
|------|------|------|
| 模型元数据 | `model_id`, `name`, `provider` | 同一个 gpt-4o 绑两个 key 就存两行，数据重复 |
| API Key 关联 | `api_key_id` | 扁平外键无法表达 N:M 关系 |
| 用户启用状态 | `available=0/1` | 启用状态混在模型记录里，难以独立管理 |

`refresh_models` action 每次需要全量 diff + 批量 upsert + 手动 `notify_entity_change`，逻辑复杂。

---

## 二、目标架构（三实体分离）

```
models (Form Entity / 全局模型注册表)
  model_id  PK    "gpt-4o", "claude-3-5-sonnet" …
  name            展示名
  provider        openai / anthropic / google / azure / openai_compatible
  context_window  可选，上下文长度
  is_custom       0/1
  created_at

api-key-models (List Entity, child of api-keys)
  id              PK UUID
  api_key_id      FK → api_keys.id  ON DELETE CASCADE
  model_id        → models.model_id
  UNIQUE(api_key_id, model_id)
  created_at

available-models (List Entity, user-scoped)
  id              PK UUID
  user_id         FK
  model_id        → models.model_id
  api_key_id      使用哪个 key 调用该 model
  UNIQUE(user_id, model_id)
  created_at
```

### 实体关系图

```
api-keys ──1:N──> api-key-models <──N:1──> models (全局)
                                                ↑
users ──1:N──> available-models ────────────────┘
```

---

## 三、各实体说明

### `models`（Form-like，but list）
- 全局模型注册表，不区分用户
- `is_custom=1` 表示用户手动添加的模型
- `refresh_models` 只往这里 upsert 元数据，无需关心谁启用了它

### `api-key-models`
- 表达"这个 api_key 支持哪些 model"
- 删 api_key 时级联删除所有关联记录
- `refresh_models` 的核心写入目标

### `available-models`
- 用户显式启用的模型，带 `api_key_id` 表明走哪个 key 调用
- 替换现在的 `available=0/1` 字段
- 前端 `useAppStore.availableModels` 读这里

---

## 四、变更影响

### Backend (`novaic-gateway`)

| 文件 | 变更 |
|------|------|
| `gateway/entity/defs.py` | 新增 `MODELS`、`API_KEY_MODELS`、`AVAILABLE_MODELS` EntityDef；删除 `CANDIDATE_MODELS` |
| `gateway/entity/defs.py` | `_refresh_models_action` 极简：只 upsert `models` + `api-key-models`，自动 notify，无需手动 batch notify |
| `gateway/entity/defs.py` | `_toggle_model_action` → 操作 `available-models`（insert/delete），不再更新 `available` 字段 |
| `gateway/entity/defs.py` | `_add_custom_model_action` → 写 `models`（is_custom=1）+ `api-key-models` |
| `gateway/entity/defs.py` | `_remove_model_action` → 删 `api-key-models` 行，若 `is_custom` 也删 `models` 行 |
| DB migration | `candidate_models` 数据拆分迁移到三张新表 |

### Frontend (`novaic-app`)

| 文件 | 变更 |
|------|------|
| `src/data/entities/__generated__.ts` | 重新 codegen，新增三个实体类型 |
| `src/data/index.ts` | 新增 `apiKeyModelsStore`、`availableModelsStore` |
| `src/components/Settings/SettingsModal.tsx` | `modelsStore.useList()` → `apiKeyModelsStore.useList()` 按 api_key_id 过滤；available 单独读 `availableModelsStore` |
| `src/components/Settings/ModelsTab.tsx` | `ModelSection` 数据源变更；toggle 语义从"更新 available 字段"变为"插入/删除 available-models 行" |
| `src/application/modelConfigService.ts` | `toggleModel` → `availableModelsStore.create/delete`；`addCustomModel` → 分别写两个实体 |
| `src/application/store.ts` (`useAppStore`) | `availableModels` 读 `availableModelsStore` |

---

## 五、预期收益

| 问题 | 现在 | 重构后 |
|------|------|------|
| gpt-4o 绑两个 key | 存两行，名字可能不一致 | `models` 一行，`api-key-models` 两行 |
| 刷新模型 | 全量 diff + 手动 batch notify | upsert api-key-models，Entangled 自动通知 |
| 用户启用状态 | `available` 字段混在模型记录 | 独立 `available-models` 实体，可扩展 |
| 未来扩展 | 需改 candidate_models schema | 直接加字段到对应实体 |

---

## 六、工作量估算

| 阶段 | 内容 | 估时 |
|------|------|------|
| 1 | Gateway defs.py 新实体 + actions 改写 | 0.5d |
| 2 | DB migration 脚本 + 数据迁移 | 0.5d |
| 3 | 前端 codegen + store + UI | 0.5d |
| 4 | 联调 + 测试 | 0.5d |
| **合计** | | **约 2d** |

---

## 七、启动条件

- [ ] agent-binding 持久化稳定（已完成 2026-03-31）
- [ ] model refresh / test API key 功能正常（进行中）
- [ ] 无进行中的其他实体 schema 变更
