# Services 架构详解 (v17)

## 设计原则

1. **无状态** - 服务无内存状态，随时可重启
2. **原子操作** - 使用 SQL `UPDATE...RETURNING` 原子 claim 任务
3. **幂等性** - Launcher/Collector 可安全重试
4. **超时回收** - Health Service 自动回收卡住的任务
5. **单一职责** - 每个服务只做一件事
6. **Gateway 通信** - 所有 DB 操作通过 Gateway API

## 服务列表

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              SQLite                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │  messages  │  │  subagents │  │  runtimes  │  │  pipeline_tasks    │ │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────────┬──────────┘ │
└────────┼──────────────┼──────────────┼────────────────────┼─────────────┘
         │              │              │                    │
         │              │              │    ┌───────────────┼───────────────┐
         ▼              ▼              ▼    │               │               │
┌────────────┐  ┌────────────┐  ┌───────────┴──┐ ┌─────────┴──┐ ┌─────────┴──┐
│  Launcher  │  │  Collector │  │    Async     │ │    Async   │ │    Async   │
│  Worker    │  │   Worker   │  │   (think)    │ │ (tool_call)│ │ (summarize)│
└────────────┘  └────────────┘  └──────────────┘ └────────────┘ └────────────┘
```

| 服务 | 入口 | 职责 | 可扩展 |
|------|------|------|--------|
| **Launcher** | `launcher_main.py` | 处理所有 launcher 任务 | 单实例* |
| **Collector** | `collector_main.py` | 处理所有 collector 任务 | 单实例 |
| **Async** | `async_main.py` | 处理 think/tool_call/summarize | **多实例** |
| **Health** | `health_main.py` | 健康检查、超时回收 | 单实例 |

*注：Launcher 理论上可多实例，但因幂等性保证，单实例足够。

## TaskWorker 基类

```python
class TaskWorker(ABC):
    """无状态任务处理器"""
    
    name = "worker"
    poll_interval = 0.1        # 轮询间隔 (秒)
    heartbeat_interval = 10.0  # 心跳间隔 (秒)
    claim_timeout_seconds = 60 # 任务超时 (秒)
    
    # 子类必须实现
    @abstractmethod
    def get_task_types(self) -> List[str]:
        """返回处理的 task_type 列表，如 ['launcher']"""
        pass
    
    @abstractmethod
    def get_task_subtypes(self) -> Optional[List[str]]:
        """返回处理的 task_subtype 列表，None 表示全部"""
        pass
    
    @abstractmethod
    async def process(self, task: dict) -> Any:
        """处理任务，返回结果"""
        pass
    
    # 可选覆盖
    async def on_success(self, task: dict, result: Any):
        """成功回调，默认标记 done"""
        pass
    
    async def on_failure(self, task: dict, error: Exception):
        """失败回调，默认标记 failed"""
        pass
```

### 主循环

```python
async def run(self):
    while not shutdown:
        task = await self.claim()  # 原子 claim
        if task:
            self._current_task = task
            result = await self.process(task)
            await self.on_success(task, result)
            self._current_task = None
        else:
            await asyncio.sleep(self.poll_interval)
```

## Launcher 详解

### LauncherWorker

```python
class LauncherWorker(TaskWorker):
    name = "launcher-worker"
    
    # Handler 注册表
    _handlers = {}
    
    @classmethod
    def register(cls, subtype: str):
        def decorator(handler_class):
            cls._handlers[subtype] = handler_class
            return handler_class
        return decorator
    
    async def process(self, task):
        handler = self._handlers[task["task_subtype"]]()
        
        # 1. 执行准备逻辑
        result = await handler.prepare_and_launch(...)
        
        # 2. 创建 collector 任务
        collector_id = await self.create_task(
            task_type="collector",
            task_subtype=f"{subtype}_collector",
            expected_tasks=len(result["async_task_ids"]),
            ...
        )
        
        return result
```

### 注册 Launcher Handler

```python
# services/launchers/think.py

@LauncherWorker.register("think_launcher")
class ThinkLauncher(BaseLauncher):
    async def prepare_and_launch(self, task, runtime_id, stage_id, agent_id, args):
        # 1. 准备 LLM 上下文
        context = await self._prepare_context(...)
        
        # 2. 创建 think async 任务
        task_id = await self.create_async_task(
            task_subtype="think",
            args={"context": context, ...},
            idempotency_key=f"{runtime_id}-{stage_id}-think",
        )
        
        return {
            "async_task_ids": [task_id] if task_id else [],
            "collector_args": {"context_length": len(context)},
            "next_stage_type": None,  # Collector 决定
        }
```

### 所有 Launcher 类型

| Subtype | 职责 | 创建的 Async |
|---------|------|-------------|
| `monitor_launcher` | 检测消息，唤醒 SubAgent | 无 (直接触发 runtime) |
| `runtime_launcher` | 创建 Runtime + MCP | 无 (直接触发 think) |
| `think_launcher` | 准备 LLM 上下文 | `think` |
| `actions_launcher` | 准备工具调用 | `tool_call` × N |
| `summarize_launcher` | 准备总结 | `summarize` |

## Collector 详解

### CollectorWorker

```python
class CollectorWorker(TaskWorker):
    name = "collector-worker"
    
    async def claim(self):
        # 只 claim "就绪" 的 collector (all async done)
        return await self.client.claim_task(
            task_types=["collector"],
            collector_ready_only=True,  # completed_tasks >= expected_tasks
        )
    
    async def process(self, task):
        handler = self._handlers[task["task_subtype"]]()
        
        # 1. 收集 async 结果
        # 2. 执行后处理
        result = await handler.collect_and_trigger(...)
        
        # 3. 触发下一个 launcher
        if result.get("next_stage_type"):
            await self.create_task(
                task_type="launcher",
                task_subtype=result["next_stage_type"],
                ...
            )
        
        return result
```

### Collector 就绪条件

```sql
-- Collector 只有在 completed_tasks >= expected_tasks 时才能被 claim
UPDATE pipeline_tasks
SET status = 'executing', claimed_by = ?
WHERE id = (
    SELECT id FROM pipeline_tasks
    WHERE task_type = 'collector'
      AND status = 'pending'
      AND completed_tasks >= expected_tasks
    LIMIT 1
)
RETURNING *
```

### 所有 Collector 类型

| Subtype | 输入 | 输出 (next_stage) |
|---------|------|-------------------|
| `monitor_collector` | SubAgent 唤醒 | `runtime_launcher` |
| `runtime_collector` | Runtime + MCP 创建 | `think_launcher` |
| `think_collector` | LLM 响应 | `actions_launcher` 或 `summarize_launcher` |
| `actions_collector` | 工具结果 | `think_launcher` 或 `summarize_launcher` |
| `summarize_collector` | Summary | 无 (SubAgent → sleeping) |

## Async 详解

### AsyncWorker

```python
class AsyncWorker(TaskWorker):
    name = "async-worker"
    
    async def on_success(self, task, result):
        # 1. 标记任务完成
        await self.client.mark_task_done(task["id"], result)
        
        # 2. 增加 collector 计数
        await self.increment_collector_count(task["stage_id"])
```

### 所有 Async 类型

| Subtype | 职责 | 执行内容 |
|---------|------|---------|
| `think` | LLM 调用 | 调用 LLM API，返回 actions |
| `tool_call` | MCP 工具 | 调用 MCP 工具，返回结果 |
| `summarize` | 生成总结 | 调用 LLM 生成 summary |

## Health Service

```python
class HealthMonitor:
    """定期回收超时任务"""
    
    async def recover_stale_tasks(self):
        # 回收超时的 executing 任务
        await self.client.recover_stale_tasks(
            timeout_seconds=60,
        )
    
    async def cleanup_orphan_runtimes(self):
        # 清理无 task 的 Runtime
        pass
```

## 数据流示例

用户发送 "Hello"：

```
1. [Gateway] POST /api/chat/send → 创建 message (read=0)

2. [Launcher] claim monitor_launcher (bootstrap)
   → MonitorLauncher.prepare_and_launch()
   → 检测到 unread message
   → 唤醒 SubAgent (status → awake)
   → 创建 monitor_collector

3. [Collector] claim monitor_collector
   → MonitorCollector.collect_and_trigger()
   → 创建 runtime_launcher

4. [Launcher] claim runtime_launcher
   → RuntimeLauncher.prepare_and_launch()
   → 创建 Runtime
   → 创建 MCP servers
   → 创建 runtime_collector

5. [Collector] claim runtime_collector
   → RuntimeCollector.collect_and_trigger()
   → 创建 think_launcher

6. [Launcher] claim think_launcher
   → ThinkLauncher.prepare_and_launch()
   → 准备 context (messages + tool schemas)
   → 创建 think async task
   → 创建 think_collector (expected_tasks=1)

7. [Async] claim think async task
   → ThinkExecutor.execute()
   → 调用 LLM API
   → 返回 {"actions": [{"type": "done", "message": "Hello!"}]}
   → increment_collector_count(stage_id)

8. [Collector] claim think_collector (completed_tasks >= expected_tasks)
   → ThinkCollector.collect_and_trigger()
   → 解析 LLM 响应
   → 发现 type="done"，创建 summarize_launcher

9. [Launcher] claim summarize_launcher
   → SummarizeLauncher.prepare_and_launch()
   → 创建 summarize async task
   → 创建 summarize_collector

10. [Async] claim summarize async task
    → SummarizeExecutor.execute()
    → 生成 summary
    → increment_collector_count()

11. [Collector] claim summarize_collector
    → SummarizeCollector.collect_and_trigger()
    → 保存 summary
    → 设置 SubAgent → sleeping
    → 完成 Runtime
    → 无 next_stage (结束)
```

## 幂等性保证

### Launcher 幂等

```python
# 使用 idempotency_key 防止重复创建
task_id = await self.create_async_task(
    task_subtype="think",
    idempotency_key=f"{runtime_id}-{stage_id}-think",
)
# 如果已存在，返回 None，不重复创建
```

### Collector 幂等

```python
# Collector 只在就绪时才能 claim
# 重复 claim 会返回同一个任务
# process 应该检查是否已处理过 (如检查 runtime.phase)
```

### Async 幂等

```python
# Async 本身不幂等 (LLM/工具可能有副作用)
# 但 increment_collector_count 是原子的
# 超时重试会产生新结果，但不会漏结果
```

## 启动方式

### 开发模式

```bash
# 单独启动各服务
cd novaic-gateway
source venv/bin/activate

# 必须先启动
export NOVAIC_DATA_DIR=~/.novaic
python main.py &                    # Gateway
python mcp_main.py &                # MCP Gateway

# Services (可选启动)
python launcher_main.py --bootstrap &  # Launcher + 初始化
python collector_main.py &             # Collector
python async_main.py &                 # Async
python health_main.py &                # Health
```

### 生产模式

```bash
# Tauri 自动启动所有进程
# 使用 novaic-backend 统一入口
novaic-backend gateway
novaic-backend mcp-gateway
novaic-backend launcher --bootstrap
novaic-backend collector
novaic-backend async
novaic-backend health
```

### 扩展 Async Worker

```bash
# Async Worker 可多实例（LLM 调用慢）
python async_main.py &  # Instance 1
python async_main.py &  # Instance 2
python async_main.py &  # Instance 3
```

## 故障恢复

### 场景 1: Service 崩溃

```
1. Service 崩溃，任务卡在 executing
2. Health Service 检测 heartbeat_at 超时 (60s)
3. 重置任务 status → pending
4. 其他 Worker 重新 claim
```

### 场景 2: Collector 等待超时

```
1. Collector expected_tasks=3, completed_tasks=2
2. 一个 Async 卡住
3. Health Service 检测并回收
4. Async 重新执行
5. completed_tasks → 3
6. Collector 变为就绪
```

### 场景 3: MCP Server 挂掉

```
1. MCP Gateway 重启或 MCP 挂掉
2. Runtime.mcp_url 请求失败
3. RuntimeLauncher 检测 mcp_url 无效
4. 重新创建 MCP servers
5. 更新 Runtime.mcp_url
```

## 监控指标

```python
# TaskWorker.metrics
{
    "claimed": 100,           # 总 claim 数
    "processed": 98,          # 成功处理数
    "failed": 2,              # 失败数
    "avg_process_time_ms": 150.5,  # 平均处理时间
    "last_claim_at": "...",   # 最后 claim 时间
    "last_process_at": "...", # 最后处理时间
}
```

### 健康检查端点

```bash
# Gateway 健康
GET /api/health

# Pipeline 任务状态
GET /internal/pipeline-tasks/stats

# 返回
{
    "pending": 5,
    "executing": 2,
    "done": 100,
    "failed": 1,
    "by_type": {
        "launcher": 10,
        "collector": 10,
        "async": 88
    }
}
```
