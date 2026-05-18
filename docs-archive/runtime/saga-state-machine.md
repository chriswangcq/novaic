# Saga 分布式长程运转机构

> 路径：`novaic-agent-runtime/task_queue/sagas/` 与 `queue_service` 集成

## 1. 短 Task 与 长 Saga 的天堑
在我们的业务系统里，处理长链事件存在“进程必定会被杀死、网络必定有空泡”的前提。如果一切都寄托于在一个内存里的 `async/await`，只要 Kubernetes 将 pod 回收，AI 的长篇大论就被腰斩。

- **`Task`** (`pool=execution`)：就是一次短平快的动作。比如“去跟 LLM 调一张生图出来返回”、“去让网关调个设备状态”。它生来就应该在 30 秒内毁灭并交付。
- **`Saga`** (`pool=control`)：状态机本身。它拥有 `steps` 和 `status`。

## 2. 以 `MessageProcess Saga` 为例
看 `sagas/message_process.py` 是怎么步步为营的。这是一个标准的三段式编排：

**Step 1. 意图清洗与入海准备 (`PREPARE`)**
这步不产生什么长连接，它往 `queue-service` 下方塞进一个给 Cortex 的 `Topic`：`cortex.prepare_llm_context`。
Saga 让路退下，等待任务返回：这时候拿到了 Cortex 千辛万苦裁切过的记忆图谱流。进入下一节点。

**Step 2. 思维火花 (`THINK_LOOP`)**
此时触发跨越到 `react_think` 的代理环（这本身可能也是个无限状态机），要求生成工具流或者吐字。如果返回的结果是需要用剪刀斩断画面。Saga 挂起（`Suspend`），把 Tool Call 扔到任务池让别的 Worker 用 Chrome 截图后塞回结果队列重新唤醒本 Saga。

**Step 3. 落土为安 (`RESOLVE`)**
Saga 把自己持有一整条链路的结果打包作为 Finalise。如果是文本消息，便产生写入事务交给 Gateway 通知 UI 发向前端。

## 3. 防抖重试与补偿回滚
若中途失败。Saga 的好处是自身携带 `compensate_topic` 与异常计数（`Retries=3`）。即使由于网络导致 Cortex 完全不可用，Saga 会在一小时中自己重试 3 次，期间它的中间断点进度永远不会在内存中失忆。
