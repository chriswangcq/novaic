# Watchdog：唤醒风暴镇压与防抖调度

> 路径：`novaic-agent-runtime/task_queue/workers/watchdog_sync.py`

## 1. 跨界扫表的盲视野问题
Watchdog 是一个脱离了任何 AI 具体逻辑的守护线程，非常纯粹。它的眼里只会按照一定频率（`poll_interval`）去通过内网向 Gateway 发送捞取未分配请求，或者直接以 `_sync_with_gateway` 去拉：
“给我所有 `status == sending` 且时间属于未超时的 `chat_messages`”。

## 2. 唤醒风暴 (Awakening Storm)
**痛点**：如果你部署了 5 个 Worker 节点，在一瞬间大家同时通过轮询查到了那条 `sending` 状态消息！就会齐刷刷向队列投递出 5 个 Saga 处理进程；导致大模型会对你说 5 遍同样的话语！这被定性为灾难级的唤醒风暴。

**防重机制 (Dedup Filter)**：
既然不能要求 Gateway 给你强加排它锁（这会降低网关的吞吐量），Runtime 把去重的压力扔在了投递口 `queue-service` 上。
- Watchdog 投递 Saga 时，会使用高度特异化的 `payload` (包含消息的唯一实体属性 ID，例如 `msg_123`)。
- 在 `queue_service` 端有着 `Idempotency Key (幂等键)` 机制！如果存在相同的实体，这封 Saga 被退回抛弃。只有拔得头筹并发网络跑得第一快的 Watchdog 的单子会被盖戳建档。

## 3. 按 `(agent, subagent)` 排队的单行道锁
就算成功建单投进去了。如果用户对着他一直狂点键盘发送了 5 条消息呢？难道我们要同时开启 5 个并发大脑去想他到底问了啥？一定会出现思维时差错乱！
这依托于 Saga 上的限制条件：
`watchdog_sync.py` 在产生唤醒 Saga 时一定会带有队列标签 `agent_{id}_sub_{sub_id}`。
Saga 引擎保证在同一个挂载的 Queue 下面，必须有且只有唯一一个 `MessageProcess` 在往前推进（单道阻塞模型）。后续的发送请求必须作为排在屁股后面的兄弟，等第一条回答结束进入 `Sent` 或者失败 `Timeout` 后才能顶上接管思维域。
