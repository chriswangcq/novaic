# Split Repos 优化方案

> 基于 `SPLIT_REPOS_CODE_DUPLICATION_ANALYSIS.md` 与 `DUPLICATION_DEAD_VS_LIVE_ANALYSIS.md` 制定。  
> 生成时间：2026-03-03

---

## 一、优化目标

1. **删除死代码**：移除未被挂载/调用的模块，降低维护成本
2. **去重共享**：将多份相同且均在用的代码抽到 shared，减少重复
3. **风险可控**：分阶段执行，每阶段可独立验证与回滚

---

## 二、阶段划分

| 阶段 | 名称 | 风险 | 依赖 | 预估工时 |
|------|------|------|------|----------|
| **Phase 1** | RO 死代码清理 | 低 | 无 | 0.5d |
| **Phase 2** | Gateway 死代码清理 | 低 | 无 | 0.5d |
| **Phase 3** | common/http/clients 抽到 shared | 中 | 无 | 1d |
| **Phase 4** | 消费方接入 shared clients | 中 | Phase 3 | 0.5d |

---

## 三、Phase 1：RO 死代码清理

### 3.1 目标

移除 novaic-runtime-orchestrator 中未被挂载路由使用的模块。

### 3.2 删除清单

| 路径 | 说明 | 前置检查 |
|------|------|----------|
| `common/http/clients.py` | 所有调用方均在死路径 | 确认 helpers 中 `resolve_agent_id_from_subagent` 无人调用 |
| `common/http/__init__.py` | 仅导出 clients | 与上同删 |
| `gateway/clients/vmcontrol.py` | 仅 vm/manager 使用，vm 未挂载 | - |
| `gateway/clients/vmuse_adapter.py` | 仅 example 使用 | - |
| `gateway/clients/runtime_orchestrator.py` | 仅 resolve_agent_id 使用，该函数未调用 | - |
| `gateway/clients/vmuse_adapter_example.py` | 示例脚本 | - |
| `skills/` | SkillRepository 未被任何挂载路由使用 | - |
| `gateway/db/repositories/skill.py` | 无挂载路由使用 | 保留 schema 中 skills/agent_skills 表定义，仅删 repository |
| `gateway/api/schemas.py` | 无路由引用 | 确认无 import |

### 3.3 需修改的文件（非删除）

| 文件 | 修改内容 |
|------|----------|
| `gateway/db/repositories/__init__.py` | 移除 `from .skill import SkillRepository` 及 `SkillRepository` 的 `__all__` 导出 |
| `gateway/api/internal/helpers.py` | 移除 `resolve_agent_id_from_subagent` 函数及其 `__all__` 导出（该函数在 RO 中从未被调用） |

### 3.4 保留项（勿删）

- `gateway/db/schema.py` 中 `skills`、`agent_skills` 表定义及 migration 逻辑（DB 可能已有数据）
- `gateway/config/devices.py`（agents_db 间接使用）

### 3.5 验证步骤

```bash
cd novaic-runtime-orchestrator
python -c "from main_runtime_orchestrator import app; print('OK')"
pytest tests/ -v -x  # 如有测试
```

---

## 四、Phase 2：Gateway 死代码清理

### 4.1 目标

移除 novaic-gateway 中未被挂载的 internal 路由及未使用的 clients。

### 4.2 删除清单

| 路径 | 说明 |
|------|------|
| `gateway/api/internal/web.py` | 未在 internal_proxy 中 include |
| `gateway/api/internal/llm.py` | 未在 internal_proxy 中 include |
| `gateway/api/internal/broadcast.py` | 未在 internal_proxy 中 include |
| `gateway/clients/vmuse_adapter.py` | 仅 tests/example 使用，无生产路由 |
| `gateway/clients/vmuse_adapter_example.py` | 示例脚本 |

### 4.3 需修改的文件

| 文件 | 修改内容 |
|------|----------|
| `gateway/api/internal/__init__.py` | 若聚合了 web/llm/broadcast router，移除对应 include；若从未使用则可能无需改 |

### 4.4 验证步骤

```bash
cd novaic-gateway
python -c "from main_gateway import app; print('OK')"
# 确认 /internal/* 下无 web、llm、broadcast 路由
pytest tests/ -v -x
```

---

## 五、Phase 3：common/http/clients 抽到 shared

### 5.1 目标

将 `common/http/clients.py` 核心逻辑抽到 `novaic-shared-runtime-common`，保留各 repo 的薄包装以注入 `ServiceConfig.INTERNAL_HTTP_TRUST_ENV`。

### 5.2 依赖分析

- `clients.py` 依赖 `common.config.ServiceConfig.INTERNAL_HTTP_TRUST_ENV`
- 各 repo 的 config 结构不同，shared 不应直接 import config
- 方案：shared 提供**显式参数**的工厂，各 repo 用薄包装传入 config 值

### 5.3 shared 新增内容

**路径**：`novaic-shared-runtime-common/shared_runtime_common/common/http/clients.py`

```python
"""
Unified HTTP client helpers. trust_env for internal calls is passed by caller.
"""
from __future__ import annotations
from typing import Any
import httpx

def create_internal_async_client(trust_env: bool, **kwargs: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(**{**kwargs, "trust_env": trust_env})

def create_internal_sync_client(trust_env: bool, **kwargs: Any) -> httpx.Client:
    return httpx.Client(**{**kwargs, "trust_env": trust_env})

def create_external_async_client(**kwargs: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(**{**kwargs, "trust_env": False})

def create_external_sync_client(**kwargs: Any) -> httpx.Client:
    return httpx.Client(**{**kwargs, "trust_env": False})
```

**路径**：`shared_runtime_common/common/http/__init__.py`（新建）

```python
from .clients import (
    create_internal_async_client,
    create_internal_sync_client,
    create_external_async_client,
    create_external_sync_client,
)
__all__ = [
    "create_internal_async_client",
    "create_internal_sync_client",
    "create_external_async_client",
    "create_external_sync_client",
]
```

### 5.4 各 repo 薄包装（替换原 42 行）

**agent-runtime / tools-server / gateway** 的 `common/http/clients.py` 改为：

```python
"""Thin wrapper: inject ServiceConfig.INTERNAL_HTTP_TRUST_ENV into shared clients."""
from __future__ import annotations
from typing import Any
from common.config import ServiceConfig
from shared_runtime_common.common.http.clients import (
    create_internal_async_client,
    create_internal_sync_client,
    create_external_async_client,
    create_external_sync_client,
)

def internal_async_client(**kwargs: Any):
    return create_internal_async_client(ServiceConfig.INTERNAL_HTTP_TRUST_ENV, **kwargs)

def internal_sync_client(**kwargs: Any):
    return create_internal_sync_client(ServiceConfig.INTERNAL_HTTP_TRUST_ENV, **kwargs)

def external_async_client(**kwargs: Any):
    return create_external_async_client(**kwargs)

def external_sync_client(**kwargs: Any):
    return create_external_sync_client(**kwargs)

internal_client = internal_sync_client
external_client = external_sync_client
```

### 5.5 RO 处理

- Phase 1 已删除 RO 的 `common/http/clients`，无需接入 shared

### 5.6 验证步骤

```bash
# 在 shared 中
cd novaic-shared-runtime-common && pytest tests/ -v

# 在各消费 repo
cd novaic-agent-runtime && python -c "
from common.http.clients import internal_client, internal_async_client
c = internal_client(); print('sync OK')
"
cd novaic-tools-server && python -c "from common.http.clients import internal_async_client; print('OK')"
cd novaic-gateway && python -c "from common.http.clients import internal_client; print('OK')"
```

---

## 六、Phase 4：消费方接入（可选细化）

若 Phase 3 中薄包装已一次性改好，则 Phase 4 仅需：

1. 发布新版本 `novaic-shared-runtime-common`
2. 更新 agent-runtime、tools-server、gateway 的 `pyproject.toml` 或 `requirements.txt` 依赖版本
3. 全量回归测试

---

## 七、执行顺序与回滚

| 顺序 | 阶段 | 可独立回滚 |
|------|------|------------|
| 1 | Phase 1（RO 清理） | ✅ git revert |
| 2 | Phase 2（Gateway 清理） | ✅ git revert |
| 3 | Phase 3（shared 新增 + 各 repo 薄包装） | ✅ 可先只改 shared，各 repo 暂不切 |
| 4 | Phase 4（依赖版本升级） | ✅ 回退依赖版本 |

**建议**：Phase 1 与 Phase 2 可并行；Phase 3 完成后再做 Phase 4。

---

## 八、不做/延后项

| 项目 | 原因 |
|------|------|
| 删除 RO 的 schema 中 skills 表 | 可能已有数据，且 migration 已执行 |
| 删除 Gateway 的 skills API | 在用，仅 builtin 目录为空 |
| common/ 薄包装改为直接 import shared | 中优先级，单独评估 |
| mcp_client 抽到 shared | 仅 tools-server 使用，无跨 repo 重复 |
| gateway/db 公共 migration 工具 | 架构分叉，低优先级 |

---

## 九、检查清单（执行前）

- [ ] 确认 RO 的 `main_runtime_orchestrator.py` 仅挂载 internal_router + /api/health
- [ ] 确认 Gateway 的 internal_proxy 未 include web/llm/broadcast
- [ ] 确认 agent-runtime、tools-server、gateway 的 common.http.clients 使用点均可达
- [ ] 备份或打 tag 便于回滚

---

## 十、参考文档

- `docs/SPLIT_REPOS_CODE_DUPLICATION_ANALYSIS.md` §十
- `docs/DUPLICATION_DEAD_VS_LIVE_ANALYSIS.md`
- `novaic-runtime-orchestrator/docs/DEAD_VS_LIVE_CODE_ANALYSIS.md`
