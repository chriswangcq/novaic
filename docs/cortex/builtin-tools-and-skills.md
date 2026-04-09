# 内置工具 Schema 与技能安装

> 源码：`novaic_cortex/tool_schemas.py`（**`BUILTIN_TOOL_SCHEMAS`**）、`runtime.py`（**`load_tool_schemas`**、**`install_skill`**、**`_seed_builtin_tools`**、**`_rebuild_skill_index`**）。

## 1. 内置 Schema：`BUILTIN_TOOL_SCHEMAS`

- 静态列表：**`skill_begin` / `skill_end`** 等（见 `tool_schemas.py` 全文）。
- 用途：作为 **LLM 可调工具** 的定义来源之一；与 Agent Runtime、saga 侧约定一致（模块头注释）。

## 2. `initialize()` 种子：`_seed_builtin_tools`

首次 **`Cortex.initialize()`** 时，若对象存储中尚不存在，则写入：

- **`/ro/config/tools/{name}.json`** — 每个 builtin 一条；
- **`/ro/config/tools/_index.json`** — 内置工具名列表。

存储键仍为 **`agents/{agent_id}/ro/config/tools/...`**（见 [storage-and-keys.md](storage-and-keys.md)）。

## 3. `load_tool_schemas()` 合并顺序

1. 扫描 **`/ro/config/tools/*.json`**（排除 `_` 前缀），按目录顺序加载，**同名只保留第一次**（`seen_names`）。
2. 扫描 **`/ro/skills/{skill}/tools/*.json`**，同样按名去重追加。

**先 config 目录，后各 skill**，后者同名不会覆盖前者（已实现为先见者胜）。

## 4. `install_skill(name, skill_md, meta)`

- 校验技能名路径深度 ≤ **`EngineConfig.max_skill_depth`**。
- 写入：
  - **`agents/{agent_id}/ro/skills/{name}/SKILL.md`**
  - **`.../meta.json`**
- **`_rebuild_skill_index()`**：遍历 `.../ro/skills/` 下对象，生成 **`.../ro/skills/_index.md`**（Markdown 列表，含各 `meta.json` 的 `description`）。
- 触发 **`hooks.on_skill_loaded`**（见 extension-points）。
- 更新 **`metrics.skills_installed`**。

返回逻辑路径：**`/ro/skills/{name}/`**。

---

## 相关

- [runtime-facade.md](runtime-facade.md)  
- [engine-config-and-metrics.md](engine-config-and-metrics.md) — `max_skill_depth`  
- [http-api.md](http-api.md) — `GET /v1/tools`、`/v1/skill/list`  
