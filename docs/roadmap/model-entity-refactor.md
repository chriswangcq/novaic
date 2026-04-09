# Model 实体规范化重构（方案）

> 对应原 `**HANDOVER.md` §十七**。**当前代码**仍以 `candidate_models` 扁平实现为主；以下为**目标设计**，落地前以 `novaic-gateway` 的 `defs.py` / DB 为准。

## 现状问题

`candidate_models`（EntityDef `name="models"`）多职合一：元数据、API Key 关联、用户启用状态混在同一扁平模型，导致 `refresh_models` 复杂、重复行多。

## 目标架构（三实体分离）

```
models（Form，全局注册表）
  model_id PK, name, provider, context_window, is_custom, …

api-key-models（List，挂 api-keys 下）
  id PK, api_key_id FK, model_id → models.model_id
  UNIQUE(api_key_id, model_id)

available-models（List，user-scoped）
  id PK, user_id FK, model_id → models.model_id, api_key_id
  UNIQUE(user_id, model_id)
```

## 变更影响（规划）


| 层                 | 内容                                                        |
| ----------------- | --------------------------------------------------------- |
| Gateway `defs.py` | 新实体定义；`refresh_models` 改为主要维护 `api-key-models`            |
| Gateway DB        | migration：从 `candidate_models` 拆表                         |
| 前端 codegen        | `__generated__.ts` 更新                                     |
| UI / stores       | `SettingsModal`、`modelConfigService`、`useAppStore` 等改读新实体 |


## 预期收益

- `refresh_models` 简化；删 key 时级联清晰；元数据去重；`available-models` 易扩展优先级等字段。

## 工作量（原估算）

约 1.5 天量级（defs + migration + UI + codegen + 测）— 实施前请重新评估。

> **启动条件（HANDOVER 原意）**：agent-binding 与 device 稳定后再动大迁移。

