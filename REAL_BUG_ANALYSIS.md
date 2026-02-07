# 真正的 Bug 分析报告

## 🐛 实际问题

### Bug 1: Internal API 路由前缀重复 ✅ 已修复

**症状：**
```
404: POST /internal/messages/claim-and-prepare
```

**原因：** 
- 重构时忘记删除旧的 `internal.py` 文件
- 子模块错误设置了双重 `prefix="/internal"`

**修复：** 
- 删除旧文件
- 修复 11 个子模块路由

**验证：** Gateway 日志现在显示 200 OK ✅

---

### Bug 2: 启动时序问题导致 Runtime 创建失败 ⚠️

**症状：**
```
404: POST /internal/runtimes/rt-xxx/tools/call
```

**真正原因：**
```sql
-- 查询 mcp.create 任务结果
task-5e040bb4fbc7 | {"runtime_id": "rt-5464aa7117cc", ...}
result: {"success": false, "error": "[Errno 61] Connection refused"}
created_at: 2026-02-07T10:48:46
```

**根本问题：启动时序竞争**

1. **启动顺序：**
   ```
   NovAIC App 启动
     ↓ 并行启动所有服务
     ↓
   Gateway ✅ 快速启动
   Queue Service ✅ 快速启动  
   Watchdog ✅ 快速启动
   Tools Server ⚠️ 启动较慢
     ↓
   用户发消息（系统刚启动）
     ↓
   创建 RuntimeStart Saga
     ↓
   执行 mcp.create 任务
     ↓ 尝试连接 Tools Server
   ❌ Connection refused (Tools Server 还没准备好)
   ```

2. **Task 标记为 done，即使失败**
   - 任务返回了 `{"success": false}` 
   - 但 Task Queue 认为任务"完成"了
   - **没有重试机制**

3. **结果：**
   - Gateway 中有 runtime 记录
   - Tools Server 中没有 runtime
   - 后续工具调用全部 404

---

## ✅ 临时修复

手动在 Tools Server 中创建缺失的 runtime：

```bash
curl -X POST http://127.0.0.1:19998/internal/runtimes \
  -H "Content-Type: application/json" \
  -d '{
    "runtime_id":"rt-5464aa7117cc",
    "agent_id":"e270ec13-bfd4-4b5b-abd9-b51b6fa85ec6",
    "subagent_id":"main-34ca3e51",
    "ports":{}
  }'
```

**结果：** ✅ Runtime 成功创建，系统恢复正常

---

## 🔧 长期解决方案

### 方案 1: 改善启动顺序 ⭐ 推荐

在 Tauri 中确保服务启动顺序：

```rust
// 1. 先启动 Gateway
start_gateway().await?;

// 2. 再启动 Tools Server  
start_tools_server().await?;

// 3. 等待 Tools Server 就绪
wait_for_service("http://127.0.0.1:19998/api/health", 30).await?;

// 4. 最后启动其他服务
start_queue_service().await?;
start_workers().await?;
```

### 方案 2: 添加重试机制

在 `task_queue/business/mcp.py` 中：

```python
def create(self, runtime_id: str, agent_id: str) -> MCPCreateResult:
    # 添加重试逻辑
    max_retries = 3
    retry_delay = 2.0
    
    for attempt in range(1, max_retries + 1):
        try:
            resp = self.client.create_aggregate_mcp(...)
            # 成功
            return MCPCreateResult(success=True, ...)
        except httpx.ConnectError as e:
            if attempt < max_retries:
                logger.warning(
                    f"[MCPBusiness] Tools Server not ready "
                    f"(attempt {attempt}/{max_retries}), "
                    f"retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
            else:
                # 最后一次也失败
                return MCPCreateResult(
                    success=False,
                    error=f"Connection failed after {max_retries} attempts: {e}"
                )
```

### 方案 3: Tools Server 启动时恢复

**已有机制，但需要改进：**

`tools_server/runtime_manager.py` 的 `restore_from_gateway()`:
- ✅ 启动时从 Gateway 拉取 runtime
- ❌ 但只拉取有 `tool_ports` 的 runtime
- ❌ 新创建的 runtime `tool_ports = NULL`，拉不到

**改进：**
```python
# gateway/api/internal/runtime.py
@router.get("/runtimes/with-tools")
def get_runtimes_with_tools():
    # 修改为：返回所有活跃 runtime，不管是否有 tool_ports
    runtimes = runtime_repo.get_all_active_runtimes()
    return {"runtimes": [format_runtime(r) for r in runtimes]}
```

---

## 📊 问题时间线

```
2026-02-07 10:48:46 - 用户启动应用
2026-02-07 10:48:46 - RuntimeStart Saga 创建
2026-02-07 10:48:46 - mcp.create 任务执行
2026-02-07 10:48:46 - ❌ Connection refused (Tools Server 未就绪)
2026-02-07 10:48:46 - 任务标记为 done (但 success=false)
...（数小时后）
2026-02-07 18:55:00 - 你重启应用（修复了路由问题）
2026-02-07 18:55:00 - 但 Tools Server 中仍然缺少 runtime
2026-02-07 18:57:18 - 手动创建 runtime ✅
2026-02-07 18:57:18 - 问题解决
```

---

## 💡 关键教训

1. **微服务启动顺序很重要**
   - 依赖的服务必须先启动
   - 需要健康检查和等待机制

2. **失败处理要完整**
   - 连接失败应该重试
   - Task 失败不应该标记为 done

3. **恢复机制要完善**
   - Tools Server 的 restore 逻辑太严格
   - 应该恢复所有活跃 runtime

4. **集成测试很重要**
   - 需要测试冷启动场景
   - 需要测试服务启动时序问题

---

## 🎯 总结

**实际 Bug：**
1. ✅ 路由前缀重复（代码问题）- 已修复
2. ⚠️ 启动时序竞争（架构问题）- 临时修复，需长期方案

**不是 Bug：**
- ❌ `MCPBusiness.create()` 逻辑是正确的
- ❌ 不需要在 `create()` 中手动调用 Tools Server
- ❌ `create_aggregate_mcp()` 已经包含了 Tools Server 调用

**真正的问题：** 
服务启动时 Tools Server 还没准备好，导致首次创建失败。

**解决方案：**
- 短期：手动修复（已完成）
- 长期：改善启动顺序 + 添加重试机制
