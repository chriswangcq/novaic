# Agent Loop 性能瓶颈分析报告

## 📊 测试场景回顾

- **消息数量**: 1117 条用户消息
- **发送速率**: 18.54 msg/s (每条间隔 ~50ms)
- **持续时间**: 60 秒
- **Agent Loop Rounds**: 3 轮
- **总处理时间**: 141 秒 (从第一轮开始到最后轮结束)

## 🔍 核心问题：Saga Worker 调度延迟

### 问题现象

| Round | Saga 类型 | 创建→认领等待 | 实际执行 | 总耗时 | 占比 |
|-------|----------|--------------|---------|--------|------|
| #1 | react_think | 1.83s | 5.72s | 7.55s | 等待 24% |
| #1 | react_actions | **13.1s** | 0.96s | 14.06s | **等待 93%** |
| #2 | react_think | **25.98s** | 13.71s | 39.69s | **等待 65%** |
| #2 | react_actions | **68.35s** | 0.73s | 69.08s | **等待 99%** |
| #3 | react_think | 0.09s | 10.78s | 10.87s | 等待 1% |
| #3 | react_actions | 0.0s | 0.84s | 0.84s | 等待 0% |

### 时间分布分析

**Agent Loop 总耗时**: 58.11 秒
- LLM 调用: 25.40 秒 (43.7%)
- **调度等待**: 32.71 秒 (56.3%) ← **主要瓶颈**

## 🎯 根本原因

### 1. 大量 message_process Saga 堵塞队列

测试期间创建的 Saga:
```
message_process:   1094 个  ← 占据了 Saga Worker 的处理能力
react_think:       3 个
react_actions:     3 个
runtime_start:     1 个
runtime_complete:  1 个
summarize:         1 个
```

**message_process Saga 统计**:
- 平均等待认领时间: **39.84 秒**
- 平均执行时间: 0.44 秒
- 状态: 1088 completed, 4 failed, 2 running

### 2. Saga Worker 配置不足

**当前配置**:
- Saga Worker 数量: **1 个** (只有 `saga-2d5f9e12`)
- 最大并发数: 10 个 saga
- 轮询间隔: 0.1 秒

**计算**:
- 1094 个 saga / 10 并发 = 至少 110 轮处理
- 每轮平均 0.44 秒 = 至少 48 秒
- 加上轮询和调度开销 ≈ 60-70 秒

这就解释了为什么 react_actions #2 要等 68 秒才被认领！

## 📈 详细时间线

### Round #1 (良好)
```
04:25:05  react_think 创建
04:25:07  react_think 认领 (等待 1.83s)
04:25:13  react_think 完成 (执行 5.72s)
          - context.read: 70 条消息
          - llm.call: 4.92s
          
04:25:13  react_actions 创建
04:25:26  react_actions 认领 (等待 13.1s) ← 队列中有大量 message_process
04:25:27  react_actions 完成 (执行 0.96s)
          - 执行 session_state 工具
          - 触发下一轮 react_think
```

### Round #2 (糟糕)
```
04:25:27  react_think 创建
04:25:53  react_think 认领 (等待 25.98s) ← 队列继续堵塞
04:26:06  react_think 完成 (执行 13.71s)
          - context.read: 849 条消息
          - llm.call: 10.85s
          
04:26:06  react_actions 创建
04:27:15  react_actions 认领 (等待 68.35s) ← 严重堵塞！
04:27:15  react_actions 完成 (执行 0.73s)
          - 执行 chat_history 工具
          - 触发下一轮 react_think
```

### Round #3 (恢复正常)
```
04:27:15  react_think 创建
04:27:15  react_think 认领 (等待 0.09s) ← message_process 队列清空
04:27:26  react_think 完成 (执行 10.78s)
          - context.read: 198 条消息
          - llm.call: 9.63s
          
04:27:26  react_actions 创建
04:27:26  react_actions 认领 (等待 0.0s) ← 队列空闲
04:27:27  react_actions 完成 (执行 0.84s)
          - 发送最终回复
          - Runtime 休眠
```

## 🔧 优化方案

### 方案 1: 优化 message_process Saga (推荐)

**问题**: 每条消息都创建一个 message_process saga 太重了

**优化方向**:
1. **批量处理**: Watchdog 批量认领消息，只创建 1 个 saga
2. **优先级队列**: react_think/react_actions 优先级高于 message_process
3. **快速路径**: message_process 检测到 SubAgent awake 时直接返回，不走完整流程

**预期效果**:
- message_process saga 数量: 1094 → ~10
- 队列堵塞: 消除
- 调度延迟: 39.84s → <1s

### 方案 2: 增加 Saga Worker 实例

**当前**: 1 个 Saga Worker，max_concurrent=10
**优化**: 3-5 个 Saga Worker，max_concurrent=20

**预期效果**:
- 并发处理能力: 10 → 60-100
- 队列处理速度: 提升 6-10 倍
- 调度延迟: 39.84s → ~5s

### 方案 3: 优化 Saga 认领策略

**当前**: 先到先服务 (FIFO)
**优化**: 优先级队列

```python
# 优先级定义
SAGA_PRIORITY = {
    "react_think": 100,      # 最高优先级
    "react_actions": 90,
    "runtime_start": 80,
    "message_process": 10,   # 最低优先级
}
```

**预期效果**:
- react_think/react_actions 立即被认领
- 不会被 message_process 堵塞

### 方案 4: message_process 异步化 (最佳)

**核心思路**: message_process 不应该是 Saga

**重新设计**:
```python
# 当前架构 (问题)
用户消息 → message_process Saga → 检查 SubAgent 状态 → 可能创建 runtime_start

# 优化架构
用户消息 → 直接写入队列 (status=sending)
Watchdog → 批量检查 → 只对需要唤醒的创建 Saga
```

**优点**:
1. 不创建无用的 Saga
2. 消息路由变成快速的数据库操作
3. 只有真正需要处理的消息才进入 Saga 流程

## 📊 性能对比预测

| 指标 | 当前 | 方案1 | 方案2 | 方案4 |
|------|------|-------|-------|-------|
| message_process Saga 数 | 1094 | ~10 | 1094 | 0 |
| 平均调度延迟 | 39.84s | <1s | ~5s | <0.1s |
| Agent Loop 总耗时 | 141s | ~60s | ~80s | ~50s |
| 系统响应延迟 | 高 | 低 | 中 | 极低 |

## 🎯 建议

### 短期 (立即可做)
1. ✅ **增加 Saga Worker 到 3 个实例** (方案2)
2. ✅ **提高 max_concurrent 到 20** (简单配置)

### 中期 (需要代码修改)
3. ✅ **实现优先级队列** (方案3)
4. ✅ **优化 message_process 逻辑** (方案1)

### 长期 (架构优化)
5. ✅ **重构消息路由** (方案4 - 最佳方案)

## 📝 总结

**当前性能瓶颈不在 LLM 或 Agent Loop 本身，而在 Saga Worker 的调度能力**。

关键数据:
- ✅ LLM 只占 43.7% 的时间 (合理)
- ❌ 调度等待占 56.3% 的时间 (不可接受)
- ❌ 1094 个 message_process saga 堵塞队列

**最优解**: 重新设计消息路由机制 (方案4)，消除不必要的 Saga 创建。

**快速解**: 增加 Saga Worker 实例 + 提高并发数 (方案2)，可立即缓解问题。
